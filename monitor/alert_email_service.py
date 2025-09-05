import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Optional
from models import EmailConfig, Users
from dependencies import init_session
import logging


logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        """
        Inicializa o serviço de email.
        Se session for fornecida, tentará obter configurações do banco.
        Caso contrário, usará variáveis de ambiente como fallback.
        """
        self.session = init_session
        
        # Inicializar valores padrão
        self.smtp_server = None
        self.smtp_port = None
        self.smtp_username = None
        self.from_email = None
        self.smtp_password = None
        self.to_emails = ""
        
        self._load_config_from_db()
        logger.info(f"Email recipients configured: {self.to_emails}")
        
    def _load_config_from_db(self):
        """
        Carrega configurações de email do banco de dados
        """
        if not self.session:
            return
        try:
            
            # Buscar configuração ativa
            session = self.session()
            email_config = session.query(EmailConfig).first()

            list_active_emails = []
            active_users = session.query(Users).filter(Users.alert == True).all()
            for user in active_users:
                list_active_emails.append(user.email)

            if email_config:
                self.smtp_server = email_config.server
                self.smtp_port = email_config.port
                self.smtp_username = email_config.email
                self.from_email = email_config.email
                self.smtp_password = email_config.password
                self.to_emails = ",".join(list_active_emails) if list_active_emails else None

                logger.info(f"Email configuration loaded from database: {email_config.email}")
                logger.info(f"Active email recipients: {len(list_active_emails)}")
            else:
                logger.error("No active email configuration found in database")
                return
                
            session.close()
                
        except Exception as e:
            logger.warning(f"Failed to load email config from database: {e}")

    def send_alert_email(
        self,
        subject: str, 
        endpoint_name: str,
        endpoint_ip: str,
        status: str,
        timestamp: datetime,
        additional_info: Optional[str] = None
    ) -> bool:
        """
        Envia email de alerta para mudança de status de endpoint
        """
        self._load_config_from_db()
        
        # Verificações detalhadas
        if not self.to_emails:
            logger.error("No recipient emails configured")
            return False
            
        if not all([self.smtp_server, self.smtp_port, self.smtp_username, self.smtp_password]):
            logger.error("Incomplete SMTP configuration. Missing: " + 
                        ", ".join([
                            "server" if not self.smtp_server else "",
                            "port" if not self.smtp_port else "",
                            "username" if not self.smtp_username else "",
                            "password" if not self.smtp_password else ""
                        ]).strip(", "))
            return False
            
        try:
            # Criar mensagem
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = self.to_emails 
            msg['Subject'] = subject
            
            # Corpo do email
            body = self._create_alert_body(
                endpoint_name, endpoint_ip, status, timestamp, additional_info
            )
            
            msg.attach(MIMEText(body, 'html'))

            # Enviar email
            logger.info(f"Attempting to send email to: {self.to_emails}")
            logger.info(f"Using SMTP: {self.smtp_server}:{self.smtp_port}")
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                result = server.send_message(msg)
                
                if result:
                    logger.warning(f"Some recipients failed: {result}")
                else:
                    logger.info("Email sent successfully to all recipients")

            logger.info(f"Alert email sent successfully to {self.to_emails}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication failed: {e}")
            return False
        except smtplib.SMTPConnectError as e:
            logger.error(f"SMTP Connection failed: {e}")
            return False
        except smtplib.SMTPServerDisconnected as e:
            logger.error(f"SMTP Server disconnected: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to send alert email: {e}")
            return False

    def _create_alert_body(
        self, 
        endpoint_name: str, 
        endpoint_ip: str, 
        status: str, 
        timestamp: datetime,
        additional_info: Optional[str] = None
    ) -> str:
        """
        Cria o corpo do email de alerta
        """
        if status == "SNMP DOWN":
            status_color = "#fd7e14"  # Laranja para None
            status_icon = "🟠"
        elif status == "UP":
            status_color = "#28a745"  # Verde para True
            status_icon = "🟢"
        elif status == "DOWN":
            status_color = "#dc3545"  # Vermelho para False
            status_icon = "🔴"
        else:
            status_color = "#6c757d"  # Cinza para outros casos
            status_icon = "⚪"

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="background-color: {status_color}; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                    <h1 style="margin: 0; font-size: 24px;">
                        {status_icon} InfraWatch Alert - {status}
                    </h1>
                </div>
                
                <div style="padding: 30px;">
                    <h2 style="color: #333; margin-top: 0;">Detalhes do Alerta</h2>
                    
                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold; width: 30%;">
                                Endpoint:
                            </td>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;">
                                {endpoint_name}
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">
                                IP/Host:
                            </td>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;">
                                {endpoint_ip}
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">
                                Status:
                            </td>
                            <td style="padding: 10px; border-bottom: 1px solid #eee; color: {status_color}; font-weight: bold;">
                                {status}
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">
                                Timestamp:
                            </td>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;">
                                {timestamp.strftime('%d/%m/%Y %H:%M:%S')}
                            </td>
                        </tr>
                    </table>
                    
                    {f'<div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;"><strong>Informações Adicionais:</strong><br>{additional_info}</div>' if additional_info else ''}
                    
                    <div style="margin-top: 30px; padding: 20px; background-color: #e9ecef; border-radius: 5px; text-align: center;">
                        <p style="margin: 0; color: #6c757d; font-size: 14px;">
                            Este é um alerta automático do sistema InfraWatch.<br>
                            Para mais detalhes, acesse o dashboard de monitoramento.
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return body

    def test_connection(self) -> bool:
        """
        Testa a conexão SMTP
        """

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
            logger.info("SMTP connection test successful")
            return True
        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            return False

    def get_status(self) -> dict:
        """
        Retorna o status atual do serviço de email
        """
        # Contar emails ativos
        active_email_count = 0
        if self.session:
            try:
                session = self.session()
                active_email_count = session.query(Users).filter(Users.alert == True).count()
                session.close()
            except Exception as e:
                logger.warning(f"Failed to count active emails: {e}")
        
        return {
            "smtp_server": self.smtp_server,
            "smtp_port": self.smtp_port,
            "from_email": self.from_email,
            "has_credentials": bool(self.smtp_username and self.smtp_password),
            "active_email_count": active_email_count,
            "configured_emails": self.to_emails
        }


if __name__ == "__main__":
    # Teste rápido do serviço de email
    email_service = EmailService()
    email_service.send_alert_email(
        subject="Teste de Alerta - InfraWatch",
        endpoint_name="Servidor de Teste",
        endpoint_ip="192.168.1.1",
        status="UP",
        timestamp=datetime.now()
    )
    
