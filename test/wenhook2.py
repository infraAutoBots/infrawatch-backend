import requests
import json
from datetime import datetime
import time

# ===== CONFIGURAÇÕES DE WEBHOOK =====
# Configurações agora são passadas dinamicamente

# EXEMPLOS DE USO:

# Para Telegram:
# webhook_config = WebhookConfig(
#     webhook_type="telegram",
#     bot_token="SEU_BOT_TOKEN",
#     chat_id="SEU_CHAT_ID"
# )

# Para Discord:
# webhook_config = WebhookConfig(
#     webhook_type="discord",
#     webhook_url="https://discord.com/api/webhooks/SEU_ID/SEU_TOKEN"
# )

# Para Slack:
# webhook_config = WebhookConfig(
#     webhook_type="slack",
#     webhook_url="https://hooks.slack.com/services/SEU/SLACK/WEBHOOK"
# )

class WebhookConfig:
    def __init__(self, webhook_type: str, webhook_url: str = None, **kwargs):
        self.webhook_type = webhook_type
        self.webhook_url = webhook_url
        self.config = kwargs
        
    def get_telegram_url(self, bot_token: str):
        """Constrói URL do Telegram dinamicamente"""
        return f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    def validate_config(self):
        """Valida se a configuração está completa"""
        if self.webhook_type == "telegram":
            if not self.config.get("bot_token") or not self.config.get("chat_id"):
                raise ValueError("Telegram requer 'bot_token' e 'chat_id'")
            self.webhook_url = self.get_telegram_url(self.config["bot_token"])
        elif not self.webhook_url:
            raise ValueError(f"webhook_url é obrigatório para tipo {self.webhook_type}")
        return True

def criar_payload_discord(hora_formatada):
    """Cria payload específico para Discord"""
    return {
        "content": f"🕐 **Hora atual do sistema:** {hora_formatada}",
        "username": "TimeBot",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/2784/2784403.png"
    }

def criar_payload_slack(hora_formatada):
    """Cria payload específico para Slack"""
    return {
        "text": f"🕐 Hora atual do sistema: {hora_formatada}",
        "username": "TimeBot",
        "icon_emoji": ":clock1:"
    }

def criar_payload_teams(hora_formatada):
    """Cria payload específico para Microsoft Teams"""
    return {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "summary": "Hora Atual",
        "themeColor": "0078D4",
        "sections": [{
            "activityTitle": "🕐 TimeBot",
            "activitySubtitle": f"Hora atual do sistema: {hora_formatada}",
            "markdown": True
        }]
    }

def criar_payload_telegram(hora_formatada, config):
    """Cria payload específico para Telegram"""
    return {
        "chat_id": config.get("chat_id"),
        "text": f"🕐 *Hora atual do sistema:* {hora_formatada}",
        "parse_mode": "Markdown"
    }

def criar_payload_generico(hora_formatada):
    """Cria payload genérico para qualquer webhook"""
    return {
        "timestamp": datetime.now().isoformat(),
        "message": f"Hora atual do sistema: {hora_formatada}",
        "source": "TimeBot",
        "data": {
            "formatted_time": hora_formatada,
            "unix_timestamp": int(datetime.now().timestamp())
        }
    }

def obter_payload_por_tipo(webhook_config, hora_formatada):
    """Retorna o payload correto baseado no tipo de webhook"""
    webhook_type = webhook_config.webhook_type
    config = webhook_config.config
    
    payloads = {
        "discord": criar_payload_discord(hora_formatada),
        "slack": criar_payload_slack(hora_formatada),
        "teams": criar_payload_teams(hora_formatada),
        "telegram": criar_payload_telegram(hora_formatada, config),
        "generic": criar_payload_generico(hora_formatada)
    }
    
    return payloads.get(webhook_type, criar_payload_generico(hora_formatada))

def obter_headers_por_tipo(webhook_type):
    """Retorna os headers corretos baseado no tipo de webhook"""
    headers_base = {"Content-Type": "application/json"}
    
    # Teams às vezes precisa de headers específicos
    if webhook_type == "teams":
        headers_base["User-Agent"] = "TimeBot/1.0"
    
    return headers_base

def enviar_hora_atual(webhook_config):
    """
    Função universal que pega a hora atual e envia para qualquer webhook
    """
    # Valida a configuração
    webhook_config.validate_config()
    
    # Obtém a hora atual do sistema
    hora_atual = datetime.now()
    
    # Formata a data e hora de forma legível
    hora_formatada = hora_atual.strftime("%d/%m/%Y às %H:%M:%S")
    
    # Cria o payload baseado no tipo de webhook
    payload = obter_payload_por_tipo(webhook_config, hora_formatada)
    
    # Obtém os headers corretos
    headers = obter_headers_por_tipo(webhook_config.webhook_type)
    
    try:
        # Envia a requisição POST para o webhook
        response = requests.post(
            webhook_config.webhook_url, 
            data=json.dumps(payload), 
            headers=headers,
            timeout=10  # Timeout de 10 segundos
        )
        
        # Códigos de sucesso por plataforma
        codigos_sucesso = {
            "discord": [200, 204],
            "slack": [200],
            "teams": [200],
            "telegram": [200],
            "generic": [200, 201, 202, 204]
        }
        
        # Verifica se a requisição foi bem-sucedida
        if response.status_code in codigos_sucesso.get(webhook_config.webhook_type, [200]):
            print(f"✅ Mensagem enviada com sucesso para {webhook_config.webhook_type.upper()}!")
            print(f"   Hora: {hora_formatada}")
            print(f"   Status: {response.status_code}")
        else:
            print(f"❌ Erro ao enviar mensagem para {webhook_config.webhook_type.upper()}")
            print(f"   Status: {response.status_code}")
            print(f"   Resposta: {response.text}")
            
    except requests.exceptions.Timeout:
        print(f"❌ Timeout na requisição para {webhook_config.webhook_type.upper()}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição para {webhook_config.webhook_type.upper()}: {e}")

def webhook_automatico(webhook_config, intervalo_minutos=1):
    """
    Executa o webhook automaticamente em intervalos regulares
    
    Args:
        webhook_config (WebhookConfig): Configuração do webhook
        intervalo_minutos (int): Intervalo em minutos entre cada envio
    """
    print(f"🚀 Iniciando webhook automático para {webhook_config.webhook_type.upper()}")
    print(f"   Intervalo: {intervalo_minutos} minuto(s)")
    print("   Pressione Ctrl+C para parar")
    print()
    
    try:
        while True:
            enviar_hora_atual(webhook_config)
            print(f"   Próximo envio em {intervalo_minutos} minuto(s)...")
            print("-" * 50)
            time.sleep(intervalo_minutos * 60)  # Converte minutos para segundos
    except KeyboardInterrupt:
        print("\n⏹️ Webhook automático interrompido pelo usuário")

def testar_webhook(webhook_config):
    """
    Testa se o webhook está funcionando corretamente
    """
    print(f"🧪 Testando webhook {webhook_config.webhook_type.upper()}...")
    print(f"   URL: {webhook_config.webhook_url[:50]}...")
    print()
    
    # Testa com uma mensagem de teste
    payload_teste = obter_payload_por_tipo(webhook_config, "TESTE - " + datetime.now().strftime("%H:%M:%S"))
    headers = obter_headers_por_tipo(webhook_config.webhook_type)
    
    try:
        response = requests.post(webhook_config.webhook_url, data=json.dumps(payload_teste), headers=headers, timeout=10)
        
        if response.status_code in [200, 201, 202, 204]:
            print("✅ Webhook funcionando corretamente!")
            return True
        else:
            print(f"❌ Webhook retornou status {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar webhook: {e}")
        return False

def listar_webhooks_suportados():
    """Lista todos os tipos de webhook suportados"""
    webhooks = {
        "discord": "Discord - Para servidores Discord",
        "slack": "Slack - Para workspaces Slack",
        "teams": "Microsoft Teams - Para canais do Teams",
        "telegram": "Telegram - Para bots do Telegram",
        "generic": "Genérico - Para qualquer webhook que aceita JSON"
    }
    
    print("🔗 WEBHOOKS SUPORTADOS:")
    print()
    for tipo, descricao in webhooks.items():
        print(f"   📌 {tipo.upper()}: {descricao}")
    print()

def criar_webhook_interativo():
    """Cria configuração de webhook de forma interativa"""
    print("🛠️ CONFIGURAR WEBHOOK")
    print("=" * 40)
    
    # Escolher tipo
    tipos_disponiveis = ["discord", "slack", "teams", "telegram", "generic"]
    print("Tipos disponíveis:")
    for i, tipo in enumerate(tipos_disponiveis, 1):
        print(f"   {i}. {tipo.upper()}")
    
    try:
        escolha = int(input("\nEscolha o tipo (1-5): ")) - 1
        webhook_type = tipos_disponiveis[escolha]
    except (ValueError, IndexError):
        print("❌ Escolha inválida!")
        return None
    
    # Configurações específicas por tipo
    if webhook_type == "telegram":
        print("\n📱 Configuração do Telegram:")
        bot_token = input("Digite o token do bot: ").strip()
        chat_id = input("Digite o chat ID: ").strip()
        
        if not bot_token or not chat_id:
            print("❌ Token e chat ID são obrigatórios!")
            return None
            
        return WebhookConfig(
            webhook_type="telegram",
            bot_token=bot_token,
            chat_id=chat_id
        )
    
    else:
        webhook_url = input(f"\n🔗 Digite a URL do webhook {webhook_type.upper()}: ").strip()
        
        if not webhook_url:
            print("❌ URL é obrigatória!")
            return None
            
        return WebhookConfig(
            webhook_type=webhook_type,
            webhook_url=webhook_url
        )

if __name__ == "__main__":
    print("=" * 60)
    print("        WEBHOOK UNIVERSAL - HORA ATUAL")
    print("=" * 60)
    print()
    
    # Criar configuração de webhook
    webhook_config = criar_webhook_interativo()
    
    if not webhook_config:
        print("❌ Configuração cancelada!")
        exit(1)
    
    try:
        webhook_config.validate_config()
    except ValueError as e:
        print(f"❌ Erro na configuração: {e}")
        exit(1)
    
    # Mostra informações do webhook atual
    print(f"🎯 Webhook ativo: {webhook_config.webhook_type.upper()}")
    print(f"🔗 URL: {webhook_config.webhook_url[:50]}...")
    print()
    
    # Menu de opções
    print("Escolha uma opção:")
    print("1 - Testar webhook")
    print("2 - Enviar hora atual uma vez")
    print("3 - Enviar automaticamente a cada minuto")
    print("4 - Enviar automaticamente com intervalo personalizado")
    print("5 - Listar webhooks suportados")
    
    try:
        opcao = input("\nDigite sua opção (1-5): ").strip()
        print()
        
        if opcao == "1":
            testar_webhook(webhook_config)
            
        elif opcao == "2":
            enviar_hora_atual(webhook_config)
            
        elif opcao == "3":
            webhook_automatico(webhook_config, 1)
            
        elif opcao == "4":
            intervalo = int(input("Digite o intervalo em minutos: "))
            if intervalo <= 0:
                print("❌ Intervalo deve ser maior que zero!")
            else:
                webhook_automatico(webhook_config, intervalo)
                
        elif opcao == "5":
            listar_webhooks_suportados()
            
        else:
            print("❌ Opção inválida!")
            
    except KeyboardInterrupt:
        print("\n👋 Programa encerrado pelo usuário")
    except ValueError:
        print("❌ Por favor, digite um número válido")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")