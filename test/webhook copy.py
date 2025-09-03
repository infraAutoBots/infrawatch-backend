import requests
import json
from datetime import datetime
import time

# URL do webhook do Discord (substitua pela sua URL)
WEBHOOK_URL = "https://discord.com/api/webhooks/1412595075099136141/WP7CfeZ4saW39XoaDb17WrgLwhNw49r3_ufGg-wOj6dTWYmSE4A019AXLyRLtRCp5jjX"

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
    print("=== WEBHOOK DISCORD - HORA ATUAL ===")
    print()
    
    # Opções de execução
    print("Escolha uma opção:")
    print("1 - Enviar hora atual uma vez")
    print("2 - Enviar automaticamente a cada minuto")
    print("3 - Enviar automaticamente com intervalo personalizado")
    
    try:
        opcao = input("\nDigite sua opção (1-3): ").strip()
        
        if opcao == "1":
            enviar_hora_atual()
            
        elif opcao == "2":
            webhook_automatico(1)
            
        elif opcao == "3":
            intervalo = int(input("Digite o intervalo em minutos: "))
            webhook_automatico(intervalo)
            
        else:
            print("❌ Opção inválida!")
            
    except KeyboardInterrupt:
        print("\n👋 Programa encerrado pelo usuário")
    except ValueError:
        print("❌ Por favor, digite um número válido")