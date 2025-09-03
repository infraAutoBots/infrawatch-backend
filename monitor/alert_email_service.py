import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Optional
import logging



logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self, db_session=None):
        """
        Inicializa o serviço de email.
        Se db_session for fornecida, tentará obter configurações do banco.
        Caso contrário, usará variáveis de ambiente como fallback.
        """
        self.db_session = db_session
        
        # Configurações padrão (fallback)
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_username)
        self.enabled = os.getenv("EMAIL_ALERTS_ENABLED", "false").lower() == "true"
        
        # Tentar obter configurações do banco de dados
        self._load_config_from_db()
        
        if not all([self.smtp_username, self.smtp_password]) and self.enabled:
            logger.warning("Email credentials not configured. Email alerts will be disabled.")
            self.enabled = False

    def _load_config_from_db(self):
        """
        Carrega configurações de email do banco de dados
        """
        if not self.db_session:
            return
        
        try:
            from models import EmailConfig
            from encryption import bcrypt_context
            
            # Buscar configuração ativa
            email_config = self.db_session.query(EmailConfig).filter(
                EmailConfig.active == True
            ).first()
            
            if email_config:
                self.smtp_server = email_config.server
                self.smtp_port = email_config.port
                self.smtp_username = email_config.email
                self.from_email = email_config.email
                
                # A senha está criptografada no banco, mas para SMTP precisamos da senha real
                # Por segurança, vamos manter as senhas em variáveis de ambiente
                # e usar o banco apenas para outros dados
                if not self.smtp_password:
                    logger.warning("Email password not found in environment variables")
                
                self.enabled = True
                logger.info(f"Email configuration loaded from database: {email_config.email}")
            else:
                logger.info("No active email configuration found in database, using environment variables")
                
        except Exception as e:
            logger.warning(f"Failed to load email config from database: {e}")

    def get_admin_emails(self) -> List[str]:
        """
        Obtém lista de emails de administradores do banco de dados
        """
        if not self.db_session:
            # Fallback para variável de ambiente ou email padrão
            default_emails = os.getenv("ADMIN_EMAILS", "").split(",")
            return [email.strip() for email in default_emails if email.strip()]
        
        try:
            from models import Users
            
            # Buscar usuários com nível ADMIN
            admin_users = self.db_session.query(Users).filter(
                Users.access_level == "ADMIN",
                Users.state == True  # Apenas usuários ativos
            ).all()
            
            admin_emails = [user.email for user in admin_users if user.email]
            logger.info(f"Found {len(admin_emails)} admin emails")
            
            return admin_emails
            
        except Exception as e:
            logger.error(f"Failed to get admin emails: {e}")
            return []

    def send_alert_to_admins(
        self,
        subject: str,
        endpoint_name: str,
        endpoint_ip: str,
        status: str,
        timestamp: datetime,
        additional_info: Optional[str] = None
    ) -> bool:
        """
        Envia alerta por email para todos os administradores
        """
        admin_emails = self.get_admin_emails()
        
        if not admin_emails:
            logger.warning("No admin emails found to send alert")
            return False
        
        return self.send_alert_email(
            to_emails=admin_emails,
            subject=subject,
            endpoint_name=endpoint_name,
            endpoint_ip=endpoint_ip,
            status=status,
            timestamp=timestamp,
            additional_info=additional_info
        )

    def send_alert_email(
        self, 
        to_emails: List[str], 
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
        if not self.enabled:
            logger.info(f"Email alerts disabled. Would send: {subject} to {to_emails}")
            return True
        try:
            # Criar mensagem
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = ", ".join(to_emails)
            msg['Subject'] = subject
            
            # Corpo do email
            body = self._create_alert_body(
                endpoint_name, endpoint_ip, status, timestamp, additional_info
            )
            
            msg.attach(MIMEText(body, 'html'))

            # Enviar email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Alert email sent successfully to {to_emails}")
            return True
            
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
        if not self.enabled:
            logger.info("Email service is disabled")
            return False
            
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
            logger.info("SMTP connection test successful")
            return True
        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            return False

    def reload_config_from_db(self):
        """
        Recarrega configurações do banco de dados
        """
        self._load_config_from_db()

    def set_enabled(self, enabled: bool):
        """
        Habilita ou desabilita o serviço de email
        """
        if enabled and not all([self.smtp_username, self.smtp_password]):
            logger.warning("Cannot enable email service without credentials")
            return False
        
        self.enabled = enabled
        return True

    def get_status(self) -> dict:
        """
        Retorna o status atual do serviço de email
        """
        return {
            "enabled": self.enabled,
            "smtp_server": self.smtp_server,
            "smtp_port": self.smtp_port,
            "from_email": self.from_email,
            "has_credentials": bool(self.smtp_username and self.smtp_password),
            "admin_count": len(self.get_admin_emails()) if self.db_session else 0
        }