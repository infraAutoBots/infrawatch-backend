from models import db
from models import Users
from fastapi import Depends, HTTPException
from sqlalchemy.orm import sessionmaker, Session
from jose import jwt, JWTError
from encryption import SECRET_KEY, ALGORITHM, oauth2_schema



def init_session():
    try:
        Session = sessionmaker(bind=db)
        session = Session()
        yield session
    finally:
        session.close()


def verify_token(token: str = Depends(oauth2_schema), session: Session =  Depends(init_session)):

    try:
        info = jwt.decode(token, SECRET_KEY, ALGORITHM)
        id_user = info.get('sub')
    except JWTError:
        raise HTTPException(status_code=401, detail="Access denied")
    user = session.query(Users).filter(Users.id == id_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
