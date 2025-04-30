"""
Utility functions for processing documents.
"""
import os
import uuid
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
    CSVLoader,
    UnstructuredMarkdownLoader,
)
from app.config.settings import CHUNK_SIZE, CHUNK_OVERLAP, ALLOWED_EXTENSIONS


def allowed_file(filename: str) -> bool:
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_loader_for_file(file_path: str):
    """Get the appropriate document loader based on file extension."""
    try:
        ext = file_path.split('.')[-1].lower()
        
        if ext == 'txt':
            return TextLoader(file_path, encoding='utf-8')
        elif ext == 'pdf':
            try:
                return PyPDFLoader(file_path)
            except Exception as e:
                raise ValueError(f"Error loading PDF file: {str(e)}")
        elif ext == 'docx':
            try:
                return Docx2txtLoader(file_path)
            except Exception as e:
                raise ValueError(f"Error loading DOCX file: {str(e)}")
        elif ext == 'csv':
            try:
                return CSVLoader(file_path)
            except Exception as e:
                raise ValueError(f"Error loading CSV file: {str(e)}")
        elif ext == 'md':
            try:
                return UnstructuredMarkdownLoader(file_path)
            except Exception as e:
                raise ValueError(f"Error loading Markdown file: {str(e)}")
        elif ext == 'json':
            return TextLoader(file_path, encoding='utf-8')  # Simple text loader for JSON
        else:
            raise ValueError(f"Unsupported file extension: {ext}")
    except Exception as e:
        raise ValueError(f"Error determining file type or loading file: {str(e)}")


def process_document(file_path: str) -> tuple[List[Dict[str, Any]], str]:
    """
    Process a document file and split it into chunks.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        Tuple containing list of document chunks with metadata and the document ID
    """
    try:
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")
            
        if not os.path.getsize(file_path):
            raise ValueError("File is empty")
            
        loader = get_loader_for_file(file_path)
        try:
            documents = loader.load()
        except Exception as e:
            raise ValueError(f"Error loading document content: {str(e)}")
            
        if not documents:
            raise ValueError("No content found in document")
        
        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
                length_function=len,
            )
            
            chunks = text_splitter.split_documents(documents)
            
            if not chunks:
                raise ValueError("Document was split but no chunks were created")
                
            document_chunks = []
            document_id = str(uuid.uuid4())
            filename = os.path.basename(file_path)
            
            for i, chunk in enumerate(chunks):
                chunk_id = str(uuid.uuid4())
                document_chunks.append({
                    "id": chunk_id,
                    "document_id": document_id,
                    "content": chunk.page_content,
                    "metadata": {
                        **chunk.metadata,
                        "filename": filename,
                        "chunk_index": i,
                    }
                })
                
            return document_chunks, document_id
            
        except Exception as e:
            raise ValueError(f"Error splitting document into chunks: {str(e)}")
            
    except Exception as e:
        raise ValueError(f"Error processing document: {str(e)}")
