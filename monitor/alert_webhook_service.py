import requests
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
import logging
from dependencies import init_session
from sqlalchemy.orm import Session
from models import WebHookConfig



logger = logging.getLogger(__name__)


class WebhookService:
    def __init__(self):
        """
        Inicializa o serviço de webhook.
        Configurações podem ser obtidas de variáveis de ambiente ou banco de dados.
        """
        # Configurações básicas (podem ser sobrescritas pelo banco de dados)
        # Tenta obter o primeiro webhook configurado no banco de dados
        self.list_config_email: List = []
        self.session = init_session
        self._load_config_from_db()

    def _load_config_from_db(self):
        """
        Carrega configurações de webhook do banco de dados
        """

        session: Session = self.session()
        config: Dict = {}
        headers = {"Content-Type": "application/json",
                    "User-Agent": "InfraWatch-Monitor/1.0"}
        db_webhooks = session.query(WebHookConfig).filter(WebHookConfig.active == True).all()
        for db_webhook in db_webhooks:
            config['webhook_url'] = db_webhook.url
            config['timeout'] = db_webhook.timeout
            config['retry_attempts'] = 3
            if db_webhook.access_token:
                    headers["Authorization"] = f"Bearer {db_webhook.access_token}"
            config['headers'] = headers
            self.list_config_email.append(config)
        session.close()

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
        endpoint_name: str,
        endpoint_ip: str,
        status: str,
        timestamp: datetime,
        additional_info: Optional[str] = None
    ) -> bool:
        """
        Envia webhook de alerta para mudança de status de endpoint
        """

        self._load_config_from_db()

        if additional_info is None and status == "UP":
            additional_info = "Host restaurado com sucesso. Conectividade normalizada."
        elif additional_info is None and status == "SNMP DOWN":
            additional_info = "Host está ONLINE mas SNMP FALHOU."
        elif additional_info is None and status == "DOWN":
            additional_info = "Host está OFFLINE."

        try:
            # Criar payload do webhook
            for config in self.list_config_email:
                url = config['webhook_url']
                timeout = config.get('timeout', 30)
                retry_attempts = config.get('retry_attempts', 3)
                headers = config.get('headers')
    
                payload = self._create_alert_payload(
                    endpoint_name, endpoint_ip, status, timestamp, additional_info
                )
                
                # Enviar webhook com retry
                success = self._send_webhook_with_retry(url, payload, headers=headers, timeout=timeout, retry_attempts=retry_attempts)

                if success:
                    logger.info(f"Alert webhook sent successfully")
                else:
                    logger.error(f"Failed to send alert webhook to {url}")
                
                return success
            
        except Exception as e:
            logger.error(f"Failed to send alert webhook: {e}")
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

    def _send_webhook_with_retry(self, url: str, payload: Dict[str, Any], headers: Dict[str, str], timeout: int, retry_attempts: int) -> bool:
        """
        Envia webhook com tentativas de retry
        """
        for attempt in range(retry_attempts):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=timeout
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

    def send_system_status_webhook(
        self,
        system_status: Dict[str, Any],
        timestamp: datetime
    ) -> bool:
        """
        Envia webhook com status geral do sistema de monitoramento
        """
        self._load_config_from_db()

        try:
            for config in self.list_config_email:
                url = config['webhook_url']
                timeout = config.get('timeout', 30)
                retry_attempts = config.get('retry_attempts', 3)
                headers = config.get('headers')

                payload = self._create_system_status_payload(system_status, timestamp)

                success = self._send_webhook_with_retry(url, payload, headers=headers, timeout=timeout, retry_attempts=retry_attempts)

                if success:
                    logger.info(f"System status webhook sent successfully to {url}")
                else:
                    logger.error(f"Failed to send system status webhook to {url}")

                return success

        except Exception as e:
            logger.error(f"Failed to send system status webhook: {e}")
            return False

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

    def test_connection(self) -> bool:
        """
        Testa a conexão com o webhook enviando uma mensagem de teste usando embeds ricos
        """
        self._load_config_from_db()

        try:
            current_time = datetime.now()

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

            for config in self.list_config_email:
                url = config['webhook_url']
                timeout = config.get('timeout', 30)
                retry_attempts = config.get('retry_attempts', 3)
                headers = config.get('headers')

                success = self._send_webhook_with_retry(url, test_payload, headers=headers, timeout=timeout, retry_attempts=retry_attempts)

                if success:
                    logger.info(f"Webhook connection test successful: {url}")
                else:
                    logger.error(f"Webhook connection test failed: {url}")

                return success

        except Exception as e:
            logger.error(f"Webhook connection test failed: {e}")
            return False

        def get_status(self) -> List[Dict[str, Any]]:
            """
            Retorna o status atual do serviço de webhook
            """
            return self.list_config_email


if __name__ == "__main__":
    webhook_service = WebhookService()
    webhook_service.test_connection()

