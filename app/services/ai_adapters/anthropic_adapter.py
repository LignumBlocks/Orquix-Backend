from typing import Optional
from app.services.ai_adapters.base import BaseAIAdapter
from app.schemas.ai_response import AIRequest, AIProviderEnum

class AnthropicAdapter(BaseAIAdapter):
    """Adaptador para Anthropic Claude 3 Haiku"""
    
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307", **kwargs):
        super().__init__(api_key, **kwargs)
        self.model = model
    
    @property
    def provider_name(self) -> AIProviderEnum:
        return AIProviderEnum.ANTHROPIC
    
    @property
    def base_url(self) -> str:
        return "https://api.anthropic.com/v1/messages"
    
    def _get_default_headers(self) -> dict:
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
    
    def _build_payload(self, request: AIRequest) -> dict:
        """Construye el payload específico de Anthropic"""
        payload = {
            "model": self.model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "messages": [
                {
                    "role": "user",
                    "content": request.prompt
                }
            ]
        }
        
        # Claude maneja el system message de forma diferente
        if request.system_message:
            payload["system"] = request.system_message
        
        return payload
    
    def _extract_response_text(self, response_data: dict) -> str:
        """Extrae el texto de respuesta de Anthropic"""
        try:
            content = response_data["content"]
            if isinstance(content, list) and len(content) > 0:
                return content[0]["text"]
            else:
                raise ValueError("Formato de contenido inesperado")
        except (KeyError, IndexError, TypeError) as e:
            raise ValueError(f"Formato de respuesta inesperado de Anthropic: {e}")
    
    def _extract_usage_info(self, response_data: dict) -> Optional[dict]:
        """Extrae información de uso de Anthropic"""
        usage = response_data.get("usage", {})
        
        if not usage:
            return None
            
        return {
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            "model": response_data.get("model", self.model)
        } 