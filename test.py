#!/usr/bin/env python
"""
Test script for the data governance knowledge base.
"""
import os
import requests
import time
import sys

# Base URL for the API
BASE_URL = "http://localhost:8000/api"

def test_upload_document(file_path):
    """Test document upload."""
    print(f"Testing document upload: {file_path}")
    
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f)}
        response = requests.post(f"{BASE_URL}/documents/upload", files=files)
    
    if response.status_code == 200:
        print("Document upload successful!")
        print(f"Response: {response.json()}")
        return response.json().get("document_id")
    else:
        print(f"Document upload failed: {response.status_code}")
        print(f"Response: {response.json()}")
        return None

def test_get_documents():
    """Test getting all documents."""
    print("Testing get documents")
    
    response = requests.get(f"{BASE_URL}/documents")
    
    if response.status_code == 200:
        print("Get documents successful!")
        print(f"Response: {response.json()}")
        return response.json().get("documents")
    else:
        print(f"Get documents failed: {response.status_code}")
        print(f"Response: {response.json()}")
        return None

def test_query(query):
    """Test querying the knowledge base."""
    print(f"Testing query: {query}")
    
    data = {"query": query}
    response = requests.post(f"{BASE_URL}/query", data=data)
    
    if response.status_code == 200:
        print("Query successful!")
        print(f"Response: {response.json()}")
        return response.json()
    else:
        print(f"Query failed: {response.status_code}")
        print(f"Response: {response.json()}")
        return None

def create_test_document(content, filename="test_document.txt"):
    """Create a test document."""
    file_path = os.path.join(os.path.dirname(__file__), filename)
    
    with open(file_path, "w") as f:
        f.write(content)
    
    return file_path

def main():
    """Main test function."""
    # Create test document
    test_content = """
    # Data Governance Best Practices
    
    Data governance is the process of managing the availability, usability, integrity, and security of data in enterprise systems.
    
    ## Key Components
    
    1. **Data Quality**: Ensuring data is accurate, complete, and consistent
    2. **Data Security**: Protecting data from unauthorized access and corruption
    3. **Data Compliance**: Adhering to regulations and standards
    4. **Data Stewardship**: Assigning responsibility for data management
    
    ## Benefits
    
    - Improved decision-making
    - Enhanced data security
    - Reduced costs
    - Better regulatory compliance
    """
    
    test_file = create_test_document(test_content)
    
    # Test document upload
    document_id = test_upload_document(test_file)
    
    if not document_id:
        print("Test failed: Document upload failed")
        sys.exit(1)
    
    # Wait for processing
    print("Waiting for document processing...")
    time.sleep(5)
    
    # Test get documents
    documents = test_get_documents()
    
    if not documents:
        print("Test failed: Get documents failed")
        sys.exit(1)
    
    # Test query
    query_result = test_query("What are the key components of data governance?")
    
    if not query_result:
        print("Test failed: Query failed")
        sys.exit(1)
    
    print("\nAll tests passed!")

if __name__ == "__main__":
    main()
