from fastapi import APIRouter, Depends, HTTPException
from models import Users
from dependencies import init_session
from encryption import bcrypt_context
from schemas import UserSchemas
from sqlalchemy.orm import Session
auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/signin") # entrar login
async def signin():
    """Login a user.

    Args:
        credentials (dict): The login credentials containing username and password.

    Returns:
        dict: A message indicating the login status and the provided credentials.
    """
    return {"message": "Login successful", "credentials": "credentials"}


# criar conta, add para criar conta tem que ser admin
@auth_router.post("/signup")
async def signup(user_schemas: UserSchemas, session: Session = Depends(init_session)):
    user = session.query(Users).filter(Users.email == user_schemas.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    else:
        encrypted_password = bcrypt_context.hash(user_schemas.password)
        new_user = Users(user_schemas.name, user_schemas.email,
                         encrypted_password, user_schemas.state,
                         user_schemas.last_login, user_schemas.access_level)
        session.add(new_user)
        session.commit()
        return {"msg" : "user add"}