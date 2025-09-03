import os
import sys
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

# Adicionar o diretório api ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

from alert_email_service import EmailService
from webhook_service import WebhookService

logger = logging.getLogger(__name__)

class AlertService:
    """
    Serviço unificado para envio de alertas via email e webhook.
    Integra com as configurações do banco de dados.
    """
    
    def __init__(self, db_session=None):
        """
        Inicializa o serviço de alertas.
        
        Args:
            db_session: Sessão do banco de dados para obter configurações
        """
        self.db_session = db_session
        self.email_service = EmailService(db_session)
        self.webhook_service = WebhookService()
        
        # Carregar configurações do banco
        self._load_webhook_config_from_db()
        self._load_failure_thresholds_from_db()
        
    def _load_webhook_config_from_db(self):
        """
        Carrega configurações de webhook do banco de dados
        """
        if not self.db_session:
            return
        
        try:
            from models import WebHookConfig
            
            # Buscar configuração ativa
            webhook_config = self.db_session.query(WebHookConfig).filter(
                WebHookConfig.active == True
            ).first()
            
            if webhook_config:
                self.webhook_service.set_webhook_url(webhook_config.url)
                logger.info(f"Webhook configuration loaded from database: {webhook_config.url}")
            else:
                logger.info("No active webhook configuration found in database")
                
        except Exception as e:
            logger.warning(f"Failed to load webhook config from database: {e}")
    
    def _load_failure_thresholds_from_db(self):
        """
        Carrega limites de falhas consecutivas do banco de dados
        """
        if not self.db_session:
            # Valores padrão
            self.snmp_failure_threshold = 3
            self.ping_failure_threshold = 5
            return
        
        try:
            from models import FailureThresholdConfig
            
            # Buscar configuração ativa
            threshold_config = self.db_session.query(FailureThresholdConfig).filter(
                FailureThresholdConfig.active == True
            ).first()
            
            if threshold_config:
                self.snmp_failure_threshold = threshold_config.consecutive_snmp_failures
                self.ping_failure_threshold = threshold_config.consecutive_ping_failures
                logger.info(f"Failure thresholds loaded: SNMP={self.snmp_failure_threshold}, Ping={self.ping_failure_threshold}")
            else:
                # Valores padrão
                self.snmp_failure_threshold = 3
                self.ping_failure_threshold = 5
                logger.info("No active failure threshold config found, using defaults")
                
        except Exception as e:
            logger.warning(f"Failed to load failure thresholds from database: {e}")
            self.snmp_failure_threshold = 3
            self.ping_failure_threshold = 5

    def send_endpoint_alert(
        self,
        endpoint_name: str,
        endpoint_ip: str,
        status: str,
        timestamp: datetime,
        additional_info: Optional[str] = None,
        force_send: bool = False
    ) -> Dict[str, bool]:
        """
        Envia alerta de mudança de status de endpoint via email e webhook.
        
        Args:
            endpoint_name: Nome do endpoint
            endpoint_ip: IP do endpoint
            status: Status atual (UP, DOWN, SNMP DOWN)
            timestamp: Timestamp do evento
            additional_info: Informações adicionais
            force_send: Força o envio mesmo se não atender aos critérios
            
        Returns:
            Dict com status do envio por email e webhook
        """
        subject = f"InfraWatch Alert: {endpoint_name} is {status}"
        
        results = {
            "email_sent": False,
            "webhook_sent": False
        }
        
        # Enviar email para administradores
        try:
            if self.email_service.enabled or force_send:
                results["email_sent"] = self.email_service.send_alert_to_admins(
                    subject=subject,
                    endpoint_name=endpoint_name,
                    endpoint_ip=endpoint_ip,
                    status=status,
                    timestamp=timestamp,
                    additional_info=additional_info
                )
            else:
                logger.info("Email service disabled, skipping email alert")
                
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
        
        # Enviar webhook
        try:
            if self.webhook_service.enabled or force_send:
                results["webhook_sent"] = self.webhook_service.send_alert_webhook(
                    webhook_url=self.webhook_service.webhook_url,
                    endpoint_name=endpoint_name,
                    endpoint_ip=endpoint_ip,
                    status=status,
                    timestamp=timestamp,
                    additional_info=additional_info
                )
            else:
                logger.info("Webhook service disabled, skipping webhook alert")
                
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
        
        return results

    def send_system_status_alert(
        self,
        system_status: Dict[str, Any],
        timestamp: datetime
    ) -> Dict[str, bool]:
        """
        Envia alerta com status geral do sistema.
        
        Args:
            system_status: Dicionário com status do sistema
            timestamp: Timestamp do evento
            
        Returns:
            Dict com status do envio
        """
        results = {
            "webhook_sent": False
        }
        
        # Enviar webhook de status do sistema
        try:
            if self.webhook_service.enabled:
                results["webhook_sent"] = self.webhook_service.send_system_status_webhook(
                    webhook_url=self.webhook_service.webhook_url,
                    system_status=system_status,
                    timestamp=timestamp
                )
            else:
                logger.info("Webhook service disabled, skipping system status webhook")
                
        except Exception as e:
            logger.error(f"Failed to send system status webhook: {e}")
        
        return results

    def should_send_alert(
        self, 
        failure_type: str, 
        consecutive_failures: int
    ) -> bool:
        """
        Determina se deve enviar alerta baseado no número de falhas consecutivas.
        
        Args:
            failure_type: Tipo de falha ('snmp' ou 'ping')
            consecutive_failures: Número de falhas consecutivas
            
        Returns:
            True se deve enviar alerta
        """
        if failure_type.lower() == 'snmp':
            return consecutive_failures >= self.snmp_failure_threshold
        elif failure_type.lower() == 'ping':
            return consecutive_failures >= self.ping_failure_threshold
        else:
            logger.warning(f"Unknown failure type: {failure_type}")
            return False

    def test_services(self) -> Dict[str, bool]:
        """
        Testa a conectividade dos serviços de email e webhook.
        
        Returns:
            Dict com resultado dos testes
        """
        results = {
            "email_connection": False,
            "webhook_connection": False
        }
        
        # Testar conexão de email
        try:
            results["email_connection"] = self.email_service.test_connection()
        except Exception as e:
            logger.error(f"Email connection test failed: {e}")
        
        # Testar conexão de webhook
        try:
            results["webhook_connection"] = self.webhook_service.test_connection()
        except Exception as e:
            logger.error(f"Webhook connection test failed: {e}")
        
        return results

    def reload_configurations(self):
        """
        Recarrega todas as configurações do banco de dados
        """
        logger.info("Reloading alert service configurations...")
        
        self.email_service.reload_config_from_db()
        self._load_webhook_config_from_db()
        self._load_failure_thresholds_from_db()
        
        logger.info("Alert service configurations reloaded")

    def get_service_status(self) -> Dict[str, Any]:
        """
        Retorna o status de todos os serviços de alerta.
        
        Returns:
            Dict com status detalhado
        """
        return {
            "email_service": self.email_service.get_status(),
            "webhook_service": self.webhook_service.get_status(),
            "failure_thresholds": {
                "snmp": self.snmp_failure_threshold,
                "ping": self.ping_failure_threshold
            },
            "database_connected": self.db_session is not None
        }

    def send_test_alert(self) -> Dict[str, bool]:
        """
        Envia alertas de teste para verificar funcionamento.
        
        Returns:
            Dict com resultado dos envios
        """
        test_timestamp = datetime.now()
        
        return self.send_endpoint_alert(
            endpoint_name="Test Endpoint",
            endpoint_ip="192.168.1.1",
            status="TEST",
            timestamp=test_timestamp,
            additional_info="This is a test alert from InfraWatch Alert Service",
            force_send=True
        )
