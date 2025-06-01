from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class SessionUser(BaseModel):
    """Usuario de la sesión de NextAuth.js"""
    id: str
    name: Optional[str] = None
    email: Optional[str] = None
    image: Optional[str] = None


class SessionResponse(BaseModel):
    """Respuesta de la sesión de NextAuth.js"""
    user: Optional[SessionUser] = None
    expires: Optional[str] = None
    accessToken: Optional[str] = None


class SignOutRequest(BaseModel):
    """Solicitud de cerrar sesión"""
    redirect: Optional[bool] = True
    callbackUrl: Optional[str] = None


class SignOutResponse(BaseModel):
    """Respuesta de cerrar sesión"""
    url: Optional[str] = None
    message: str = "Sesión cerrada exitosamente"


class TokenValidationResponse(BaseModel):
    """Respuesta de validación de token"""
    valid: bool
    user_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    error: Optional[str] = None 