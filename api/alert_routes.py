from fastapi import APIRouter, Depends, HTTPException, Query
from .dependencies import init_session, verify_token
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from .models import Users, Alerts, AlertLogs
from .schemas import (
    AlertCreateSchema, AlertUpdateSchema, AlertResponseSchema,
    AlertListResponseSchema, AlertFiltersSchema, PaginationSchema,
    AlertStatsSchema, AlertActionSchema, AlertWithLogsSchema,
    AlertSeverityEnum, AlertStatusEnum, AlertCategoryEnum, AlertImpactEnum
)
from typing import List, Optional
from datetime import datetime
import math



# Mapeamentos para normalizar valores em português para inglês
SEVERITY_MAPPING = {
    'critico': 'critical',
    'crítico': 'critical',
    'alto': 'high',
    'medio': 'medium',
    'médio': 'medium',
    'baixo': 'low',
    'critical': 'critical',
    'high': 'high',
    'medium': 'medium',
    'low': 'low'
}

STATUS_MAPPING = {
    'aberto': 'open',
    'em_progresso': 'in_progress',
    'em progresso': 'in_progress',
    'resolvido': 'resolved',
    'fechado': 'closed',
    'open': 'open',
    'in_progress': 'in_progress',
    'resolved': 'resolved',
    'closed': 'closed'
}

IMPACT_MAPPING = {
    'alto': 'high',
    'medio': 'medium',
    'médio': 'medium',
    'baixo': 'low',
    'high': 'high',
    'medium': 'medium',
    'low': 'low'
}

CATEGORY_MAPPING = {
    'rede': 'network',
    'sistema': 'system',
    'aplicacao': 'application',
    'aplicação': 'application',
    'seguranca': 'security',
    'segurança': 'security',
    'network': 'network',
    'system': 'system',
    'application': 'application',
    'security': 'security'
}


def _normalize_filter_values(values: Optional[List[str]], mapping: dict) -> Optional[List[str]]:
    """
    Normaliza valores de filtro usando mapeamento fornecido.
    Remove valores inválidos e converte português para inglês.
    """
    if not values:
        return None
    
    normalized = []
    for value in values:
        if value and value.lower() in mapping:
            normalized_value = mapping[value.lower()]
            if normalized_value not in normalized:
                normalized.append(normalized_value)
    
    return normalized if normalized else None


def _safe_build_filters(
    search: Optional[str],
    severity: Optional[List[str]],
    status: Optional[List[str]],
    category: Optional[List[str]],
    impact: Optional[List[str]],
    assignee: Optional[str],
    system: Optional[str],
    date_from: Optional[datetime],
    date_to: Optional[datetime]
) -> AlertFiltersSchema:
    """
    Constrói filtros de forma segura, normalizando valores e tratando erros.
    """
    try:
        # Normalizar valores usando mapeamentos
        normalized_severity = _normalize_filter_values(severity, SEVERITY_MAPPING)
        normalized_status = _normalize_filter_values(status, STATUS_MAPPING)
        normalized_category = _normalize_filter_values(category, CATEGORY_MAPPING)
        normalized_impact = _normalize_filter_values(impact, IMPACT_MAPPING)
        
        # Converter para enums
        severity_enums = None
        if normalized_severity:
            severity_enums = []
            for sev in normalized_severity:
                try:
                    severity_enums.append(AlertSeverityEnum(sev))
                except ValueError:
                    continue  # Ignorar valores inválidos
        
        status_enums = None
        if normalized_status:
            status_enums = []
            for stat in normalized_status:
                try:
                    status_enums.append(AlertStatusEnum(stat))
                except ValueError:
                    continue
        
        category_enums = None
        if normalized_category:
            category_enums = []
            for cat in normalized_category:
                try:
                    category_enums.append(AlertCategoryEnum(cat))
                except ValueError:
                    continue
        
        impact_enums = None
        if normalized_impact:
            impact_enums = []
            for imp in normalized_impact:
                try:
                    impact_enums.append(AlertImpactEnum(imp))
                except ValueError:
                    continue
        
        return AlertFiltersSchema(
            search=search,
            severity=severity_enums,
            status=status_enums,
            category=category_enums,
            impact=impact_enums,
            assignee=assignee,
            system=system,
            date_from=date_from,
            date_to=date_to
        )
    
    except Exception as e:
        # Em caso de erro, retornar filtros básicos
        return AlertFiltersSchema(
            search=search,
            assignee=assignee,
            system=system,
            date_from=date_from,
            date_to=date_to
        )


alert_router = APIRouter(prefix="/alerts", tags=["alerts"], dependencies=[Depends(verify_token)])


def _check_admin_or_monitor(user: Users):
    """Verifica se o usuário tem permissão de ADMIN ou MONITOR"""
    if user.access_level not in ["ADMIN", "MONITOR"]:
        raise HTTPException(status_code=403, detail="Operação não permitida: requer nível ADMIN ou MONITOR")


def _build_alert_filters(filters: AlertFiltersSchema, query):
    """Constrói filtros dinâmicos para consultas de alertas"""
    if filters.search:
        search_term = f"%{filters.search.lower()}%"
        query = query.filter(
            or_(
                Alerts.title.ilike(search_term),
                Alerts.description.ilike(search_term),
                Alerts.system.ilike(search_term),
                Alerts.assignee.ilike(search_term)
            )
        )
    
    if filters.severity:
        query = query.filter(Alerts.severity.in_([s.value for s in filters.severity]))
    
    if filters.status:
        query = query.filter(Alerts.status.in_([s.value for s in filters.status]))
    
    if filters.category:
        query = query.filter(Alerts.category.in_([c.value for c in filters.category]))
    
    if filters.impact:
        query = query.filter(Alerts.impact.in_([i.value for i in filters.impact]))
    
    if filters.assignee:
        query = query.filter(Alerts.assignee.ilike(f"%{filters.assignee}%"))
    
    if filters.system:
        query = query.filter(Alerts.system.ilike(f"%{filters.system}%"))
    
    if filters.date_from:
        query = query.filter(Alerts.created_at >= filters.date_from)
    
    if filters.date_to:
        query = query.filter(Alerts.created_at <= filters.date_to)
    
    return query


@alert_router.post("/", response_model=AlertResponseSchema)
async def create_alert(
    alert_data: AlertCreateSchema,
    logged_user: Users = Depends(verify_token),
    session: Session = Depends(init_session)
):
    """
    Cria um novo alerta no sistema.
    Requer permissão de ADMIN ou MONITOR.
    """
    _check_admin_or_monitor(logged_user)

    new_alert = Alerts(
        title=alert_data.title,
        description=alert_data.description,
        severity=alert_data.severity.value,
        category=alert_data.category.value,
        system=alert_data.system,
        impact=alert_data.impact.value,
        id_endpoint=alert_data.id_endpoint,
        id_user_created=logged_user.id,
        assignee=alert_data.assignee
    )
    
    session.add(new_alert)
    session.commit()
    session.refresh(new_alert)
    
    # Log da criação
    log_entry = AlertLogs(
        id_alert=new_alert.id,
        id_user=logged_user.id,
        action="created",
        comment=f"Alerta criado: {alert_data.title}"
    )
    session.add(log_entry)
    session.commit()
    
    return AlertResponseSchema.model_validate(new_alert)


@alert_router.get("/", response_model=AlertListResponseSchema)
async def list_alerts(
    page: int = Query(1, ge=1, description="Número da página"),
    size: int = Query(10, ge=1, le=100, description="Tamanho da página"),
    search: Optional[str] = Query(None, description="Termo de busca"),
    severity: Optional[List[str]] = Query(None, description="Filtro por severidade"),
    status: Optional[List[str]] = Query(None, description="Filtro por status"),
    category: Optional[List[str]] = Query(None, description="Filtro por categoria"),
    impact: Optional[List[str]] = Query(None, description="Filtro por impacto"),
    assignee: Optional[str] = Query(None, description="Filtro por responsável"),
    system: Optional[str] = Query(None, description="Filtro por sistema"),
    date_from: Optional[datetime] = Query(None, description="Data inicial"),
    date_to: Optional[datetime] = Query(None, description="Data final"),
    sort_by: str = Query("created_at", description="Campo para ordenação"),
    sort_order: str = Query("desc", description="Ordem: asc ou desc"),
    logged_user: Users = Depends(verify_token),
    session: Session = Depends(init_session)
):
    """
    Lista alertas com suporte a paginação e filtros avançados.
    Suporta valores em português e inglês, ignorando valores inválidos.
    """
    # Construir filtros de forma segura
    filters = _safe_build_filters(
        search=search,
        severity=severity,
        status=status,
        category=category,
        impact=impact,
        assignee=assignee,
        system=system,
        date_from=date_from,
        date_to=date_to
    )
    
    # Query base
    query = session.query(Alerts).options(
        joinedload(Alerts.endpoint),
        joinedload(Alerts.user_created),
        joinedload(Alerts.user_assigned)
    )
    
    # Aplicar filtros
    query = _build_alert_filters(filters, query)
    
    # Ordenação
    order_column = getattr(Alerts, sort_by, Alerts.created_at)
    if sort_order.lower() == "desc":
        query = query.order_by(desc(order_column))
    else:
        query = query.order_by(order_column)
    
    # Paginação
    total = query.count()
    offset = (page - 1) * size
    alerts = query.offset(offset).limit(size).all()
    
    # Converter para schemas de resposta com tratamento seguro para valores inválidos
    alert_responses = []
    
    # Valores válidos para cada campo
    valid_impacts = ["high", "medium", "low"]
    valid_severities = ["critical", "high", "medium", "low"]
    valid_categories = ["infrastructure", "security", "application", "performance", "monitoring"]
    valid_statuses = ["active", "acknowledged", "resolved"]
    
    for alert in alerts:
        try:
            # Tenta converter diretamente, mas captura erros de validação
            alert_response = AlertResponseSchema.model_validate(alert)
            alert_responses.append(alert_response)
        except Exception as e:
            # Se falhar a validação, cria um dicionário com valores seguros
            try:
                # Define valores padrão
                default_impact = "medium"
                default_severity = "medium"
                default_category = "infrastructure" 
                default_status = "active"
                
                # Cria um dicionário com valores seguros
                alert_dict = {
                    "id": alert.id,
                    "title": alert.title or "Sem título",
                    "description": alert.description or "Sem descrição",
                    "severity": alert.severity if hasattr(alert, "severity") and alert.severity in valid_severities else default_severity,
                    "category": alert.category if hasattr(alert, "category") and alert.category in valid_categories else default_category,
                    "system": alert.system or "Desconhecido",
                    "impact": alert.impact if hasattr(alert, "impact") and alert.impact in valid_impacts else default_impact,
                    "status": alert.status if hasattr(alert, "status") and alert.status in valid_statuses else default_status,
                    "assignee": alert.assignee,
                    "id_endpoint": alert.id_endpoint,
                    "created_at": alert.created_at,
                    "updated_at": alert.updated_at,
                    "acknowledged_at": alert.acknowledged_at,
                    "resolved_at": alert.resolved_at,
                    "duration": alert.duration
                }
                
                # Tenta validar com os valores corrigidos
                alert_response = AlertResponseSchema.model_validate(alert_dict)
                alert_responses.append(alert_response)
            except Exception as e2:
                print(f"Erro ao validar alerta ID {alert.id}: {e2}")
                continue
    
    # Calcular informações de paginação
    pages = math.ceil(total / size)
    pagination = PaginationSchema(
        page=page,
        size=size,
        total=total,
        pages=pages
    )

    return AlertListResponseSchema(
        data=alert_responses,
        pagination=pagination,
        filters_applied=filters
    )


@alert_router.get("/stats", response_model=AlertStatsSchema)
async def get_alert_stats(
    logged_user: Users = Depends(verify_token),
    session: Session = Depends(init_session)
):
    """
    Retorna estatísticas dos alertas para o dashboard.
    """
    # Estatísticas básicas
    total_alerts = session.query(Alerts).count()
    critical_active = session.query(Alerts).filter(
        and_(Alerts.severity == "critical", Alerts.status == "active")
    ).count()
    
    high_active = session.query(Alerts).filter(
        and_(Alerts.severity == "high", Alerts.status == "active")
    ).count()
    
    medium_active = session.query(Alerts).filter(
        and_(Alerts.severity == "medium", Alerts.status == "active")
    ).count()
    
    low_active = session.query(Alerts).filter(
        and_(Alerts.severity == "low", Alerts.status == "active")
    ).count()
    
    acknowledged = session.query(Alerts).filter(Alerts.status == "acknowledged").count()
    
    # Resolvidos hoje
    today = datetime.now().date()
    resolved_today = session.query(Alerts).filter(
        and_(
            Alerts.status == "resolved",
            func.date(Alerts.resolved_at) == today
        )
    ).count()
    
    # MTTR (Mean Time To Resolution) - tempo médio de resolução em horas
    resolved_alerts = session.query(Alerts).filter(
        and_(Alerts.status == "resolved", Alerts.resolved_at.isnot(None))
    ).all()
    
    if resolved_alerts:
        total_resolution_time = sum([
            (alert.resolved_at - alert.created_at).total_seconds() / 3600
            for alert in resolved_alerts
        ])
        avg_resolution_hours = total_resolution_time / len(resolved_alerts)
        mttr = f"{avg_resolution_hours:.1f}h"
    else:
        mttr = "N/A"
    
    # Estatísticas por categoria
    category_stats = session.query(
        Alerts.category,
        func.count(Alerts.id).label('count')
    ).group_by(Alerts.category).all()

    by_category = {stat.category: stat.count for stat in category_stats}

    # Estatísticas por sistema (top 10)
    system_stats = session.query(
        Alerts.system,
        func.count(Alerts.id).label('count')
    ).group_by(Alerts.system).order_by(desc('count')).limit(10).all()
    
    by_system = {stat.system: stat.count for stat in system_stats}
    
    return AlertStatsSchema(
        total_alerts=total_alerts,
        critical_active=critical_active,
        high_active=high_active,
        medium_active=medium_active,
        low_active=low_active,
        acknowledged=acknowledged,
        resolved_today=resolved_today,
        average_resolution_time=mttr,
        by_category=by_category,
        by_system=by_system
    )


@alert_router.get("/{alert_id}", response_model=AlertWithLogsSchema)
async def get_alert_details(
    alert_id: int,
    logged_user: Users = Depends(verify_token),
    session: Session = Depends(init_session)
):
    """
    Retorna detalhes de um alerta específico com histórico de logs.
    """
    alert = session.query(Alerts).options(
        joinedload(Alerts.alert_logs).joinedload(AlertLogs.user),
        joinedload(Alerts.endpoint),
        joinedload(Alerts.user_created),
        joinedload(Alerts.user_assigned)
    ).filter(Alerts.id == alert_id).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    
    return AlertWithLogsSchema.model_validate(alert)


@alert_router.put("/{alert_id}", response_model=AlertResponseSchema)
async def update_alert(
    alert_id: int,
    alert_data: AlertUpdateSchema,
    logged_user: Users = Depends(verify_token),
    session: Session = Depends(init_session)
):
    """
    Atualiza um alerta existente.
    Requer permissão de ADMIN ou MONITOR.
    """
    _check_admin_or_monitor(logged_user)
    
    alert = session.query(Alerts).filter(Alerts.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    
    # Atualizar campos
    update_data = alert_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(alert, field):
            if hasattr(value, 'value'):  # Para enums
                setattr(alert, field, value.value)
            else:
                setattr(alert, field, value)
    
    alert.updated_at = datetime.now()
    session.commit()
    session.refresh(alert)
    
    # Log da atualização
    log_entry = AlertLogs(
        id_alert=alert.id,
        id_user=logged_user.id,
        action="updated",
        comment=f"Alerta atualizado por {logged_user.name}"
    )
    session.add(log_entry)
    session.commit()
    
    return AlertResponseSchema.model_validate(alert)


@alert_router.post("/{alert_id}/actions")
async def alert_action(
    alert_id: int,
    action_data: AlertActionSchema,
    logged_user: Users = Depends(verify_token),
    session: Session = Depends(init_session)
):
    """
    Executa ações em um alerta (acknowledge, resolve, assign).
    """
    _check_admin_or_monitor(logged_user)
    
    alert = session.query(Alerts).filter(Alerts.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    
    if action_data.action == "acknowledge":
        alert.status = "acknowledged"
        alert.acknowledged_at = datetime.now()
        action_comment = f"Alerta reconhecido por {logged_user.name}"
        
    elif action_data.action == "resolve":
        alert.status = "resolved"
        alert.resolved_at = datetime.now()
        action_comment = f"Alerta resolvido por {logged_user.name}"
        
    elif action_data.action == "assign":
        if not action_data.assignee:
            raise HTTPException(status_code=400, detail="Responsável deve ser informado para atribuição")
        alert.assignee = action_data.assignee
        action_comment = f"Alerta atribuído para {action_data.assignee} por {logged_user.name}"
        
    else:
        raise HTTPException(status_code=400, detail="Ação inválida")
    
    alert.updated_at = datetime.now()
    session.commit()
    
    # Log da ação
    log_entry = AlertLogs(
        id_alert=alert.id,
        id_user=logged_user.id,
        action=action_data.action,
        comment=action_data.comment or action_comment
    )
    session.add(log_entry)
    session.commit()
    
    return {"success": True, "message": f"Ação '{action_data.action}' executada com sucesso"}


@alert_router.delete("/{alert_id}")
async def delete_alert(
    alert_id: int,
    logged_user: Users = Depends(verify_token),
    session: Session = Depends(init_session)
):
    """
    Remove um alerta do sistema.
    Requer permissão de ADMIN.
    """
    if logged_user.access_level != "ADMIN":
        raise HTTPException(status_code=403, detail="Operação não permitida: requer nível ADMIN")
    
    alert = session.query(Alerts).filter(Alerts.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    
    session.delete(alert)
    session.commit()
    
    return {"success": True, "message": "Alerta removido com sucesso"}


@alert_router.post("/bulk-actions")
async def bulk_alert_actions(
    alert_ids: List[int],
    action_data: AlertActionSchema,
    logged_user: Users = Depends(verify_token),
    session: Session = Depends(init_session)
):
    """
    Executa ações em lote em múltiplos alertas.
    """
    _check_admin_or_monitor(logged_user)
    
    alerts = session.query(Alerts).filter(Alerts.id.in_(alert_ids)).all()
    if not alerts:
        raise HTTPException(status_code=404, detail="Nenhum alerta encontrado")
    
    updated_count = 0
    for alert in alerts:
        if action_data.action == "acknowledge" and alert.status == "active":
            alert.status = "acknowledged"
            alert.acknowledged_at = datetime.now()
            updated_count += 1
            
        elif action_data.action == "resolve" and alert.status != "resolved":
            alert.status = "resolved"
            alert.resolved_at = datetime.now()
            updated_count += 1
            
        elif action_data.action == "assign":
            alert.assignee = action_data.assignee
            updated_count += 1
        
        alert.updated_at = datetime.now()
        
        # Log da ação
        log_entry = AlertLogs(
            id_alert=alert.id,
            id_user=logged_user.id,
            action=f"bulk_{action_data.action}",
            comment=action_data.comment or f"Ação em lote executada por {logged_user.name}"
        )
        session.add(log_entry)
    
    session.commit()
    
    return {
        "success": True, 
        "message": f"Ação executada em {updated_count} alertas",
        "updated_count": updated_count
    }

