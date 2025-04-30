"""
DeepSeek LLM integration for langchain.
"""
import requests
from typing import Any, List, Mapping, Optional
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM
from app.config.settings import DEEPSEEK_API_KEY, DEEPSEEK_CHAT_MODEL

class DeepSeekLLM(LLM):
    """LLM wrapper for DeepSeek API."""
    
    model_name: str = DEEPSEEK_CHAT_MODEL
    api_key: str = DEEPSEEK_API_KEY
    temperature: float = 0.7
    max_tokens: int = 1024
    
    @property
    def _llm_type(self) -> str:
        return "deepseek"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call the DeepSeek API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        if stop:
            payload["stop"] = stop
            
        try:
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers, 
                json=payload
            )
            
            if response.status_code != 200:
                raise ValueError(f"Error from DeepSeek API: {response.text}")
                
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            raise ValueError(f"Error calling DeepSeek API: {str(e)}")
