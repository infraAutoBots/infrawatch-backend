from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import jwt
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional
from models import Users
from dependencies import init_session, verify_token
from encryption import SECRET_KEY, bcrypt_context, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from schemas import LoginSchemas



auth_router = APIRouter(prefix="/auth", tags=["auth"])


def create_token(id_user: int, timeout: Optional[timedelta] = None, token_type: str = "access") -> str:
    """
    Cria um token JWT para um usuário.
    Args:
        id_user (int): O ID do usuário.
        timeout (timedelta, optional): O tempo de expiração do token.
        token_type (str): Tipo do token ("access" ou "refresh").
    Returns:
        str: O token JWT codificado.
    """
    if timeout is None:
        timeout = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expiration_date = datetime.now(timezone.utc) + timeout
    exp_timestamp = expiration_date.timestamp()
    info = {"sub": str(id_user), "exp": exp_timestamp, "type": token_type}
    token = jwt.encode(info, SECRET_KEY, ALGORITHM)
    return token



def _authenticate_user(email: str, password: str, session: Session) -> Optional[Users]:
    user = session.query(Users).filter(Users.email == email).first()
    if user and bcrypt_context.verify(password, user.password):
        return user
    return None

@auth_router.post("/login", status_code=status.HTTP_200_OK)
async def login(login_schemas: LoginSchemas, session: Session = Depends(init_session)):
    """
    Realiza o login de um usuário via JSON.
    """
    user = _authenticate_user(login_schemas.email, login_schemas.password, session)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    access_token = create_token(user.id, token_type="access")
    refresh_token = create_token(user.id, timeout=timedelta(days=7), token_type="refresh")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer"
    }

@auth_router.post("/login-form", status_code=status.HTTP_200_OK)
async def login_form(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(init_session)):
    """
    Realiza o login de um usuário via formulário.
    """
    user = _authenticate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    access_token = create_token(user.id, timeout=timedelta(days=30), token_type="access")
    return {
        "access_token": access_token,
        "token_type": "Bearer"
    }

@auth_router.get("/refresh", status_code=status.HTTP_200_OK)
async def refresh_token(user: Users = Depends(verify_token)):
    """
    Gera um novo access token para o usuário autenticado.
    """
    access_token = create_token(user.id, token_type="access")
    return {"access_token": access_token, "token_type": "Bearer"}
