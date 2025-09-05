import os
import requests
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
import logging
from dependencies import init_session
from sqlalchemy.orm import Session
from models import WebHookConfig



logger = logging.getLogger(__name__)


class WebhookService:
    def __init__(self, session: Session = init_session()):
        """
        Inicializa o serviço de webhook.
        Configurações podem ser obtidas de variáveis de ambiente ou banco de dados.
        """
        # Configurações básicas (podem ser sobrescritas pelo banco de dados)
        # Tenta obter o primeiro webhook configurado no banco de dados
        db_webhook = session.query(WebHookConfig).first()
        self.webhook_url = db_webhook.url if db_webhook and db_webhook.url else ""
        self.enabled = db_webhook.active if db_webhook else False
        self.timeout = int(os.getenv("WEBHOOK_TIMEOUT", "30"))
        self.retry_attempts = int(os.getenv("WEBHOOK_RETRY_ATTEMPTS", "3"))
        session.close()

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
        self.set_webhook_url(self.webhook_url)

    def _format_timestamp_for_discord(self, timestamp: datetime) -> str:
        """
        Formata timestamp para usar no Discord com fuso horário consistente
        """
        if timestamp.tzinfo is None:
            # Se não tem timezone, assume horário local (UTC-3 para Brasil)
            # Assume horário de Brasília (UTC-3)
            timestamp = timestamp.replace(tzinfo=timezone(timedelta(hours=1)))
        return timestamp.isoformat()

    def _format_timestamp_for_display(self, timestamp: datetime) -> str:
        """
        Formata timestamp para exibição em formato brasileiro
        """
        return timestamp.strftime('%d/%m/%Y %H:%M:%S')

    def send_alert_webhook(
        self, 
        webhook_url: Optional[str],
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

        if additional_info is None and status == "UP":
            additional_info = "Host restaurado com sucesso. Conectividade normalizada."
        elif additional_info is None and status == "SNMP DOWN":
            additional_info = "Host está ONLINE mas SNMP FALHOU."
        elif additional_info is None and status == "DOWN":
            additional_info = "Host está OFFLINE."

        try:
            # Criar payload do webhook
            payload = self._create_alert_payload(
                endpoint_name, endpoint_ip, status, timestamp, additional_info
            )
            
            # Enviar webhook com retry
            success = self._send_webhook_with_retry(url, payload)
            
            if success:
                logger.info(f"Alert webhook sent successfully")
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
        Cria o payload JSON para webhook de alerta usando embeds ricos do Discord
        """
        # Determinar cor e emoji baseado no status
        if status == "SNMP DOWN":
            color = 0xfd7e14  # Laranja
            emoji = "🟠"
        elif status == "UP":
            color = 0x28a745  # Verde
            emoji = "🟢"
        elif status == "DOWN":
            color = 0xdc3545  # Vermelho
            emoji = "🔴"
        else:
            color = 0x6c757d  # Cinza
            emoji = "⚪"

        # Cria embed rico para Discord
        embed = {
            "title": f"{emoji} InfraWatch Alert - {status}",
            "description": f"Alerta de monitoramento para **{endpoint_name}**",
            "color": color,
            "timestamp": self._format_timestamp_for_discord(timestamp),
            "fields": [
                {
                    "name": "📍 Endpoint",
                    "value": endpoint_name,
                    "inline": True
                },
                {
                    "name": "🌐 IP/Host",
                    "value": endpoint_ip,
                    "inline": True
                },
                {
                    "name": "📊 Status",
                    "value": f"`{status}`",
                    "inline": True
                },
                {
                    "name": "🕐 Timestamp",
                    "value": self._format_timestamp_for_display(timestamp),
                    "inline": False
                }
            ],
            "footer": {
                "text": "InfraWatch - Sistema de Monitoramento",
                "icon_url": "https://cdn-icons-png.flaticon.com/512/2784/2784403.png"
            },
            "thumbnail": {
                "url": "https://cdn-icons-png.flaticon.com/512/1570/1570647.png"
            }
        }
        
        # Adiciona informações extras se fornecidas
        if additional_info:
            embed["fields"].append({
                "name": "ℹ️ Informações Adicionais",
                "value": additional_info,
                "inline": False
            })

        payload = {
            "username": "InfraWatch Alert Bot",
            "avatar_url": "https://cdn-icons-png.flaticon.com/512/1182/1182718.png",
            "embeds": [embed]
        }

        return payload

    def _create_system_status_payload(
        self,
        system_status: Dict[str, Any],
        timestamp: datetime
    ) -> Dict[str, Any]:
        """
        Cria o payload JSON para status do sistema usando embeds ricos do Discord
        """
        total_endpoints = system_status.get("total_endpoints", 0)
        up_endpoints = system_status.get("up_endpoints", 0)
        down_endpoints = system_status.get("down_endpoints", 0)
        snmp_down_endpoints = system_status.get("snmp_down_endpoints", 0)
        
        # Determinar status geral
        if down_endpoints == 0 and snmp_down_endpoints == 0:
            overall_status = "healthy"
            color = 0x28a745  # Verde
            emoji = "✅"
        elif down_endpoints > 0:
            overall_status = "critical"
            color = 0xdc3545  # Vermelho
            emoji = "❌"
        else:
            overall_status = "warning"
            color = 0xfd7e14  # Laranja
            emoji = "⚠️"

        # Cria embed rico para Discord
        embed = {
            "title": f"{emoji} InfraWatch System Status",
            "description": f"Relatório de status geral do sistema - **{overall_status.upper()}**",
            "color": color,
            "timestamp": self._format_timestamp_for_discord(timestamp),
            "fields": [
                {
                    "name": "📊 Total de Endpoints",
                    "value": str(total_endpoints),
                    "inline": True
                },
                {
                    "name": "🟢 UP",
                    "value": str(up_endpoints),
                    "inline": True
                },
                {
                    "name": "🔴 DOWN",
                    "value": str(down_endpoints),
                    "inline": True
                },
                {
                    "name": "🟠 SNMP DOWN",
                    "value": str(snmp_down_endpoints),
                    "inline": True
                },
                {
                    "name": "🕐 Timestamp",
                    "value": self._format_timestamp_for_display(timestamp),
                    "inline": True
                },
                {
                    "name": "📈 Status Geral",
                    "value": f"`{overall_status.upper()}`",
                    "inline": True
                }
            ],
            "footer": {
                "text": "InfraWatch - Sistema de Monitoramento",
                "icon_url": "https://cdn-icons-png.flaticon.com/512/2784/2784403.png"
            },
            "thumbnail": {
                "url": "https://cdn-icons-png.flaticon.com/512/3079/3079003.png"
            }
        }

        # Adicionar informações extras se disponíveis
        if "uptime" in system_status:
            embed["fields"].append({
                "name": "⏱️ Uptime",
                "value": system_status["uptime"],
                "inline": True
            })
        
        if "last_check" in system_status:
            embed["fields"].append({
                "name": "🔍 Última Verificação",
                "value": system_status["last_check"],
                "inline": True
            })

        payload = {
            "username": "InfraWatch System",
            "avatar_url": "https://cdn-icons-png.flaticon.com/512/1182/1182718.png",
            "embeds": [embed]
        }

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
        Testa a conexão com o webhook enviando uma mensagem de teste usando embeds ricos
        """
        test_url = webhook_url or self.webhook_url
        
        if not test_url:
            logger.error("No webhook URL to test")
            return False
        
        try:
            # Obter timestamp único para usar em todo o embed
            current_time = datetime.now()
            
            # Cria embed rico para teste de conexão
            embed = {
                "title": "🔧 InfraWatch Connection Test",
                "description": "Teste de conexão do serviço de webhook",
                "color": 0x007bff,  # Azul
                "timestamp": self._format_timestamp_for_discord(current_time),
                "fields": [
                    {
                        "name": "🕐 Timestamp",
                        "value": self._format_timestamp_for_display(current_time),
                        "inline": True
                    },
                    {
                        "name": "✅ Status",
                        "value": "`Connection test successful!`",
                        "inline": True
                    },
                    {
                        "name": "🛠️ Service",
                        "value": "InfraWatch Webhook Service",
                        "inline": False
                    }
                ],
                "footer": {
                    "text": "Se você recebeu esta mensagem, o webhook está funcionando corretamente!",
                    "icon_url": "https://cdn-icons-png.flaticon.com/512/2784/2784403.png"
                },
                "thumbnail": {
                    "url": "https://cdn-icons-png.flaticon.com/512/1828/1828833.png"
                }
            }

            test_payload = {
                "username": "InfraWatch Test",
                "avatar_url": "https://cdn-icons-png.flaticon.com/512/1182/1182718.png",
                "embeds": [embed]
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


if __name__ == "__main__":
    webhook_service = WebhookService()
    webhook_service.test_connection()

