from fastapi import APIRouter, Depends, HTTPException
from models import Users
from dependencies import init_session, verify_token
from encryption import SECRET_KEY, bcrypt_context, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from schemas import LoginSchemas
from sqlalchemy.orm import Session
from jose import jwt
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordRequestForm



auth_router = APIRouter(prefix="/auth", tags=["auth"])


def create_token(id_user: int, timeout=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    """Cria um token JWT para um usuário.

    Args:
        id_user (int): O ID do usuário.
        timeout (timedelta, optional): O tempo de expiração do token. Defaults to timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES).

    Returns:
        str: O token JWT codificado.
    """

    expiration_date = datetime.now(timezone.utc) + timeout
    info = {"sub": str(id_user), "exp": expiration_date}
    token = jwt.encode(info, SECRET_KEY, ALGORITHM)
    return token


@auth_router.post("/login") # fazer login
async def login(login_schemas:LoginSchemas, session: Session = Depends(init_session)):
    """Realiza o login de um usuário.

    Args:
        credentials (dict): As credenciais de login contendo e-mail e senha.

    Returns:
        dict: A mensagem indicando o status do login e as credenciais fornecidas.
    """

    user = session.query(Users).filter(Users.email == login_schemas.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    elif not bcrypt_context.verify(login_schemas.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid password")
    else:
        access_token = create_token(user.id)
        refresh_token = create_token(user.id, timeout=timedelta(days=7))
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer"
            }


@auth_router.post("/login-form") # fazer login via formulario
async def login_form(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(init_session)):
    """Login a user.

    Args:
        credentials (dict): The login credentials containing username and password.

    Returns:
        dict: A message indicating the login status and the provided credentials.
    """

    user = session.query(Users).filter(Users.email == form_data.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    elif not bcrypt_context.verify(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid password")
    else:
        access_token = create_token(user.id, timeout=timedelta(days=30))
        return {
            "access_token": access_token,
            "token_type": "Bearer"
            }

@auth_router.get("/refresh")
async def refresh_token(user: Users = Depends(verify_token)):
    access_token = create_token(user.id)
    return {"access_token": access_token, "token_type": "Bearer"}
