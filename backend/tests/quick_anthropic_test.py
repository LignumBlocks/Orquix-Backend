import asyncio
import httpx
from app.core.config import settings

async def quick_test():
    print('🔍 Test rápido de Anthropic...')
    print(f'🔑 API Key (primeros 15 chars): {settings.ANTHROPIC_API_KEY[:15]}...')
    
    headers = {
        'x-api-key': settings.ANTHROPIC_API_KEY,
        'Content-Type': 'application/json',
        'anthropic-version': '2023-06-01'
    }
    
    payload = {
        'model': 'claude-3-haiku-20240307',
        'max_tokens': 10,
        'messages': [{'role': 'user', 'content': 'Hi'}]
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(
                'https://api.anthropic.com/v1/messages',
                json=payload,
                headers=headers
            )
            
            print(f'📊 Status: {response.status_code}')
            
            if response.status_code == 200:
                print('✅ Anthropic funcionando!')
                data = response.json()
                content = data.get('content', [{}])
                if content:
                    text = content[0].get('text', 'N/A')
                    print(f'📝 Respuesta: {text}')
            else:
                print(f'❌ Error {response.status_code}')
                print(f'📄 Respuesta: {response.text[:200]}...')
                
        except Exception as e:
            print(f'❌ Error: {e}')

if __name__ == "__main__":
    asyncio.run(quick_test()) 