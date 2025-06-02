import asyncio
import httpx
import json
from app.core.config import settings

async def test_anthropic_debug():
    """Test de diagnóstico para Anthropic"""
    
    print("🔍 Diagnóstico directo de API de Anthropic...")
    
    api_key = settings.ANTHROPIC_API_KEY
    print(f"📋 API Key configurada: {'SÍ' if api_key else 'NO'}")
    
    if not api_key:
        print("❌ ANTHROPIC_API_KEY no está configurada")
        return
    
    print(f"🔑 API Key (primeros 10 chars): {api_key[:10]}...")
    
    # Test directo a la API de Anthropic
    url = "https://api.anthropic.com/v1/messages"
    
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    payload = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 50,
        "temperature": 0.7,
        "messages": [
            {
                "role": "user",
                "content": "Hola, ¿cómo estás?"
            }
        ]
    }
    
    print("\n📤 Enviando request directa a Anthropic...")
    print(f"🌐 URL: {url}")
    print(f"📦 Payload: {json.dumps(payload, indent=2)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                url,
                json=payload,
                headers=headers
            )
            
            print(f"\n📥 Respuesta HTTP: {response.status_code}")
            print(f"📋 Headers de respuesta:")
            for key, value in response.headers.items():
                print(f"   {key}: {value}")
            
            # Intentar obtener el contenido de la respuesta
            try:
                response_text = response.text
                print(f"\n📄 Contenido de respuesta:")
                print(response_text)
                
                # Si es JSON, parsearlo
                if response.headers.get("content-type", "").startswith("application/json"):
                    try:
                        response_json = response.json()
                        print(f"\n📊 JSON parseado:")
                        print(json.dumps(response_json, indent=2))
                    except json.JSONDecodeError:
                        print("❌ No se pudo parsear como JSON")
                        
            except Exception as e:
                print(f"❌ Error leyendo contenido: {e}")
            
            # Verificar si la respuesta es exitosa
            if response.status_code == 200:
                print("\n✅ Request exitosa!")
            else:
                print(f"\n❌ Request falló con código {response.status_code}")
                
        except httpx.RequestError as e:
            print(f"\n❌ Error de red: {e}")
        except Exception as e:
            print(f"\n❌ Error inesperado: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_anthropic_debug()) 