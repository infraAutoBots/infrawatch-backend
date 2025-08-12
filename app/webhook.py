
# 7. webhook.py
# - Envia POST assíncrono com aiohttp para o webhook_url.
# - Personaliza mensagem: Envia dict com message, services, snmp_data.

import aiohttp
from typing import Dict, Optional

async def send_webhook(url: str, payload: Dict):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload):
                pass  # Ignora resposta, ou logue
        except Exception:
            pass  # Handle error se necessário

