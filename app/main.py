"""
Main application file for the data governance knowledge base.
"""
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api.endpoints import router as api_router
from app.config.settings import UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = FastAPI(
    title="Data Governance Knowledge Base",
    description="A data governance knowledge base with RAG capabilities",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# 设置静态文件目录
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 设置模板目录
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
os.makedirs(templates_dir, exist_ok=True)
templates = Jinja2Templates(directory=templates_dir)

# 添加API路由
app.include_router(api_router, prefix="/api")

# 创建index.html
with open(os.path.join(templates_dir, "index.html"), "w") as f:
    f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>Data Governance Knowledge Base</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #333;
        }
        .container {
            margin-top: 20px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
        }
        input[type="file"], input[type="text"] {
            width: 100%;
            padding: 8px;
            box-sizing: border-box;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 15px;
            border: none;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
        .result {
            margin-top: 20px;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background-color: #f9f9f9;
        }
        .documents {
            margin-top: 20px;
        }
        .document-item {
            padding: 10px;
            margin-bottom: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <h1>Data Governance Knowledge Base</h1>
    
    <div class="container">
        <h2>Upload Document</h2>
        <div class="form-group">
            <label for="document">Select Document:</label>
            <input type="file" id="document" name="document">
        </div>
        <button onclick="uploadDocument()">Upload</button>
    </div>
    
    <div class="container">
        <h2>Query Knowledge Base</h2>
        <div class="form-group">
            <label for="query">Enter Query:</label>
            <input type="text" id="query" name="query" placeholder="Ask a question...">
        </div>
        <button onclick="queryKnowledgeBase()">Submit</button>
        
        <div id="result" class="result" style="display: none;"></div>
    </div>
    
    <div class="container">
        <h2>Documents</h2>
        <button onclick="loadDocuments()">Refresh Documents</button>
        <div id="documents" class="documents"></div>
    </div>
    
    <script>
        // Load documents on page load
        window.onload = function() {
            loadDocuments();
        };
        
        // Upload document
        async function uploadDocument() {
            const fileInput = document.getElementById('document');
            const file = fileInput.files[0];
            
            if (!file) {
                alert('Please select a file');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await fetch('/api/documents/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    alert('Document uploaded successfully');
                    loadDocuments();
                } else {
                    alert(`Error: ${data.detail}`);
                }
            } catch (error) {
                alert(`Error: ${error.message}`);
            }
        }
        
        // Query knowledge base
        async function queryKnowledgeBase() {
            const queryInput = document.getElementById('query');
            const query = queryInput.value.trim();
            
            if (!query) {
                alert('Please enter a query');
                return;
            }
            
            const formData = new FormData();
            formData.append('query', query);
            
            try {
                const response = await fetch('/api/query', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    const resultDiv = document.getElementById('result');
                    resultDiv.innerHTML = `
                        <h3>Response:</h3>
                        <p>${data.response}</p>
                        <h3>Retrieved Documents:</h3>
                        <ul>
                            ${data.retrieved_documents.map(doc => `
                                <li>
                                    <strong>${doc.filename}</strong> (Score: ${doc.similarity.toFixed(2)})
                                    <p>${doc.content.substring(0, 200)}...</p>
                                </li>
                            `).join('')}
                        </ul>
                    `;
                    resultDiv.style.display = 'block';
                } else {
                    alert(`Error: ${data.detail}`);
                }
            } catch (error) {
                alert(`Error: ${error.message}`);
            }
        }
        
        // Load documents
        async function loadDocuments() {
            try {
                const response = await fetch('/api/documents');
                const data = await response.json();
                
                const documentsDiv = document.getElementById('documents');
                
                if (data.documents.length === 0) {
                    documentsDiv.innerHTML = '<p>No documents found</p>';
                    return;
                }
                
                documentsDiv.innerHTML = data.documents.map(doc => `
                    <div class="document-item">
                        <h3>${doc.filename}</h3>
                        <p><strong>Upload Date:</strong> ${new Date(doc.upload_date).toLocaleString()}</p>
                        <p><strong>Size:</strong> ${formatFileSize(doc.size)}</p>
                        <p><strong>Type:</strong> ${doc.content_type}</p>
                    </div>
                `).join('');
            } catch (error) {
                alert(`Error: ${error.message}`);
            }
        }
        
        // Format file size
        function formatFileSize(bytes) {
            if (bytes < 1024) {
                return bytes + ' bytes';
            } else if (bytes < 1024 * 1024) {
                return (bytes / 1024).toFixed(2) + ' KB';
            } else {
                return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
            }
        }
    </script>
</body>
</html>
    """)

app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """首页路由"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
