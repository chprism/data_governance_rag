"""
Run script for the data governance knowledge base application.
"""
import os
import uvicorn
from app.main import app
from app.config.settings import OPENAI_API_KEY

if __name__ == "__main__":
    if not OPENAI_API_KEY or OPENAI_API_KEY == "your_openai_api_key":
        print("WARNING: OpenAI API key is not set. Please set it in the .env file.")
        print("Using a placeholder API key for testing purposes.")
        os.environ["OPENAI_API_KEY"] = "sk-placeholder-api-key"
    
    print("Starting the data governance knowledge base application...")
    print("The application will be available at http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
