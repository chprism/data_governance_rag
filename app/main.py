"""
Main application file for the data governance knowledge base.
"""
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api.endpoints import router as api_router
from app.config.settings import UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = FastAPI(
    title="OceanBase知识库",
    description="基于OceanBase文档的知识库，具有RAG检索能力",
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
    <title>OceanBase知识库</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root {
            --deepseek-primary: #1e3a8a;
            --deepseek-secondary: #3b82f6;
            --deepseek-background: #f8fafc;
            --deepseek-text: #1e293b;
            --deepseek-border: #e2e8f0;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            max-width: 960px;
            margin: 0 auto;
            padding: 20px;
            background-color: var(--deepseek-background);
            color: var(--deepseek-text);
            line-height: 1.6;
        }
        
        h1, h2, h3 {
            color: var(--deepseek-primary);
            font-weight: 600;
        }
        
        h1 {
            font-size: 28px;
            margin-bottom: 24px;
            text-align: center;
        }
        
        .container {
            margin-top: 28px;
            background-color: white;
            padding: 24px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
        }
        
        input[type="file"], input[type="text"] {
            width: 100%;
            padding: 10px;
            box-sizing: border-box;
            border: 1px solid var(--deepseek-border);
            border-radius: 6px;
            font-size: 16px;
        }
        
        button {
            background-color: var(--deepseek-secondary);
            color: white;
            padding: 12px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
            font-size: 16px;
            transition: background-color 0.2s;
        }
        
        button:hover {
            background-color: var(--deepseek-primary);
        }
        
        .result {
            margin-top: 24px;
            padding: 20px;
            border: 1px solid var(--deepseek-border);
            border-radius: 6px;
            background-color: white;
        }
        
        .documents {
            margin-top: 24px;
        }
        
        .document-item {
            padding: 16px;
            margin-bottom: 16px;
            border: 1px solid var(--deepseek-border);
            border-radius: 6px;
            background-color: white;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .document-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
    </style>
</head>
<body>
    <h1>OceanBase知识库</h1>
    
    <div class="container">
        <h2>上传文档</h2>
        <div class="form-group">
            <label for="document">选择文档：</label>
            <input type="file" id="document" name="document">
        </div>
        <button onclick="uploadDocument()">上传</button>
    </div>
    
    <div class="container">
        <h2>查询知识库</h2>
        <div class="form-group">
            <label for="query">输入问题：</label>
            <input type="text" id="query" name="query" placeholder="请输入您的问题...">
        </div>
        <button onclick="queryKnowledgeBase()">提交</button>
        
        <div id="result" class="result" style="display: none;"></div>
    </div>
    
    <div class="container">
        <h2>文档列表</h2>
        <button onclick="loadDocuments()">刷新文档</button>
        <div id="documents" class="documents"></div>
    </div>
    
    <script>
        // 页面加载时加载文档
        window.onload = function() {
            loadDocuments();
        };
        
        // 上传文档
        async function uploadDocument() {
            const fileInput = document.getElementById('document');
            const file = fileInput.files[0];
            
            if (!file) {
                alert('请选择一个文件');
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
                    alert('文档上传成功');
                    loadDocuments();
                } else {
                    alert(`错误: ${data.detail}`);
                }
            } catch (error) {
                alert(`错误: ${error.message}`);
            }
        }
        
        // 查询知识库
        async function queryKnowledgeBase() {
            const queryInput = document.getElementById('query');
            const query = queryInput.value.trim();
            
            if (!query) {
                alert('请输入问题');
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
                        <h3>回答:</h3>
                        <p>${data.response}</p>
                        <h3>检索到的文档:</h3>
                        <ul>
                            ${data.retrieved_documents.map(doc => `
                                <li>
                                    <strong>${doc.filename}</strong> (相关度: ${doc.similarity.toFixed(2)})
                                    <p>${doc.content.substring(0, 200)}...</p>
                                </li>
                            `).join('')}
                        </ul>
                    `;
                    resultDiv.style.display = 'block';
                } else {
                    alert(`错误: ${data.detail}`);
                }
            } catch (error) {
                alert(`错误: ${error.message}`);
            }
        }
        
        // 加载文档
        async function loadDocuments() {
            try {
                const response = await fetch('/api/documents');
                const data = await response.json();
                
                const documentsDiv = document.getElementById('documents');
                
                if (data.documents.length === 0) {
                    documentsDiv.innerHTML = '<p>未找到文档</p>';
                    return;
                }
                
                documentsDiv.innerHTML = data.documents.map(doc => `
                    <div class="document-item">
                        <h3>${doc.filename}</h3>
                        <p><strong>上传日期:</strong> ${new Date(doc.upload_date).toLocaleString()}</p>
                        <p><strong>大小:</strong> ${formatFileSize(doc.size)}</p>
                        <p><strong>类型:</strong> ${doc.content_type}</p>
                    </div>
                `).join('');
            } catch (error) {
                alert(`错误: ${error.message}`);
            }
        }
        
        // 格式化文件大小
        function formatFileSize(bytes) {
            if (bytes < 1024) {
                return bytes + ' 字节';
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
