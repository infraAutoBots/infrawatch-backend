from fastapi import APIRouter, Depends, HTTPException, status
from models import Users
from dependencies import init_session, verify_token
from encryption import SECRET_KEY, bcrypt_context, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from schemas import LoginSchemas, TokenResponse, MessageResponse
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordRequestForm



auth_router = APIRouter(prefix="/auth", tags=["auth"])


def create_token(user_id: int, timeout: timedelta = None) -> str:
    """Cria um token JWT para um usuário.

    Args:
        user_id (int): O ID do usuário.
        timeout (timedelta, optional): O tempo de expiração do token. 
                                     Se None, usa ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        str: O token JWT codificado.
        
    Raises:
        Exception: Se houver erro na criação do token.
    """
    if timeout is None:
        timeout = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    expiration_date = datetime.now(timezone.utc) + timeout
    payload = {
        "sub": str(user_id), 
        "exp": expiration_date,
        "iat": datetime.now(timezone.utc)  # issued at
    }
    
    try:
        token = jwt.encode(payload, SECRET_KEY, ALGORITHM)
        return token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao criar token de acesso"
        ) from e


def _authenticate_user(email: str, password: str, session: Session) -> Users:
    """Autentica um usuário com email e senha.
    
    Args:
        email (str): Email do usuário
        password (str): Senha do usuário
        session (Session): Sessão do banco de dados
        
    Returns:
        Users: Objeto do usuário autenticado
        
    Raises:
        HTTPException: Se as credenciais forem inválidas
    """
    user = session.query(Users).filter(Users.email == email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas"
        )
    
    if not bcrypt_context.verify(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas"
        )
    
    # Verificar se o usuário está ativo
    if not user.state:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário desativado"
        )
    
    return user
@auth_router.post("/login", response_model=TokenResponse)
async def login(login_schemas: LoginSchemas, session: Session = Depends(init_session)):
    """Realiza o login de um usuário.

    Args:
        login_schemas (LoginSchemas): Os dados de login contendo e-mail e senha.
        session (Session): Sessão do banco de dados.

    Returns:
        TokenResponse: Tokens de acesso e refresh com tipo do token.
        
    Raises:
        HTTPException: Se as credenciais forem inválidas ou usuário desativado.
    """
    user = _authenticate_user(login_schemas.email, login_schemas.password, session)
    
    # Atualizar último login
    user.last_login = datetime.now(timezone.utc)
    session.commit()
    
    access_token = create_token(user.id)
    refresh_token = create_token(user.id, timeout=timedelta(days=7))
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60  # em segundos
    )


@auth_router.post("/login-form", response_model=Dict[str, Any])
async def login_form(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(init_session)):
    """Realiza login via formulário OAuth2 (compatível com Swagger UI).

    Args:
        form_data (OAuth2PasswordRequestForm): Dados do formulário com username e password.
        session (Session): Sessão do banco de dados.

    Returns:
        Dict[str, Any]: Token de acesso e tipo do token.
        
    Raises:
        HTTPException: Se as credenciais forem inválidas ou usuário desativado.
    """
    user = _authenticate_user(form_data.username, form_data.password, session)
    
    # Atualizar último login
    user.last_login = datetime.now(timezone.utc)
    session.commit()
    
    access_token = create_token(user.id, timeout=timedelta(days=30))
    
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 30 * 24 * 60 * 60  # 30 dias em segundos
    }

@auth_router.get("/refresh", response_model=Dict[str, Any])
async def refresh_token(user: Users = Depends(verify_token)):
    """Renova o token de acesso usando um token válido.
    
    Args:
        user (Users): Usuário autenticado através do token.
        
    Returns:
        Dict[str, Any]: Novo token de acesso e tipo do token.
    """
    access_token = create_token(user.id)
    
    return {
        "access_token": access_token, 
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@auth_router.post("/logout")
async def logout():
    """Endpoint para logout (implementação futura com blacklist de tokens).
    
    Returns:
        Dict[str, str]: Mensagem de sucesso.
    """
    # TODO: Implementar blacklist de tokens para logout efetivo
    return {"message": "Logout realizado com sucesso"}
