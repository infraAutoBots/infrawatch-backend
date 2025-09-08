from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import datetime

from models import Users, WebHookConfig, EmailConfig, FailureThresholdConfig, PerformanceThresholds
from dependencies import init_session, verify_token
from encryption import bcrypt_context
from schemas import (
    WebHookConfigSchema,
    WebHookConfigResponse,
    WebHookConfigUpdate,
    EmailConfigSchema,
    EmailConfigResponse,
    EmailConfigUpdate,
    FailureThresholdConfigSchema,
    FailureThresholdConfigResponse,
    FailureThresholdConfigUpdate,
    PerformanceThresholdsSchemas,
    PerformanceThresholdsResponse,
    PerformanceThresholdsUpdate
)



config_router = APIRouter(prefix="/config", tags=["config"], dependencies=[Depends(verify_token)])


def check_admin_permission(user: Users):
    """Verifica se o usuário tem permissão de administrador."""
    if user.access_level != "ADMIN":
        raise HTTPException(status_code=403, detail="Operation not permitted. Admin access required.")


# =============================================================================
# ROTAS DE WEBHOOK
# =============================================================================

@config_router.post("/webhook", response_model=WebHookConfigResponse)
async def create_webhook_config(
    webhook_data: WebHookConfigSchema,
    session: Session = Depends(init_session),
    current_user: Users = Depends(verify_token)
):
    """
    Cria uma nova configuração de webhook.
    Requer permissão de administrador.
    """
    check_admin_permission(current_user)
    
    try:
        new_webhook = WebHookConfig(
            url=webhook_data.url,
            active=webhook_data.active,
            timeout=webhook_data.timeout,
            access_token=webhook_data.access_token
        )
        
        session.add(new_webhook)
        session.commit()
        session.refresh(new_webhook)
        
        return new_webhook
        
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating webhook config: {str(e)}")


@config_router.get("/webhook", response_model=List[WebHookConfigResponse])
async def list_webhook_configs(
    session: Session = Depends(init_session),
    current_user: Users = Depends(verify_token)
):
    """
    Lista todas as configurações de webhook.
    """
    try:
        webhooks = session.query(WebHookConfig).order_by(WebHookConfig.created_at.desc()).all()
        return webhooks
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching webhook configs: {str(e)}")


@config_router.get("/webhook/{webhook_id}", response_model=WebHookConfigResponse)
async def get_webhook_config(
    webhook_id: int,
    session: Session = Depends(init_session),
    current_user: Users = Depends(verify_token)
):
    """
    Obtém uma configuração de webhook específica pelo ID.
    """
    try:
        webhook = session.query(WebHookConfig).filter(WebHookConfig.id == webhook_id).first()
        
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook config not found")
            
        return webhook
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching webhook config: {str(e)}")


@config_router.put("/webhook/{webhook_id}", response_model=WebHookConfigResponse)
async def update_webhook_config(
    webhook_id: int,
    webhook_data: WebHookConfigUpdate,
    session: Session = Depends(init_session),
    current_user: Users = Depends(verify_token)
):
    """
    Atualiza uma configuração de webhook existente.
    Requer permissão de administrador.
    """
    check_admin_permission(current_user)
    
    try:
        webhook = session.query(WebHookConfig).filter(WebHookConfig.id == webhook_id).first()
        
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook config not found")
        
        # Atualizar apenas os campos fornecidos
        if webhook_data.url is not None:
            webhook.url = webhook_data.url
        if webhook_data.active is not None:
            webhook.active = webhook_data.active
        
        webhook.updated_at = func.now()
        
        session.commit()
        session.refresh(webhook)
        
        return webhook
        
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating webhook config: {str(e)}")


@config_router.delete("/webhook/{webhook_id}")
async def delete_webhook_config(
    webhook_id: int,
    session: Session = Depends(init_session),
    current_user: Users = Depends(verify_token)
):
    """
    Deleta uma configuração de webhook.
    Requer permissão de administrador.
    """
    check_admin_permission(current_user)
    
    try:
        webhook = session.query(WebHookConfig).filter(WebHookConfig.id == webhook_id).first()
        
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook config not found")
        
        session.delete(webhook)
        session.commit()
        
        return {"message": "Webhook config deleted successfully"}
        
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting webhook config: {str(e)}")


# =============================================================================
# ROTAS DE EMAIL
# =============================================================================

@config_router.post("/email", response_model=EmailConfigResponse)
async def create_email_config(
    email_data: EmailConfigSchema,
    session: Session = Depends(init_session),
    current_user: Users = Depends(verify_token)
):
    """
    Cria uma nova configuração de email.
    Requer permissão de administrador.
    """
    check_admin_permission(current_user)
    
    try:
        
        new_email_config = EmailConfig(
            email=email_data.email,
            password=email_data.password,
            port=email_data.port,
            server=email_data.server,
            active=email_data.active
        )

        session.add(new_email_config)
        session.commit()
        session.refresh(new_email_config)

        return new_email_config
        
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating email config: {str(e)}")


@config_router.get("/email", response_model=List[EmailConfigResponse])
async def list_email_configs(
    session: Session = Depends(init_session),
    current_user: Users = Depends(verify_token)
):
    """
    Lista todas as configurações de email.
    """
    try:
        email_configs = session.query(EmailConfig).order_by(EmailConfig.created_at.desc()).all()
        return email_configs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching email configs: {str(e)}")


@config_router.get("/email/{email_id}", response_model=EmailConfigResponse)
async def get_email_config(
    email_id: int,
    session: Session = Depends(init_session),
    current_user: Users = Depends(verify_token)
):
    """
    Obtém uma configuração de email específica pelo ID.
    """
    try:
        email_config = session.query(EmailConfig).filter(EmailConfig.id == email_id).first()
        
        if not email_config:
            raise HTTPException(status_code=404, detail="Email config not found")
            
        return email_config
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching email config: {str(e)}")


@config_router.put("/email/{email_id}", response_model=EmailConfigResponse)
async def update_email_config(
    email_id: int,
    email_data: EmailConfigUpdate,
    session: Session = Depends(init_session),
    current_user: Users = Depends(verify_token)
):
    """
    Atualiza uma configuração de email existente.
    Requer permissão de administrador.
    """
    check_admin_permission(current_user)
    
    try:
        email_config = session.query(EmailConfig).filter(EmailConfig.id == email_id).first()
        
        if not email_config:
            raise HTTPException(status_code=404, detail="Email config not found")
        
        # Atualizar apenas os campos fornecidos
        if email_data.email is not None:
            email_config.email = email_data.email
        if email_data.password is not None:
            email_config.password = bcrypt_context.hash(email_data.password)
        if email_data.port is not None:
            email_config.port = email_data.port
        if email_data.server is not None:
            email_config.server = email_data.server

        email_config.updated_at = func.now()
        
        session.commit()
        session.refresh(email_config)
        
        return email_config
        
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating email config: {str(e)}")


@config_router.delete("/email/{email_id}")
async def delete_email_config(
    email_id: int,
    session: Session = Depends(init_session),
    current_user: Users = Depends(verify_token)
):
    """
    Deleta uma configuração de email.
    Requer permissão de administrador.
    """
    check_admin_permission(current_user)
    
    try:
        email_config = session.query(EmailConfig).filter(EmailConfig.id == email_id).first()
        
        if not email_config:
            raise HTTPException(status_code=404, detail="Email config not found")
        
        session.delete(email_config)
        session.commit()
        
        return {"message": "Email config deleted successfully"}
        
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting email config: {str(e)}")


# =============================================================================
# ROTAS DE CONFIGURAÇÃO DE LIMITES DE FALHAS
# =============================================================================

@config_router.post("/failure-threshold", response_model=FailureThresholdConfigResponse)
async def create_failure_threshold_config(
    threshold_data: FailureThresholdConfigSchema,
    session: Session = Depends(init_session),
    current_user: Users = Depends(verify_token)
):
    """
    Cria uma nova configuração de limites de falhas.
    Requer permissão de administrador.
    """
    check_admin_permission(current_user)
    
    try:
        new_threshold_config = FailureThresholdConfig(
            consecutive_snmp_failures=threshold_data.consecutive_snmp_failures,
            consecutive_ping_failures=threshold_data.consecutive_ping_failures,
            active=threshold_data.active
        )
        
        session.add(new_threshold_config)
        session.commit()
        session.refresh(new_threshold_config)
        
        return new_threshold_config
        
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating failure threshold config: {str(e)}")


@config_router.get("/failure-threshold", response_model=List[FailureThresholdConfigResponse])
async def list_failure_threshold_configs(
    session: Session = Depends(init_session),
    current_user: Users = Depends(verify_token)
):
    """
    Lista todas as configurações de limites de falhas.
    """
    try:
        threshold_configs = session.query(FailureThresholdConfig).order_by(FailureThresholdConfig.created_at.desc()).all()
        return threshold_configs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching failure threshold configs: {str(e)}")


@config_router.get("/failure-threshold/{threshold_id}", response_model=FailureThresholdConfigResponse)
async def get_failure_threshold_config(
    threshold_id: int,
    session: Session = Depends(init_session),
    current_user: Users = Depends(verify_token)
):
    """
    Obtém uma configuração de limites de falhas específica pelo ID.
    """
    try:
        threshold_config = session.query(FailureThresholdConfig).filter(FailureThresholdConfig.id == threshold_id).first()
        
        if not threshold_config:
            raise HTTPException(status_code=404, detail="Failure threshold config not found")
            
        return threshold_config
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching failure threshold config: {str(e)}")


@config_router.put("/failure-threshold/{threshold_id}", response_model=FailureThresholdConfigResponse)
async def update_failure_threshold_config(
    threshold_id: int,
    threshold_data: FailureThresholdConfigUpdate,
    session: Session = Depends(init_session),
    current_user: Users = Depends(verify_token)
):
    """
    Atualiza uma configuração de limites de falhas existente.
    Requer permissão de administrador.
    """
    check_admin_permission(current_user)
    
    try:
        threshold_config = session.query(FailureThresholdConfig).filter(FailureThresholdConfig.id == threshold_id).first()
        
        if not threshold_config:
            raise HTTPException(status_code=404, detail="Failure threshold config not found")
        
        # Atualizar apenas os campos fornecidos
        if threshold_data.consecutive_snmp_failures is not None:
            threshold_config.consecutive_snmp_failures = threshold_data.consecutive_snmp_failures
        if threshold_data.consecutive_ping_failures is not None:
            threshold_config.consecutive_ping_failures = threshold_data.consecutive_ping_failures
        if threshold_data.active is not None:
            threshold_config.active = threshold_data.active
        
        threshold_config.updated_at = func.now()
        
        session.commit()
        session.refresh(threshold_config)
        
        return threshold_config
        
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating failure threshold config: {str(e)}")


@config_router.delete("/failure-threshold/{threshold_id}")
async def delete_failure_threshold_config(
    threshold_id: int,
    session: Session = Depends(init_session),
    current_user: Users = Depends(verify_token)
):
    """
    Deleta uma configuração de limites de falhas.
    Requer permissão de administrador.
    """
    check_admin_permission(current_user)
    
    try:
        threshold_config = session.query(FailureThresholdConfig).filter(FailureThresholdConfig.id == threshold_id).first()
        
        if not threshold_config:
            raise HTTPException(status_code=404, detail="Failure threshold config not found")
        
        session.delete(threshold_config)
        session.commit()
        
        return {"message": "Failure threshold config deleted successfully"}
        
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting failure threshold config: {str(e)}")


# =============================================================================
# ROTA PARA OBTER CONFIGURAÇÃO ATIVA
# =============================================================================

@config_router.get("/active")
async def get_active_configs(
    session: Session = Depends(init_session),
    current_user: Users = Depends(verify_token)
):
    """
    Obtém todas as configurações ativas do sistema.
    """
    try:
        active_webhook = session.query(WebHookConfig).filter(WebHookConfig.active == True).first()
        active_email = session.query(EmailConfig).filter(EmailConfig.active == True).first()
        active_threshold = session.query(FailureThresholdConfig).filter(FailureThresholdConfig.active == True).first()
        performance_thresholds = session.query(PerformanceThresholds).all()
        
        return {
            "webhook": active_webhook,
            "email": active_email,
            "failure_threshold": active_threshold,
            "performance_thresholds": performance_thresholds
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching active configs: {str(e)}")


# =============================================================================
# ROTAS DE PERFORMANCE THRESHOLDS
# =============================================================================

@config_router.post("/performance-thresholds", response_model=PerformanceThresholdsResponse)
async def create_performance_threshold(
    threshold_data: PerformanceThresholdsSchemas,
    session: Session = Depends(init_session),
    current_user: Users = Depends(verify_token)
):
    """
    Cria uma nova configuração de limite de performance.
    Requer permissão de administrador.
    """
    check_admin_permission(current_user)
    
    try:
        # Verificar se já existe configuração para este tipo de métrica
        existing = session.query(PerformanceThresholds).filter(
            PerformanceThresholds.metric_type == threshold_data.metric_type
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"Performance threshold for {threshold_data.metric_type} already exists"
            )
        
        new_threshold = PerformanceThresholds(
            metric_type=threshold_data.metric_type,
            warning_threshold=threshold_data.warning_threshold,
            critical_threshold=threshold_data.critical_threshold,
            enabled=threshold_data.enabled
        )
        
        session.add(new_threshold)
        session.commit()
        session.refresh(new_threshold)
        
        return new_threshold
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating performance threshold: {str(e)}")


@config_router.get("/performance-thresholds", response_model=List[PerformanceThresholdsResponse])
async def get_performance_thresholds(
    session: Session = Depends(init_session),
    current_user: Users = Depends(verify_token)
):
    """
    Obtém todas as configurações de limites de performance.
    """
    try:
        thresholds = session.query(PerformanceThresholds).all()
        return thresholds
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching performance thresholds: {str(e)}")


@config_router.get("/performance-thresholds/{metric_type}", response_model=PerformanceThresholdsResponse)
async def get_performance_threshold_by_type(
    metric_type: str,
    session: Session = Depends(init_session),
    current_user: Users = Depends(verify_token)
):
    """
    Obtém configuração de limite de performance por tipo de métrica.
    """
    try:
        threshold = session.query(PerformanceThresholds).filter(
            PerformanceThresholds.metric_type == metric_type
        ).first()
        
        if not threshold:
            raise HTTPException(status_code=404, detail=f"Performance threshold for {metric_type} not found")
        
        return threshold
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching performance threshold: {str(e)}")


@config_router.put("/performance-thresholds/{threshold_id}", response_model=PerformanceThresholdsResponse)
async def update_performance_threshold(
    threshold_id: int,
    threshold_update: PerformanceThresholdsUpdate,
    session: Session = Depends(init_session),
    current_user: Users = Depends(verify_token)
):
    """
    Atualiza uma configuração de limite de performance.
    Requer permissão de administrador.
    """
    check_admin_permission(current_user)
    
    try:
        threshold = session.query(PerformanceThresholds).filter(
            PerformanceThresholds.id == threshold_id
        ).first()
        
        if not threshold:
            raise HTTPException(status_code=404, detail="Performance threshold not found")
        
        # Atualizar apenas os campos fornecidos
        if threshold_update.warning_threshold is not None:
            threshold.warning_threshold = threshold_update.warning_threshold
        if threshold_update.critical_threshold is not None:
            threshold.critical_threshold = threshold_update.critical_threshold
        if threshold_update.enabled is not None:
            threshold.enabled = threshold_update.enabled
        
        threshold.updated_at = datetime.now()
        
        session.commit()
        session.refresh(threshold)
        
        return threshold
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating performance threshold: {str(e)}")


@config_router.delete("/performance-thresholds/{threshold_id}")
async def delete_performance_threshold(
    threshold_id: int,
    session: Session = Depends(init_session),
    current_user: Users = Depends(verify_token)
):
    """
    Remove uma configuração de limite de performance.
    Requer permissão de administrador.
    """
    check_admin_permission(current_user)
    
    try:
        threshold = session.query(PerformanceThresholds).filter(
            PerformanceThresholds.id == threshold_id
        ).first()
        
        if not threshold:
            raise HTTPException(status_code=404, detail="Performance threshold not found")
        
        session.delete(threshold)
        session.commit()
        
        return {"success": True, "message": f"Performance threshold for {threshold.metric_type} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting performance threshold: {str(e)}")


@config_router.post("/performance-thresholds/reset-defaults")
async def reset_default_performance_thresholds(
    session: Session = Depends(init_session),
    current_user: Users = Depends(verify_token)
):
    """
    Restaura os limites padrão de performance.
    Requer permissão de administrador.
    """
    check_admin_permission(current_user)
    
    try:
        # Remover configurações existentes
        session.query(PerformanceThresholds).delete()
        
        # Criar configurações padrão
        default_thresholds = [
            PerformanceThresholds('cpu', 80, 90, True),
            PerformanceThresholds('memory', 85, 95, True),
            PerformanceThresholds('storage', 85, 95, True),
            PerformanceThresholds('network', 80, 95, True)
        ]
        
        for threshold in default_thresholds:
            session.add(threshold)
        
        session.commit()
        
        return {"success": True, "message": "Default performance thresholds restored successfully"}
        
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error resetting default thresholds: {str(e)}")
