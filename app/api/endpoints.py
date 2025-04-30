"""
API endpoints for the data governance knowledge base.
"""
import os
import shutil
from typing import List, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.core.vector_store import get_vector_store
from app.core.rag_chain import RAGChain
from app.utils.document_processor import process_document, allowed_file
from app.config.settings import UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

router = APIRouter()

vector_store = get_vector_store()

rag_chain = RAGChain()


@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document to the knowledge base.
    
    Args:
        file: Document file
        
    Returns:
        Document ID
    """
    try:
        if not file:
            raise HTTPException(status_code=400, detail="No file provided")
            
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
            
        if not allowed_file(file.filename):
            raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}")
        
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        
        # 确保文件内容可以被读取
        try:
            file_content = await file.read()
            if not file_content:
                raise HTTPException(status_code=400, detail="File is empty")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
        
        # 写入文件
        try:
            with open(file_path, "wb") as buffer:
                buffer.write(file_content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
        
        try:
            document_chunks, document_id = process_document(file_path)
            
            document_data = {
                "id": document_id,
                "filename": file.filename,
                "content_type": file.content_type,
                "size": os.path.getsize(file_path),
            }
            
            vector_store.add_document(document_data, document_chunks)
        
            return JSONResponse(
                content={
                    "document_id": document_id,
                    "message": "Document uploaded successfully",
                    "filename": file.filename,
                    "size": os.path.getsize(file_path)
                },
                status_code=200
            )
            
        except Exception as e:
            # 处理文档处理错误
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")
            
    except HTTPException as he:
        # 重新抛出HTTP异常
        raise he
    except Exception as e:
        # 处理其他所有异常
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/documents")
async def get_documents():
    """
    Get all documents in the knowledge base.
    
    Returns:
        List of documents
    """
    documents = vector_store.get_all_documents()
    return {"documents": documents}


@router.get("/documents/{document_id}")
async def get_document(document_id: str):
    """
    Get a document by ID.
    
    Args:
        document_id: Document ID
        
    Returns:
        Document data
    """
    document = vector_store.get_document(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"document": document}


@router.post("/query")
async def query_knowledge_base(query: str = Form(...)):
    """
    Query the knowledge base.
    
    Args:
        query: User query
        
    Returns:
        Response from the RAG chain
    """
    try:
        result = rag_chain.query(query)
        return {
            "query": query,
            "response": result["response"],
            "retrieved_documents": result["retrieved_documents"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
