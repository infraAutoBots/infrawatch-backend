from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from math import ceil
from datetime import datetime

from .models import Users
from .dependencies import init_session, verify_token
from .encryption import bcrypt_context
from .schemas import (
    UserResponseSchemas, 
    UserCreateSchemas, 
    UserUpdateSchemas, 
    UserStatusUpdateSchemas,
    UserStatsSchemas,
    UserListResponse
)


users_router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(verify_token)])


def get_user_stats(session: Session) -> UserStatsSchemas:
    """Calcula as estatísticas dos usuários."""
    total_users = session.query(Users).count()
    admins = session.query(Users).filter(Users.access_level == "ADMIN").count()
    monitors = session.query(Users).filter(Users.access_level == "MONITOR").count()
    viewers = session.query(Users).filter(Users.access_level == "VIEWER").count()
    active_users = session.query(Users).filter(Users.state == True).count()
    inactive_users = session.query(Users).filter(Users.state == False).count()
    
    return UserStatsSchemas(
        total_users=total_users,
        admins=admins,
        monitors=monitors,
        viewers=viewers,
        active_users=active_users,
        inactive_users=inactive_users
    )


def check_admin_permission(user: Users):
    """Verifica se o usuário tem permissão de administrador."""
    if user.access_level != "ADMIN":
        raise HTTPException(status_code=403, detail="Operation not permitted. Admin access required.")


@users_router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1, description="Página"),
    limit: int = Query(10, ge=1, le=100, description="Limite de itens por página"),
    search: Optional[str] = Query(None, description="Buscar por nome ou email"),
    status: Optional[str] = Query(None, description="Filtrar por status: active, inactive"),
    access_level: Optional[str] = Query(None, description="Filtrar por nível de acesso: ADMIN, MONITOR, VIEWER"),
    current_user: Users = Depends(verify_token),
    session: Session = Depends(init_session)
):
    """
    Lista todos os usuários com paginação e filtros.
    
    Permissões:
    - ADMIN: Visualiza todos os usuários
    - MONITOR/VIEWER: Visualiza usuários limitados (apenas ativos)
    """
    
    # Query base
    query = session.query(Users)
    
    # Aplicar filtros baseados no nível de acesso do usuário logado
    if current_user.access_level != "ADMIN":
        # Usuários não-admin só veem usuários ativos
        query = query.filter(Users.state == True)
    
    # Filtro por busca (nome ou email)
    if search:
        query = query.filter(
            or_(
                Users.name.ilike(f"%{search}%"),
                Users.email.ilike(f"%{search}%")
            )
        )
    
    # Filtro por status
    if status:
        if status == "active":
            query = query.filter(Users.state == True)
        elif status == "inactive":
            query = query.filter(Users.state == False)
    
    # Filtro por nível de acesso
    if access_level:
        valid_levels = ["ADMIN", "MONITOR", "VIEWER"]
        if access_level in valid_levels:
            query = query.filter(Users.access_level == access_level)
        else:
            raise HTTPException(status_code=400, detail="Invalid access level")
    
    # Contar total de registros
    total = query.count()
    
    # Calcular número de páginas
    pages = ceil(total / limit) if total > 0 else 1
    
    # Aplicar paginação
    offset = (page - 1) * limit
    users = query.offset(offset).limit(limit).all()
    
    # Obter estatísticas
    stats = get_user_stats(session)
    
    return UserListResponse(
        users=[UserResponseSchemas.model_validate(user) for user in users],
        total=total,
        page=page,
        pages=pages,
        stats=stats
    )


@users_router.post("", response_model=dict, status_code=201)
async def create_user(
    user_data: UserCreateSchemas,
    current_user: Users = Depends(verify_token),
    session: Session = Depends(init_session)
):
    """
    Cria um novo usuário.
    
    Permissões: Apenas ADMIN
    """
    
    # Verificar permissão de admin
    check_admin_permission(current_user)
    
    # Validar nível de acesso
    valid_levels = ["ADMIN", "MONITOR", "VIEWER"]
    if user_data.access_level not in valid_levels:
        raise HTTPException(status_code=400, detail="Invalid access level")
    
    # Verificar se email já existe
    existing_user = session.query(Users).filter(Users.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Criptografar senha
    hashed_password = bcrypt_context.hash(user_data.password)
    
    # Criar novo usuário
    new_user = Users(
        name=user_data.name,
        email=user_data.email,
        password=hashed_password,
        state=user_data.state,
        last_login=None,
        access_level=user_data.access_level,
        url=user_data.url
    )
    
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    return {
        "message": "Usuário criado com sucesso",
        "user": UserResponseSchemas.model_validate(new_user)
    }


@users_router.get("/{user_id}", response_model=UserResponseSchemas)
async def get_user(
    user_id: int,
    current_user: Users = Depends(verify_token),
    session: Session = Depends(init_session)
):
    """
    Obtém um usuário específico pelo ID.
    
    Permissões:
    - ADMIN: Pode ver qualquer usuário
    - MONITOR/VIEWER: Só pode ver o próprio perfil
    """
    
    # Verificar se o usuário existe
    user = session.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verificar permissões
    if current_user.access_level != "ADMIN" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    return UserResponseSchemas.model_validate(user)


@users_router.put("/{user_id}", response_model=dict)
async def update_user(
    user_id: int,
    user_data: UserUpdateSchemas,
    current_user: Users = Depends(verify_token),
    session: Session = Depends(init_session)
):
    """
    Atualiza um usuário existente.
    
    Permissões:
    - ADMIN: Pode editar qualquer usuário
    - MONITOR/VIEWER: Só pode editar o próprio perfil (sem alterar access_level)
    """
    
    # Verificar se o usuário existe
    user = session.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verificar permissões
    is_admin = current_user.access_level == "ADMIN"
    is_self_edit = current_user.id == user_id
    
    if not is_admin and not is_self_edit:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Se não é admin e está tentando alterar access_level
    if not is_admin and user_data.access_level is not None:
        raise HTTPException(status_code=403, detail="Cannot change access level")
    
    # Validar nível de acesso se fornecido
    if user_data.access_level is not None:
        valid_levels = ["ADMIN", "MONITOR", "VIEWER"]
        if user_data.access_level not in valid_levels:
            raise HTTPException(status_code=400, detail="Invalid access level")
    
    # Verificar email único se alterado
    if user_data.email is not None and user_data.email != user.email:
        existing_user = session.query(Users).filter(Users.email == user_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    # Atualizar campos fornecidos
    update_data = user_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if field == "password" and value is not None:
            # Criptografar nova senha
            setattr(user, field, bcrypt_context.hash(value))
        else:
            setattr(user, field, value)
    
    session.commit()
    session.refresh(user)
    
    return {
        "message": "Usuário atualizado com sucesso",
        "user": UserResponseSchemas.model_validate(user)
    }


@users_router.delete("/{user_id}", response_model=dict)
async def delete_user(
    user_id: int,
    current_user: Users = Depends(verify_token),
    session: Session = Depends(init_session)
):
    """
    Exclui um usuário.
    
    Permissões: Apenas ADMIN
    """
    
    # Verificar permissão de admin
    check_admin_permission(current_user)
    
    # Verificar se o usuário existe
    user = session.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Impedir autoexclusão
    if current_user.id == user_id:
        raise HTTPException(status_code=409, detail="Cannot delete your own account")
    
    # Verificar se não é o último admin
    if user.access_level == "ADMIN":
        admin_count = session.query(Users).filter(Users.access_level == "ADMIN").count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=409, 
                detail="Cannot delete the last administrator"
            )
    
    session.delete(user)
    session.commit()
    
    return {"message": "Usuário excluído com sucesso"}


@users_router.patch("/{user_id}/status", response_model=dict)
async def update_user_status(
    user_id: int,
    status_data: UserStatusUpdateSchemas,
    current_user: Users = Depends(verify_token),
    session: Session = Depends(init_session)
):
    """
    Altera o status (ativo/inativo) de um usuário.
    
    Permissões: Apenas ADMIN
    """
    
    # Verificar permissão de admin
    check_admin_permission(current_user)
    
    # Verificar se o usuário existe
    user = session.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Impedir desativar o próprio usuário
    if current_user.id == user_id and not status_data.state:
        raise HTTPException(status_code=409, detail="Cannot deactivate your own account")
    
    # Verificar se não é o último admin ativo
    if (user.access_level == "ADMIN" and user.state and not status_data.state):
        active_admin_count = session.query(Users).filter(
            Users.access_level == "ADMIN",
            Users.state == True
        ).count()
        if active_admin_count <= 1:
            raise HTTPException(
                status_code=409, 
                detail="Cannot deactivate the last active administrator"
            )
    
    user.state = status_data.state
    session.commit()
    session.refresh(user)
    
    return {
        "message": "Status do usuário atualizado com sucesso",
        "user": {
            "id": user.id,
            "state": user.state,
            "updated_at": datetime.now()
        }
    }


@users_router.get("/stats/summary", response_model=UserStatsSchemas)
async def get_users_stats(
    current_user: Users = Depends(verify_token),
    session: Session = Depends(init_session)
):
    """
    Obtém estatísticas dos usuários.
    
    Permissões: Todos os usuários logados
    """
    
    return get_user_stats(session)
