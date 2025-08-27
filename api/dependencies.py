from fastapi import Depends, HTTPException
from sqlalchemy.orm import sessionmaker, Session
from jose import jwt, JWTError
from typing import Generator
from models import db, Users
from encryption import SECRET_KEY, ALGORITHM, oauth2_schema



def init_session() -> Generator[Session, None, None]:
    """
    Inicializa uma sessão do banco de dados e garante seu fechamento.
    Yields:
        Session: Sessão do SQLAlchemy.
    """
    SessionLocal = sessionmaker(bind=db)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def verify_token(token: str = Depends(oauth2_schema), session: Session = Depends(init_session)) -> Users:
    """
    Valida o token JWT e retorna o usuário correspondente.
    Args:
        token (str): Token JWT.
        session (Session): Sessão do SQLAlchemy.
    Raises:
        HTTPException: Se o token for inválido ou o usuário não existir.
    Returns:
        Users: Usuário autenticado.
    """
    try:
        info = jwt.decode(token, SECRET_KEY, ALGORITHM)
        id_user = info.get('sub')
        exp = info.get('exp')
        if not id_user:
            raise HTTPException(status_code=401, detail="Token inválido: sub ausente")
        if exp is not None:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc).timestamp()
            if now > float(exp):
                raise HTTPException(status_code=401, detail="Token expirado. Faça login novamente.")
    except JWTError:
        raise HTTPException(status_code=401, detail="Acesso negado: token inválido")
    user = session.query(Users).filter(Users.id == id_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user
