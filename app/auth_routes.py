from fastapi import APIRouter, Depends, HTTPException
from models import Users
from dependencies import init_session, verify_token
from encryption import SECRET_KEY, bcrypt_context, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from schemas import UserSchemas, LoginSchemas
from sqlalchemy.orm import Session
from jose import jwt
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordRequestForm



auth_router = APIRouter(prefix="/auth", tags=["auth"])


def create_token(id_user: int, timeout=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    """_summary_

    Args:
        id_user (int): _description_
        timeout (_type_, optional): _description_. Defaults to timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES).

    Returns:
        _type_: _description_
    """

    expiration_date = datetime.now(timezone.utc) + timeout
    info = {"sub": str(id_user), "exp": expiration_date}
    token = jwt.encode(info, SECRET_KEY, ALGORITHM)
    return token


@auth_router.post("/login") # fazer login
async def login(login_schemas:LoginSchemas, session: Session = Depends(init_session)):
    """Login a user.

    Args:
        credentials (dict): The login credentials containing username and password.

    Returns:
        dict: A message indicating the login status and the provided credentials.
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


@auth_router.post("/signup") # criar conta, add para criar conta tem que ser admin
async def signup(user_schemas: UserSchemas, session: Session = Depends(init_session)):
    """_summary_

    Args:
        user_schemas (UserSchemas): _description_
        session (Session, optional): _description_. Defaults to Depends(init_session).

    Raises:
        HTTPException: _description_
        HTTPException: _description_

    Returns:
        _type_: _description_
    """

    user = session.query(Users).filter(Users.email == user_schemas.email).first()
    if user_schemas.access_level not in ['ADMIN', 'MONITOR', 'VIEWER']:
        raise HTTPException(status_code=400, detail="Invalid access level")
    elif user:
        raise HTTPException(status_code=400, detail="Email already registered")
    elif user.access_level != 'ADMIN':
        raise HTTPException(status_code=401, detail="Access denied")
    else:
        encrypted_password = bcrypt_context.hash(user_schemas.password)
        new_user = Users(user_schemas.name, user_schemas.email,
                         encrypted_password, user_schemas.state,
                         user_schemas.last_login, user_schemas.access_level)
        session.add(new_user)
        session.commit()
        return {"msg" : f"user {new_user.name} add"}


@auth_router.get("/refresh")
async def refresh_token(user: Users = Depends(verify_token)):
    access_token = create_token(user.id)
    return {"access_token": access_token, "token_type": "Bearer"}
