import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_username)
        self.enabled = os.getenv("EMAIL_ALERTS_ENABLED", "false").lower() == "true"
        
        if not all([self.smtp_username, self.smtp_password]) and self.enabled:
            logger.warning("Email credentials not configured. Email alerts will be disabled.")
            self.enabled = False

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
        status_color = "#dc3545" if status == "DOWN" else "#28a745"  # Vermelho para DOWN, Verde para UP
        status_icon = "🔴" if status == "DOWN" else "🟢"
        
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