"""
Vector store implementation with OceanBase.
"""
import uuid
import json
import os
from typing import List, Dict, Any, Optional
import numpy as np
import pymysql
from sqlalchemy import create_engine, text
import requests
from app.config.settings import (
    OCEANBASE_HOST, 
    OCEANBASE_PORT, 
    OCEANBASE_USER, 
    OCEANBASE_PASSWORD, 
    OCEANBASE_DATABASE,
    DEEPSEEK_API_KEY,
    DEEPSEEK_EMBEDDING_MODEL,
    VECTOR_DIMENSION
)


class BaseVectorStore:
    """Base vector store implementation."""
    
    def __init__(self):
        """Initialize the base vector store."""
        self.api_key = DEEPSEEK_API_KEY
        self.embedding_model = DEEPSEEK_EMBEDDING_MODEL
    
    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for a list of texts using DeepSeek API."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.embedding_model,
                "input": texts
            }
            
            response = requests.post(
                "https://api.deepseek.com/v1/embeddings",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return [item["embedding"] for item in result["data"]]
            else:
                raise Exception(f"Error from DeepSeek API: {response.text}")
                
        except Exception as e:
            print(f"Error creating embeddings: {e}")
            print("Using random embeddings for testing purposes")
            return [list(np.random.rand(VECTOR_DIMENSION).astype(float)) for _ in range(len(texts))]





class OceanBaseVectorStore(BaseVectorStore):
    """Vector store implementation using OceanBase."""
    
    def __init__(self):
        """Initialize the OceanBase vector store."""
        super().__init__()
        self.connection_string = f"mysql+pymysql://{OCEANBASE_USER}:{OCEANBASE_PASSWORD}@{OCEANBASE_HOST}:{OCEANBASE_PORT}/{OCEANBASE_DATABASE}"
        self.engine = create_engine(self.connection_string)
        self._initialize_tables()
    
    def _initialize_tables(self):
        """初始化OceanBase中的必要表。"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS documents (
                        id VARCHAR(36) PRIMARY KEY,
                        filename VARCHAR(255) NOT NULL,
                        content_type VARCHAR(100) NOT NULL,
                        size INT NOT NULL,
                        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata TEXT
                    )
                """))
                
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS document_chunks (
                        id VARCHAR(36) PRIMARY KEY,
                        document_id VARCHAR(36) NOT NULL,
                        content TEXT NOT NULL,
                        metadata TEXT,
                        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                    )
                """))
                
                conn.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS vectors (
                        id VARCHAR(36) PRIMARY KEY,
                        chunk_id VARCHAR(36) NOT NULL,
                        embedding BLOB NOT NULL,
                        FOREIGN KEY (chunk_id) REFERENCES document_chunks(id) ON DELETE CASCADE
                    )
                """))
                
                conn.commit()
        except Exception as e:
            print(f"初始化OceanBase表时出错: {e}")
            raise e
    
    def add_document(self, document_data: Dict[str, Any], chunks: List[Dict[str, Any]]) -> str:
        """
        将文档及其分块添加到向量存储中。
        
        参数:
            document_data: 文档元数据
            chunks: 文档分块列表
            
        返回:
            文档ID
        """
        document_id = document_data.get('id') or str(uuid.uuid4())
        
        try:
            with self.engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO documents (id, filename, content_type, size, metadata)
                        VALUES (:id, :filename, :content_type, :size, :metadata)
                    """),
                    {
                        "id": document_id,
                        "filename": document_data["filename"],
                        "content_type": document_data["content_type"],
                        "size": document_data["size"],
                        "metadata": json.dumps(document_data.get("metadata", {}))
                    }
                )
                
                batch_size = 10
                for i in range(0, len(chunks), batch_size):
                    batch = chunks[i:i+batch_size]
                    
                    texts = [chunk["content"] for chunk in batch]
                    
                    embeddings = self.create_embeddings(texts)
                    
                    for j, chunk in enumerate(batch):
                        chunk_id = chunk.get("id") or str(uuid.uuid4())
                        
                        conn.execute(
                            text("""
                                INSERT INTO document_chunks (id, document_id, content, metadata)
                                VALUES (:id, :document_id, :content, :metadata)
                            """),
                            {
                                "id": chunk_id,
                                "document_id": document_id,
                                "content": chunk["content"],
                                "metadata": json.dumps(chunk["metadata"])
                            }
                        )
                        
                        embedding_bytes = np.array(embeddings[j], dtype=np.float32).tobytes()
                        conn.execute(
                            text("""
                                INSERT INTO vectors (id, chunk_id, embedding)
                                VALUES (:id, :chunk_id, :embedding)
                            """),
                            {
                                "id": str(uuid.uuid4()),
                                "chunk_id": chunk_id,
                                "embedding": embedding_bytes
                            }
                        )
                
                conn.commit()
            
            return document_id
        except Exception as e:
            print(f"向OceanBase添加文档时出错: {e}")
            raise e
    
    def similarity_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        对查询执行相似度搜索。
        
        参数:
            query: 查询文本
            top_k: 返回的结果数量
            
        返回:
            包含文档分块和相似度分数的列表
        """
        try:
            query_embedding = self.create_embeddings([query])[0]
            query_embedding_array = np.array(query_embedding, dtype=np.float32)
            
            results = []
            
            with self.engine.connect() as conn:
                vectors_result = conn.execute(text("""
                    SELECT v.id, v.chunk_id, v.embedding, c.content, c.metadata, c.document_id, d.filename
                    FROM vectors v
                    JOIN document_chunks c ON v.chunk_id = c.id
                    JOIN documents d ON c.document_id = d.id
                """))
                
                for row in vectors_result:
                    embedding_bytes = row.embedding
                    embedding_array = np.frombuffer(embedding_bytes, dtype=np.float32)
                    
                    similarity = np.dot(query_embedding_array, embedding_array) / (
                        np.linalg.norm(query_embedding_array) * np.linalg.norm(embedding_array)
                    )
                    
                    results.append({
                        "chunk_id": row.chunk_id,
                        "document_id": row.document_id,
                        "filename": row.filename,
                        "content": row.content,
                        "metadata": json.loads(row.metadata),
                        "similarity": float(similarity)
                    })
            
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:top_k]
        except Exception as e:
            print(f"在OceanBase中执行相似度搜索时出错: {e}")
            raise e
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """通过ID获取文档。"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT * FROM documents WHERE id = :id"),
                    {"id": document_id}
                ).fetchone()
                
                if result:
                    return {
                        "id": result.id,
                        "filename": result.filename,
                        "content_type": result.content_type,
                        "size": result.size,
                        "upload_date": result.upload_date,
                        "metadata": json.loads(result.metadata) if result.metadata else {}
                    }
                
                return None
        except Exception as e:
            print(f"从OceanBase获取文档时出错: {e}")
            raise e
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """获取所有文档。"""
        try:
            documents = []
            
            with self.engine.connect() as conn:
                results = conn.execute(text("SELECT * FROM documents"))
                
                for row in results:
                    documents.append({
                        "id": row.id,
                        "filename": row.filename,
                        "content_type": row.content_type,
                        "size": row.size,
                        "upload_date": row.upload_date,
                        "metadata": json.loads(row.metadata) if row.metadata else {}
                    })
            
            return documents
        except Exception as e:
            print(f"从OceanBase获取所有文档时出错: {e}")
            raise e


def get_vector_store():
    """获取向量存储实现。"""
    try:
        vector_store = OceanBaseVectorStore()
        vector_store.get_all_documents()
        print("使用OceanBase向量存储")
        return vector_store
    except Exception as e:
        print(f"连接到OceanBase时出错: {e}")
        raise Exception(f"无法连接到OceanBase: {e}")
