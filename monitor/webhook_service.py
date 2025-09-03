import os
import json
import requests
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class WebhookService:
    def __init__(self):
        """
        Inicializa o serviço de webhook.
        Configurações podem ser obtidas de variáveis de ambiente ou banco de dados.
        """
        # Configurações básicas (podem ser sobrescritas pelo banco de dados)
        self.webhook_url = os.getenv("WEBHOOK_URL", "")
        self.enabled = os.getenv("WEBHOOK_ALERTS_ENABLED", "false").lower() == "true"
        self.timeout = int(os.getenv("WEBHOOK_TIMEOUT", "30"))
        self.retry_attempts = int(os.getenv("WEBHOOK_RETRY_ATTEMPTS", "3"))
        
        # Headers customizados
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "InfraWatch-Monitor/1.0"
        }
        
        # Adicionar token de autorização se configurado
        webhook_token = os.getenv("WEBHOOK_TOKEN", "")
        if webhook_token:
            self.headers["Authorization"] = f"Bearer {webhook_token}"
        
        if not self.webhook_url and self.enabled:
            logger.warning("Webhook URL not configured. Webhook alerts will be disabled.")
            self.enabled = False

    def send_alert_webhook(
        self, 
        webhook_url: str,
        endpoint_name: str,
        endpoint_ip: str,
        status: str,
        timestamp: datetime,
        additional_info: Optional[str] = None
    ) -> bool:
        """
        Envia webhook de alerta para mudança de status de endpoint
        """
        if not self.enabled and not webhook_url:
            logger.info(f"Webhook alerts disabled. Would send alert for {endpoint_name}")
            return True
        
        # Usar URL fornecida ou URL padrão
        url = webhook_url or self.webhook_url
        
        if not url:
            logger.error("No webhook URL configured")
            return False
        
        try:
            # Criar payload do webhook
            payload = self._create_alert_payload(
                endpoint_name, endpoint_ip, status, timestamp, additional_info
            )
            
            # Enviar webhook com retry
            success = self._send_webhook_with_retry(url, payload)
            
            if success:
                logger.info(f"Alert webhook sent successfully to {url}")
            else:
                logger.error(f"Failed to send alert webhook to {url}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send alert webhook: {e}")
            return False

    def send_system_status_webhook(
        self,
        webhook_url: str,
        system_status: Dict[str, Any],
        timestamp: datetime
    ) -> bool:
        """
        Envia webhook com status geral do sistema de monitoramento
        """
        if not self.enabled and not webhook_url:
            logger.info("Webhook alerts disabled. Would send system status")
            return True
        
        # Usar URL fornecida ou URL padrão
        url = webhook_url or self.webhook_url
        
        if not url:
            logger.error("No webhook URL configured")
            return False
        
        try:
            # Criar payload do status do sistema
            payload = self._create_system_status_payload(system_status, timestamp)
            
            # Enviar webhook
            success = self._send_webhook_with_retry(url, payload)
            
            if success:
                logger.info(f"System status webhook sent successfully to {url}")
            else:
                logger.error(f"Failed to send system status webhook to {url}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send system status webhook: {e}")
            return False

    def _create_alert_payload(
        self, 
        endpoint_name: str, 
        endpoint_ip: str, 
        status: str, 
        timestamp: datetime,
        additional_info: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria o payload JSON para webhook de alerta
        """
        # Determinar cor e emoji baseado no status
        if status == "SNMP DOWN":
            color = "#fd7e14"  # Laranja
            emoji = "🟠"
            severity = "warning"
        elif status == "UP":
            color = "#28a745"  # Verde
            emoji = "🟢"
            severity = "info"
        elif status == "DOWN":
            color = "#dc3545"  # Vermelho
            emoji = "🔴"
            severity = "critical"
        else:
            color = "#6c757d"  # Cinza
            emoji = "⚪"
            severity = "unknown"

        payload = {
            "type": "alert",
            "service": "InfraWatch",
            "timestamp": timestamp.isoformat(),
            "severity": severity,
            "alert": {
                "title": f"{emoji} InfraWatch Alert - {status}",
                "message": f"Endpoint '{endpoint_name}' ({endpoint_ip}) is {status}",
                "details": {
                    "endpoint_name": endpoint_name,
                    "endpoint_ip": endpoint_ip,
                    "status": status,
                    "timestamp": timestamp.strftime('%d/%m/%Y %H:%M:%S'),
                    "additional_info": additional_info
                },
                "color": color
            }
        }

        return payload

    def _create_system_status_payload(
        self,
        system_status: Dict[str, Any],
        timestamp: datetime
    ) -> Dict[str, Any]:
        """
        Cria o payload JSON para status do sistema
        """
        total_endpoints = system_status.get("total_endpoints", 0)
        up_endpoints = system_status.get("up_endpoints", 0)
        down_endpoints = system_status.get("down_endpoints", 0)
        snmp_down_endpoints = system_status.get("snmp_down_endpoints", 0)
        
        # Determinar status geral
        if down_endpoints == 0 and snmp_down_endpoints == 0:
            overall_status = "healthy"
            color = "#28a745"  # Verde
            emoji = "✅"
        elif down_endpoints > 0:
            overall_status = "critical"
            color = "#dc3545"  # Vermelho
            emoji = "❌"
        else:
            overall_status = "warning"
            color = "#fd7e14"  # Laranja
            emoji = "⚠️"

        payload = {
            "type": "system_status",
            "service": "InfraWatch",
            "timestamp": timestamp.isoformat(),
            "system": {
                "title": f"{emoji} InfraWatch System Status",
                "status": overall_status,
                "message": f"Monitoring {total_endpoints} endpoints",
                "details": {
                    "total_endpoints": total_endpoints,
                    "up_endpoints": up_endpoints,
                    "down_endpoints": down_endpoints,
                    "snmp_down_endpoints": snmp_down_endpoints,
                    "timestamp": timestamp.strftime('%d/%m/%Y %H:%M:%S')
                },
                "color": color
            }
        }

        # Adicionar informações extras se disponíveis
        if "uptime" in system_status:
            payload["system"]["details"]["uptime"] = system_status["uptime"]
        
        if "last_check" in system_status:
            payload["system"]["details"]["last_check"] = system_status["last_check"]

        return payload

    def _send_webhook_with_retry(self, url: str, payload: Dict[str, Any]) -> bool:
        """
        Envia webhook com tentativas de retry
        """
        for attempt in range(self.retry_attempts):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=self.headers,
                    timeout=self.timeout
                )
                
                # Considerar sucesso se status code for 2xx
                if 200 <= response.status_code < 300:
                    logger.debug(f"Webhook sent successfully (attempt {attempt + 1}): {response.status_code}")
                    return True
                else:
                    logger.warning(f"Webhook attempt {attempt + 1} failed with status {response.status_code}: {response.text}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Webhook attempt {attempt + 1} timed out")
            except requests.exceptions.ConnectionError:
                logger.warning(f"Webhook attempt {attempt + 1} failed: connection error")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Webhook attempt {attempt + 1} failed: {e}")
            
            # Se não for a última tentativa, aguardar um pouco
            if attempt < self.retry_attempts - 1:
                import time
                time.sleep(2 ** attempt)  # Backoff exponencial: 1s, 2s, 4s...
        
        return False

    def test_connection(self, webhook_url: Optional[str] = None) -> bool:
        """
        Testa a conexão com o webhook enviando uma mensagem de teste
        """
        test_url = webhook_url or self.webhook_url
        
        if not test_url:
            logger.error("No webhook URL to test")
            return False
        
        try:
            test_payload = {
                "type": "test",
                "service": "InfraWatch",
                "timestamp": datetime.now().isoformat(),
                "message": "Test connection from InfraWatch webhook service",
                "test": True
            }
            
            response = requests.post(
                test_url,
                json=test_payload,
                headers=self.headers,
                timeout=self.timeout
            )
            
            if 200 <= response.status_code < 300:
                logger.info(f"Webhook connection test successful: {response.status_code}")
                return True
            else:
                logger.error(f"Webhook connection test failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Webhook connection test failed: {e}")
            return False

    def set_webhook_url(self, url: str):
        """
        Define uma nova URL de webhook
        """
        self.webhook_url = url
        if url and not self.enabled:
            self.enabled = True
        elif not url:
            self.enabled = False

    def set_enabled(self, enabled: bool):
        """
        Habilita ou desabilita o serviço de webhook
        """
        self.enabled = enabled and bool(self.webhook_url)

    def get_status(self) -> Dict[str, Any]:
        """
        Retorna o status atual do serviço de webhook
        """
        return {
            "enabled": self.enabled,
            "webhook_url": self.webhook_url[:50] + "..." if len(self.webhook_url) > 50 else self.webhook_url,
            "timeout": self.timeout,
            "retry_attempts": self.retry_attempts,
            "has_token": bool(self.headers.get("Authorization"))
        }
