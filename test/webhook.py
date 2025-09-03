import requests
import json
from datetime import datetime
import time

# URL do webhook do Discord (substitua pela sua URL)
WEBHOOK_URL = "https://discord.com/api/webhooks/1412595075099136141/WP7CfeZ4saW39XoaDb17WrgLwhNw49r3_ufGg-wOj6dTWYmSE4A019AXLyRLtRCp5jjX"

def get_status_info(status):
    """Retorna informações de cor e emoji baseado no status"""
    if status == "SNMP DOWN":
        return {"color": 0xfd7e14, "icon": "🟠", "hex": "#fd7e14"}  # Laranja
    elif status == "UP":
        return {"color": 0x28a745, "icon": "🟢", "hex": "#28a745"}  # Verde
    elif status == "DOWN":
        return {"color": 0xdc3545, "icon": "🔴", "hex": "#dc3545"}  # Vermelho
    else:
        return {"color": 0x6c757d, "icon": "⚪", "hex": "#6c757d"}  # Cinza

def enviar_alerta_infrawatch(endpoint_name, endpoint_ip, status, timestamp=None, additional_info=None):
    """
    Envia alerta estruturado do InfraWatch via webhook do Discord
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    status_info = get_status_info(status)
    
    # Cria embed rico para Discord
    embed = {
        "title": f"{status_info['icon']} InfraWatch Alert - {status}",
        "description": f"Alerta de monitoramento para **{endpoint_name}**",
        "color": status_info["color"],
        "timestamp": timestamp.isoformat(),
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
                "value": timestamp.strftime('%d/%m/%Y %H:%M:%S'),
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
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/1570/1570647.png",
        "embeds": [embed]
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(WEBHOOK_URL, data=json.dumps(payload), headers=headers)
        
        if response.status_code == 204:
            print(f"✅ Alerta InfraWatch enviado com sucesso!")
            print(f"   Endpoint: {endpoint_name} ({endpoint_ip})")
            print(f"   Status: {status}")
        else:
            print(f"❌ Erro ao enviar alerta. Status: {response.status_code}")
            print(f"   Resposta: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")

def enviar_hora_atual():
    """
    Função que pega a hora atual e envia para o Discord via webhook
    """
    # Obtém a hora atual do sistema
    hora_atual = datetime.now()
    
    # Formata a data e hora de forma legível
    hora_formatada = hora_atual.strftime("%d/%m/%Y às %H:%M:%S")
    
    # Cria o payload (dados) que será enviado
    payload = {
        "content": f"🕐 **Hora atual do sistema:** {hora_formatada}",
        "username": "TimeBot",  # Nome que aparecerá como remetente
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/2784/2784403.png"  # Ícone do bot
    }
    
    # Converte o payload para JSON
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        # Envia a requisição POST para o webhook
        response = requests.post(
            WEBHOOK_URL, 
            data=json.dumps(payload), 
            headers=headers
        )
        
        # Verifica se a requisição foi bem-sucedida
        if response.status_code == 204:
            print(f"✅ Mensagem enviada com sucesso! Hora: {hora_formatada}")
        else:
            print(f"❌ Erro ao enviar mensagem. Status: {response.status_code}")
            print(f"Resposta: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")

def testar_alertas_infrawatch():
    """Testa diferentes tipos de alerta do InfraWatch"""
    print("🧪 Testando alertas do InfraWatch...")
    
    # Teste 1: Host DOWN
    print("\n1. Testando alerta HOST DOWN...")
    enviar_alerta_infrawatch(
        endpoint_name="Servidor Web Principal",
        endpoint_ip="192.168.1.100",
        status="DOWN",
        additional_info="Falha consecutiva de ping detectada. Host não responde há 5 minutos."
    )
    
    time.sleep(2)  # Pausa entre os testes
    
    # Teste 2: SNMP DOWN
    print("\n2. Testando alerta SNMP DOWN...")
    enviar_alerta_infrawatch(
        endpoint_name="Switch Core",
        endpoint_ip="10.0.0.1",
        status="SNMP DOWN",
        additional_info="Host responde ao ping mas SNMP não está acessível."
    )
    
    time.sleep(2)
    
    # Teste 3: Host UP
    print("\n3. Testando alerta HOST UP...")
    enviar_alerta_infrawatch(
        endpoint_name="Servidor Web Principal",
        endpoint_ip="192.168.1.100",
        status="UP",
        additional_info="Host restaurado com sucesso. Conectividade normalizada."
    )
    
    print("\n✅ Testes de alerta concluídos!")

def webhook_automatico(intervalo_minutos=1):
    """
    Executa o webhook automaticamente em intervalos regulares
    
    Args:
        intervalo_minutos (int): Intervalo em minutos entre cada envio
    """
    print(f"🚀 Iniciando webhook automático (intervalo: {intervalo_minutos} minuto(s))")
    print("Pressione Ctrl+C para parar")
    
    try:
        while True:
            enviar_hora_atual()
            time.sleep(intervalo_minutos * 60)  # Converte minutos para segundos
    except KeyboardInterrupt:
        print("\n⏹️ Webhook automático interrompido pelo usuário")

if __name__ == "__main__":
    print("=== WEBHOOK DISCORD - INFRAWATCH ALERTS ===")
    print()
    
    # Opções de execução
    print("Escolha uma opção:")
    print("1 - Enviar hora atual uma vez")
    print("2 - Enviar automaticamente a cada minuto")
    print("3 - Enviar automaticamente com intervalo personalizado")
    print("4 - 🆕 Testar alertas do InfraWatch")
    print("5 - 🆕 Enviar alerta personalizado")
    
    try:
        opcao = input("\nDigite sua opção (1-5): ").strip()
        
        if opcao == "1":
            enviar_hora_atual()
            
        elif opcao == "2":
            webhook_automatico(1)
            
        elif opcao == "3":
            intervalo = int(input("Digite o intervalo em minutos: "))
            webhook_automatico(intervalo)
            
        elif opcao == "4":
            testar_alertas_infrawatch()
            
        elif opcao == "5":
            print("\n📝 Criar alerta personalizado:")
            endpoint_name = input("Nome do endpoint: ").strip()
            endpoint_ip = input("IP/Host: ").strip()
            
            print("\nEscolha o status:")
            print("1 - UP")
            print("2 - DOWN") 
            print("3 - SNMP DOWN")
            
            status_opcao = input("Status (1-3): ").strip()
            status_map = {"1": "UP", "2": "DOWN", "3": "SNMP DOWN"}
            status = status_map.get(status_opcao, "DOWN")
            
            additional_info = input("Informações adicionais (opcional): ").strip()
            if not additional_info:
                additional_info = None
            
            enviar_alerta_infrawatch(endpoint_name, endpoint_ip, status, None, additional_info)
            
        else:
            print("❌ Opção inválida!")
            
    except KeyboardInterrupt:
        print("\n👋 Programa encerrado pelo usuário")
    except ValueError:
        print("❌ Por favor, digite um número válido")