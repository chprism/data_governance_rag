# 数据治理知识库 (Data Governance Knowledge Base)

基于Python 3.12.8、langchain、langgraph和OceanBase的AI数据治理知识库，支持文档上传和检索功能，结合RAG技术和ChatGPT模型。

## 功能特点

- 支持多种文档格式上传（txt、pdf、docx、md、csv、json）
- 使用RAG（检索增强生成）技术进行智能问答
- 支持中文处理和检索
- 使用OceanBase作为向量存储（自动回退到SQLite）
- 基于ChatGPT模型生成回答

## 系统要求

- Python 3.12.8
- Docker（用于运行OceanBase）
- OpenAI API密钥

## 安装步骤

1. 克隆代码库并进入项目目录

```bash
git clone <repository-url>
cd data_governance_rag
```

2. 创建并激活虚拟环境

```bash
python -m venv venv
#source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. 安装依赖

```bash
pip install -r requirements.txt
```

4. 配置环境变量

编辑`.env`文件，并更新以下配置：

```
OPENAI_API_KEY=your_openai_api_key
OCEANBASE_HOST=localhost
OCEANBASE_PORT=2881
OCEANBASE_USER=root
OCEANBASE_PASSWORD=oceanbase
OCEANBASE_DATABASE=test
```

5. 启动OceanBase

```bash
docker-compose up -d
```

## 运行应用

```bash
python run.py
```

应用将在 http://localhost:8000 上运行。

## 使用方法

1. 访问 http://localhost:8000
2. 上传数据治理相关文档
3. 在查询框中输入问题（支持中文）
4. 查看系统返回的回答和相关文档

## 故障排除

- 如果OceanBase连接失败，系统会自动回退到SQLite存储
- 如果OpenAI API密钥未设置或无效，系统会使用随机嵌入和预设回答进行测试

## 技术栈

- FastAPI: Web框架
- langchain 0.3.23: LLM应用框架
- langgraph 0.3.31: 工作流编排
- OceanBase 4.3.5-lts: 向量存储
- OpenAI ChatGPT: 大型语言模型
- SQLite: 备用数据库

## 项目结构

```
data_governance_rag/
├── app/
│   ├── api/            # API端点
│   ├── config/         # 配置设置
│   ├── core/           # 核心功能（向量存储、RAG链）
│   ├── models/         # 数据模型
│   └── utils/          # 工具函数
├── static/             # 静态文件
├── templates/          # HTML模板
├── uploads/            # 上传文件存储
├── .env                # 环境变量
├── docker-compose.yml  # Docker配置
├── requirements.txt    # 依赖列表
└── run.py              # 应用入口
```


python -m uvicorn app.main:app --reload


