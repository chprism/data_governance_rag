"""
Configuration settings for the application.
"""
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

OCEANBASE_HOST = os.getenv("OCEANBASE_HOST", "localhost")
OCEANBASE_PORT = int(os.getenv("OCEANBASE_PORT", "2881"))
OCEANBASE_USER = os.getenv("OCEANBASE_USER", "root")
OCEANBASE_PASSWORD = os.getenv("OCEANBASE_PASSWORD", "oceanbase")
OCEANBASE_DATABASE = os.getenv("OCEANBASE_DATABASE", "test")

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'md', 'csv', 'json'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size

EMBEDDING_MODEL = "text-embedding-3-small"
VECTOR_DIMENSION = 1536  # Dimension for text-embedding-3-small
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
