"""
Test simple para diagnosticar problemas con los endpoints.
"""
from fastapi.testclient import TestClient
from app.main import app

def test_simple_endpoints():
    """Test simple para verificar que los endpoints básicos funcionan."""
    
    print("🧪 Test simple de endpoints...")
    
    # Crear cliente de test
    client = TestClient(app)
    
    # Headers de autenticación mock
    headers = {
        "Authorization": "Bearer dev-mock-token-12345",
        "Content-Type": "application/json"
    }
    
    # Test 1: Verificar que la aplicación se inicia
    print("\n📊 Test 1: Verificar aplicación...")
    response = client.get("/")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Aplicación funcionando")
    else:
        print(f"❌ Error en aplicación: {response.text}")
        return
    
    # Test 2: Verificar autenticación
    print("\n🔐 Test 2: Verificar autenticación...")
    response = client.get("/api/v1/auth/session", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        session_data = response.json()
        print(f"✅ Autenticación funcionando: {session_data.get('user', {}).get('email', 'N/A')}")
    else:
        print(f"❌ Error en autenticación: {response.text}")
        return
    
    # Test 3: Verificar que los nuevos endpoints están registrados
    print("\n📋 Test 3: Verificar endpoints registrados...")
    response = client.get("/docs")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Documentación accesible")
    else:
        print(f"❌ Error en documentación: {response.text}")
    
    print("\n🎉 Tests simples completados!")


if __name__ == "__main__":
    test_simple_endpoints() 