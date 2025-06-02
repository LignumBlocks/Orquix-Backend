from typing import Optional
from app.services.ai_adapters.base import BaseAIAdapter
from app.schemas.ai_response import AIRequest, AIProviderEnum

class OpenAIAdapter(BaseAIAdapter):
    """Adaptador para OpenAI GPT-4o-mini"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", **kwargs):
        super().__init__(api_key, **kwargs)
        self.model = model
    
    @property
    def provider_name(self) -> AIProviderEnum:
        return AIProviderEnum.OPENAI
    
    @property
    def base_url(self) -> str:
        return "https://api.openai.com/v1/chat/completions"
    
    def _get_default_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _build_payload(self, request: AIRequest) -> dict:
        """Construye el payload específico de OpenAI"""
        messages = []
        
        # Mensaje del sistema si existe
        if request.system_message:
            messages.append({
                "role": "system",
                "content": request.system_message
            })
        
        # Mensaje del usuario
        messages.append({
            "role": "user",
            "content": request.prompt
        })
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature
        }
        
        return payload
    
    def _extract_response_text(self, response_data: dict) -> str:
        """Extrae el texto de respuesta de OpenAI"""
        try:
            return response_data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise ValueError(f"Formato de respuesta inesperado de OpenAI: {e}")
    
    def _extract_usage_info(self, response_data: dict) -> Optional[dict]:
        """Extrae información de uso de OpenAI"""
        usage = response_data.get("usage", {})
        
        if not usage:
            return None
            
        return {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "model": response_data.get("model", self.model)
        } 