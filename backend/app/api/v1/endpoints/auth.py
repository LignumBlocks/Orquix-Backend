from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import logging
from datetime import datetime

from app.core.config import settings
from app.schemas.auth import (
    SessionResponse, 
    SessionUser, 
    SignOutRequest, 
    SignOutResponse,
    TokenValidationResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer(auto_error=False)


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[SessionUser]:
    """
    Obtiene el usuario actual desde el token JWT de NextAuth.js
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    
    # 🔐 MODO DESARROLLO/TESTING: Aceptar token mock
    # TODO: Remover en producción final cuando tengamos autenticación real
    if token == "dev-mock-token-12345":
        logger.info(f"🔐 Usando autenticación mock en {settings.ENVIRONMENT}")
        return SessionUser(
            id="550e8400-e29b-41d4-a716-446655440000",  # UUID válido para desarrollo
            name="Developer User",
            email="dev@orquix.com",
            image=None
        )
    
    try:
        # Decodificar token JWT de NextAuth.js
        payload = jwt.decode(
            token, 
            settings.JWT_PUBLIC_KEY, 
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_signature": False}  # En producción, verificar firma
        )
        
        user_id = payload.get("sub")
        name = payload.get("name")
        email = payload.get("email")
        picture = payload.get("picture")
        
        if not user_id:
            return None
            
        return SessionUser(
            id=user_id,
            name=name,
            email=email,
            image=picture
        )
        
    except jwt.DecodeError:
        logger.warning("Token JWT inválido")
        return None
    except jwt.ExpiredSignatureError:
        logger.warning("Token JWT expirado")
        return None
    except Exception as e:
        logger.error(f"Error procesando token JWT: {e}")
        return None


@router.get("/session", response_model=SessionResponse)
async def get_session(
    request: Request,
    current_user: Optional[SessionUser] = Depends(get_current_user)
) -> SessionResponse:
    """
    GET /api/auth/session
    
    Obtiene la sesión actual del usuario (compatible con NextAuth.js)
    """
    if not current_user:
        return SessionResponse(user=None, expires=None, accessToken=None)
    
    # En producción, obtener expires del token JWT
    # Por ahora retornamos un valor por defecto
    expires = datetime.utcnow().isoformat() + "Z"
    
    return SessionResponse(
        user=current_user,
        expires=expires,
        accessToken=None  # No exponemos el token por seguridad
    )


@router.post("/signout", response_model=SignOutResponse)
async def sign_out(
    request: Request,
    response: Response,
    body: Optional[SignOutRequest] = None
) -> SignOutResponse:
    """
    POST /api/auth/signout
    
    Cierra la sesión del usuario (compatible con NextAuth.js)
    """
    # En un entorno real, aquí invalidaríamos el token en el servidor
    # o agregaríamos el token a una lista negra
    
    callback_url = None
    if body and body.callbackUrl:
        callback_url = body.callbackUrl
    
    # Limpiar cookies de sesión si es necesario
    response.delete_cookie("next-auth.session-token")
    response.delete_cookie("__Secure-next-auth.session-token")
    
    logger.info("Usuario cerró sesión exitosamente")
    
    return SignOutResponse(
        url=callback_url,
        message="Sesión cerrada exitosamente"
    )


@router.post("/validate-token", response_model=TokenValidationResponse)
async def validate_token(
    current_user: Optional[SessionUser] = Depends(get_current_user)
) -> TokenValidationResponse:
    """
    POST /api/auth/validate-token
    
    Valida si un token JWT es válido y retorna información del usuario
    """
    if not current_user:
        return TokenValidationResponse(
            valid=False,
            error="Token inválido o expirado"
        )
    
    return TokenValidationResponse(
        valid=True,
        user_id=current_user.id,
        expires_at=None  # Se puede implementar según necesidad
    )


@router.get("/me", response_model=SessionUser)
async def get_current_user_info(
    current_user: Optional[SessionUser] = Depends(get_current_user)
) -> SessionUser:
    """
    GET /api/auth/me
    
    Obtiene información del usuario autenticado
    """
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="No autenticado"
        )
    
    return current_user 