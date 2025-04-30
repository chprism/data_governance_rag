"""
Vector store implementation with support for both OceanBase and SQLite.
"""
import uuid
import json
import os
import sqlite3
from typing import List, Dict, Any, Optional
import numpy as np
import pymysql
from sqlalchemy import create_engine, text
from openai import OpenAI
from app.config.settings import (
    OCEANBASE_HOST, 
    OCEANBASE_PORT, 
    OCEANBASE_USER, 
    OCEANBASE_PASSWORD, 
    OCEANBASE_DATABASE,
    OPENAI_API_KEY,
    EMBEDDING_MODEL,
    VECTOR_DIMENSION
)


class BaseVectorStore:
    """Base vector store implementation."""
    
    def __init__(self):
        """Initialize the base vector store."""
        self.client = OpenAI(api_key=OPENAI_API_KEY)
    
    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for a list of texts using OpenAI API."""
        response = self.client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts
        )
        return [item.embedding for item in response.data]


class SQLiteVectorStore(BaseVectorStore):
    """Vector store implementation using SQLite."""
    
    def __init__(self, db_path=None):
        """Initialize the SQLite vector store."""
        super().__init__()
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "vector_store.db")
        self.db_path = db_path
        self._initialize_tables()
    
    def _initialize_tables(self):
        """Initialize the necessary tables in SQLite."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                content_type TEXT NOT NULL,
                size INTEGER NOT NULL,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vectors (
                id TEXT PRIMARY KEY,
                chunk_id TEXT NOT NULL,
                embedding BLOB NOT NULL,
                FOREIGN KEY (chunk_id) REFERENCES document_chunks(id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_document(self, document_data: Dict[str, Any], chunks: List[Dict[str, Any]]) -> str:
        """
        Add a document and its chunks to the vector store.
        
        Args:
            document_data: Document metadata
            chunks: List of document chunks
            
        Returns:
            Document ID
        """
        document_id = document_data.get('id') or str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """
                INSERT INTO documents (id, filename, content_type, size, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    document_data["filename"],
                    document_data["content_type"],
                    document_data["size"],
                    json.dumps(document_data.get("metadata", {}))
                )
            )
            
            batch_size = 10
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i+batch_size]
                
                texts = [chunk["content"] for chunk in batch]
                
                embeddings = self.create_embeddings(texts)
                
                for j, chunk in enumerate(batch):
                    chunk_id = chunk.get("id") or str(uuid.uuid4())
                    
                    cursor.execute(
                        """
                        INSERT INTO document_chunks (id, document_id, content, metadata)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            chunk_id,
                            document_id,
                            chunk["content"],
                            json.dumps(chunk["metadata"])
                        )
                    )
                    
                    embedding_bytes = np.array(embeddings[j], dtype=np.float32).tobytes()
                    cursor.execute(
                        """
                        INSERT INTO vectors (id, chunk_id, embedding)
                        VALUES (?, ?, ?)
                        """,
                        (
                            str(uuid.uuid4()),
                            chunk_id,
                            embedding_bytes
                        )
                    )
            
            conn.commit()
            return document_id
        
        except Exception as e:
            conn.rollback()
            raise e
        
        finally:
            conn.close()
    
    def similarity_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform similarity search for a query.
        
        Args:
            query: Query text
            top_k: Number of top results to return
            
        Returns:
            List of document chunks with similarity scores
        """
        query_embedding = self.create_embeddings([query])[0]
        query_embedding_array = np.array(query_embedding, dtype=np.float32)
        
        results = []
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT v.id, v.chunk_id, v.embedding, c.content, c.metadata, c.document_id, d.filename
                FROM vectors v
                JOIN document_chunks c ON v.chunk_id = c.id
                JOIN documents d ON c.document_id = d.id
            """)
            
            for row in cursor.fetchall():
                embedding_bytes = row["embedding"]
                embedding_array = np.frombuffer(embedding_bytes, dtype=np.float32)
                
                similarity = np.dot(query_embedding_array, embedding_array) / (
                    np.linalg.norm(query_embedding_array) * np.linalg.norm(embedding_array)
                )
                
                results.append({
                    "chunk_id": row["chunk_id"],
                    "document_id": row["document_id"],
                    "filename": row["filename"],
                    "content": row["content"],
                    "metadata": json.loads(row["metadata"]),
                    "similarity": float(similarity)
                })
        
        finally:
            conn.close()
        
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT * FROM documents WHERE id = ?",
                (document_id,)
            )
            
            result = cursor.fetchone()
            
            if result:
                return {
                    "id": result["id"],
                    "filename": result["filename"],
                    "content_type": result["content_type"],
                    "size": result["size"],
                    "upload_date": result["upload_date"],
                    "metadata": json.loads(result["metadata"]) if result["metadata"] else {}
                }
            
            return None
        
        finally:
            conn.close()
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all documents."""
        documents = []
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM documents")
            
            for row in cursor.fetchall():
                documents.append({
                    "id": row["id"],
                    "filename": row["filename"],
                    "content_type": row["content_type"],
                    "size": row["size"],
                    "upload_date": row["upload_date"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
                })
            
            return documents
        
        finally:
            conn.close()


class OceanBaseVectorStore(BaseVectorStore):
    """Vector store implementation using OceanBase."""
    
    def __init__(self):
        """Initialize the OceanBase vector store."""
        super().__init__()
        self.connection_string = f"mysql+pymysql://{OCEANBASE_USER}:{OCEANBASE_PASSWORD}@{OCEANBASE_HOST}:{OCEANBASE_PORT}/{OCEANBASE_DATABASE}"
        self.engine = create_engine(self.connection_string)
        self._initialize_tables()
    
    def _initialize_tables(self):
        """Initialize the necessary tables in OceanBase."""
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
            print(f"Error initializing OceanBase tables: {e}")
            print("Falling back to SQLite vector store")
    
    def add_document(self, document_data: Dict[str, Any], chunks: List[Dict[str, Any]]) -> str:
        """
        Add a document and its chunks to the vector store.
        
        Args:
            document_data: Document metadata
            chunks: List of document chunks
            
        Returns:
            Document ID
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
            print(f"Error adding document to OceanBase: {e}")
            print("Falling back to SQLite vector store")
            sqlite_store = SQLiteVectorStore()
            return sqlite_store.add_document(document_data, chunks)
    
    def similarity_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform similarity search for a query.
        
        Args:
            query: Query text
            top_k: Number of top results to return
            
        Returns:
            List of document chunks with similarity scores
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
            print(f"Error performing similarity search in OceanBase: {e}")
            print("Falling back to SQLite vector store")
            sqlite_store = SQLiteVectorStore()
            return sqlite_store.similarity_search(query, top_k)
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID."""
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
            print(f"Error getting document from OceanBase: {e}")
            print("Falling back to SQLite vector store")
            sqlite_store = SQLiteVectorStore()
            return sqlite_store.get_document(document_id)
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all documents."""
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
            print(f"Error getting all documents from OceanBase: {e}")
            print("Falling back to SQLite vector store")
            sqlite_store = SQLiteVectorStore()
            return sqlite_store.get_all_documents()


def get_vector_store():
    """Get the appropriate vector store implementation."""
    try:
        vector_store = OceanBaseVectorStore()
        vector_store.get_all_documents()
        print("Using OceanBase vector store")
        return vector_store
    except Exception as e:
        print(f"Error connecting to OceanBase: {e}")
        print("Falling back to SQLite vector store")
        return SQLiteVectorStore()
