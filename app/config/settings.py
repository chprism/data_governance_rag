"""
Configuration settings for the application.
"""
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

OCEANBASE_HOST = os.getenv("OCEANBASE_HOST", "localhost")
OCEANBASE_PORT = int(os.getenv("OCEANBASE_PORT", "2881"))
OCEANBASE_USER = os.getenv("OCEANBASE_USER", "root")
OCEANBASE_PASSWORD = os.getenv("OCEANBASE_PASSWORD", "oceanbase")
OCEANBASE_DATABASE = os.getenv("OCEANBASE_DATABASE", "test")

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'md', 'csv', 'json'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size

DEEPSEEK_EMBEDDING_MODEL = "deepseek-ai/deepseek-embed-v1"
DEEPSEEK_CHAT_MODEL = "deepseek-ai/deepseek-chat"
VECTOR_DIMENSION = 1024  # DeepSeek embedding向量维度
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
