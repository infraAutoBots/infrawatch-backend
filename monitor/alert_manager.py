import os
from datetime import datetime
from typing import Dict, List, Optional
import logging
from sqlalchemy.orm import Session
from alert_email_service import EmailService
from dependencies import init_session
from models import EndPoints

logger = logging.getLogger(__name__)

class AlertManager:
    def __init__(self):
        self.email_service = EmailService()
        self.previous_status: Dict[str, bool] = {}  # Armazena status anterior de cada IP
        self.default_recipients = self._load_default_recipients()

    def _load_default_recipients(self) -> List[str]:
        """
        Carrega lista de destinatários padrão das variáveis de ambiente
        """
        recipients_str = os.getenv("DEFAULT_ALERT_RECIPIENTS", "ndondadaniel2020@gmail.com")
        if recipients_str:
            return [email.strip() for email in recipients_str.split(",") if email.strip()]
        return []

    def check_and_send_alerts(self, ip: str, current_status: bool, endpoint_data: dict = None):
        """
        Verifica se deve enviar alerta baseado na mudança de status
        
        Regra implementada: Alerta quando endpoint muda de UP (True) para DOWN (False)
        """
        try:
            # Verifica se houve mudança de status
            previous_status = self.previous_status.get(ip)
            
            # Se é a primeira verificação, apenas armazena o status atual
            if previous_status is None:
                self.previous_status[ip] = current_status
                logger.debug(f"First check for {ip}, status: {'UP' if current_status else 'DOWN'}")
                return
            
            # Se não houve mudança, não faz nada
            if previous_status == current_status:
                return
                
            # Atualiza o status armazenado
            self.previous_status[ip] = current_status
            
            # REGRA 1: Alerta quando muda de UP para DOWN
            if previous_status and not current_status:
                self._send_down_alert(ip, endpoint_data)
                logger.info(f"DOWN alert sent for {ip}")
                
            # REGRA 2: Alerta quando muda de DOWN para UP (recuperação)
            elif not previous_status and current_status:
                self._send_up_alert(ip, endpoint_data)
                logger.info(f"UP alert sent for {ip}")
                
        except Exception as e:
            logger.error(f"Error in alert check for {ip}: {e}")

    def _send_down_alert(self, ip: str, endpoint_data: dict = None):
        """
        Envia alerta quando endpoint fica DOWN
        """
        endpoint_info = self._get_endpoint_info(ip)
        endpoint_name = endpoint_info.get('name', ip)
        
        subject = f"🔴 ALERTA: {endpoint_name} está DOWN"
        
        additional_info = None
        if endpoint_data and endpoint_data.get('snmp_data'):
            snmp_info = []
            snmp_data = endpoint_data['snmp_data']
            if snmp_data.get('sysDescr'):
                snmp_info.append(f"Sistema: {snmp_data['sysDescr']}")
            if snmp_data.get('sysName'):
                snmp_info.append(f"Nome: {snmp_data['sysName']}")
            if snmp_info:
                additional_info = "<br>".join(snmp_info)
        
        recipients = self._get_recipients_for_endpoint(ip)
        if recipients:
            self.email_service.send_alert_email(
                to_emails=recipients,
                subject=subject,
                endpoint_name=endpoint_name,
                endpoint_ip=ip,
                status="DOWN",
                timestamp=datetime.now(),
                additional_info=additional_info
            )

    def _send_up_alert(self, ip: str, endpoint_data: dict = None):
        """
        Envia alerta quando endpoint volta a ficar UP (recuperação)
        """
        endpoint_info = self._get_endpoint_info(ip)
        endpoint_name = endpoint_info.get('name', ip)
        
        subject = f"🟢 RECUPERAÇÃO: {endpoint_name} está UP novamente"
        
        additional_info = None
        if endpoint_data and endpoint_data.get('snmp_data'):
            snmp_info = []
            snmp_data = endpoint_data['snmp_data']
            if snmp_data.get('sysDescr'):
                snmp_info.append(f"Sistema: {snmp_data['sysDescr']}")
            if snmp_data.get('sysName'):
                snmp_info.append(f"Nome: {snmp_data['sysName']}")
            if snmp_data.get('sysUpTime'):
                snmp_info.append(f"Uptime: {snmp_data['sysUpTime']}")
            if snmp_info:
                additional_info = "<br>".join(snmp_info)
        
        recipients = self._get_recipients_for_endpoint(ip)
        if recipients:
            self.email_service.send_alert_email(
                to_emails=recipients,
                subject=subject,
                endpoint_name=endpoint_name,
                endpoint_ip=ip,
                status="UP",
                timestamp=datetime.now(),
                additional_info=additional_info
            )

    def _get_endpoint_info(self, ip: str) -> dict:
        """
        Busca informações do endpoint no banco de dados
        """
        try:
            session = init_session()
            endpoint = session.query(EndPoints).filter(EndPoints.ip == ip).first()
            session.close()
            
            if endpoint:
                return {
                    'name': endpoint.name or ip,
                    'description': endpoint.description,
                    'id': endpoint.id
                }
            return {'name': ip}
        except Exception as e:
            logger.error(f"Error getting endpoint info for {ip}: {e}")
            return {'name': ip}

    def _get_recipients_for_endpoint(self, ip: str) -> List[str]:
        """
        Retorna lista de destinatários para um endpoint específico
        Por enquanto, usa apenas os destinatários padrão
        """
        # TODO: Implementar destinatários específicos por endpoint
        return self.default_recipients

    def test_email_service(self) -> bool:
        """
        Testa o serviço de email
        """
        return self.email_service.test_connection()

    def send_test_alert(self, test_email: str) -> bool:
        """
        Envia um alerta de teste
        """
        try:
            return self.email_service.send_alert_email(
                to_emails=[test_email],
                subject="🧪 Teste de Alerta - InfraWatch",
                endpoint_name="Endpoint de Teste",
                endpoint_ip="192.168.1.100",
                status="DOWN",
                timestamp=datetime.now(),
                additional_info="Este é um email de teste do sistema de alertas InfraWatch."
            )
        except Exception as e:
            logger.error(f"Error sending test alert: {e}")
            return False