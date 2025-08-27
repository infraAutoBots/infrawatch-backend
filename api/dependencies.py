from models import db, Users
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import sessionmaker, Session
from jose import jwt, JWTError
from encryption import SECRET_KEY, ALGORITHM, oauth2_schema
from typing import Generator
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def init_session() -> Generator[Session, None, None]:
    """Inicializa e gerencia uma sessão do banco de dados.

    Yields:
        Session: Instância da sessão do banco de dados.
        
    Note:
        Garante que a sessão seja fechada mesmo em caso de erro.
    """
    SessionLocal = sessionmaker(bind=db, autocommit=False, autoflush=False)
    session = SessionLocal()
    
    try:
        yield session
    except Exception as e:
        logger.error(f"Erro na sessão do banco de dados: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()


def verify_token(token: str = Depends(oauth2_schema), session: Session = Depends(init_session)) -> Users:
    """Verifica e valida um token JWT.

    Args:
        token (str): Token JWT a ser verificado.
        session (Session): Sessão do banco de dados.

    Returns:
        Users: Objeto do usuário autenticado.

    Raises:
        HTTPException: Se o token for inválido, expirado ou o usuário não existir.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            logger.warning("Token sem subject (sub)")
            raise credentials_exception
            
    except JWTError as e:
        logger.warning(f"Erro ao decodificar JWT: {str(e)}")
        raise credentials_exception
    
    # Buscar usuário no banco de dados
    user = session.query(Users).filter(Users.id == int(user_id)).first()
    
    if user is None:
        logger.warning(f"Usuário com ID {user_id} não encontrado")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Usuário não encontrado"
        )
    
    # Verificar se o usuário está ativo
    if not user.state:
        logger.warning(f"Usuário {user.email} está desativado")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário desativado"
        )
    
    return user


def verify_admin_access(current_user: Users = Depends(verify_token)) -> Users:
    """Verifica se o usuário atual tem acesso de administrador.
    
    Args:
        current_user (Users): Usuário autenticado.
        
    Returns:
        Users: Usuário com acesso de administrador confirmado.
        
    Raises:
        HTTPException: Se o usuário não tiver permissões de administrador.
    """
    if current_user.access_level != "ADMIN":
        logger.warning(f"Usuário {current_user.email} tentou acessar recurso de admin")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissões de administrador necessárias"
        )
    
    return current_user


def get_current_active_user(current_user: Users = Depends(verify_token)) -> Users:
    """Alias para verify_token para melhor semântica.
    
    Args:
        current_user (Users): Usuário autenticado através do token.
        
    Returns:
        Users: Usuário ativo autenticado.
    """
    return current_user
