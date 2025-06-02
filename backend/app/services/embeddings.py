from typing import List
import openai
from app.core.config import settings

class EmbeddingsService:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        self.model = "text-embedding-3-small"  # Modelo más reciente y económico de OpenAI

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Obtiene embeddings para una lista de textos usando la API de OpenAI.
        
        Args:
            texts: Lista de textos para generar embeddings
            
        Returns:
            Lista de vectores de embeddings
        """
        try:
            response = await openai.embeddings.create(
                model=self.model,
                input=texts
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            # En producción, deberías manejar errores específicos y logging
            raise Exception(f"Error al obtener embeddings: {str(e)}")

embeddings_service = EmbeddingsService() 