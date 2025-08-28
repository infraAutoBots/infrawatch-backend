import uvicorn
from fastapi import FastAPI, Request, Header, HTTPException, BackgroundTasks
from pydantic import BaseModel
import hmac, hashlib, os, logging

app = FastAPI(title="Webhook Receiver")

# Ajuste via ambiente. Para testar rápido, pode deixar em branco.
WEBHOOK_TOKEN  = os.getenv("WEBHOOK_TOKEN", "mytoken")      # Authorization: Bearer mytoken
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change-me")   # usado na assinatura HMAC


class Event(BaseModel):
    event: str
    server_ip: str | None = None
    data: dict | None = None
    timestamp: str | None = None


def verify_signature(body: bytes, signature: str | None) -> bool:
    # Aceita "sha256=<hex>" ou apenas "<hex>"
    if not signature:
        return False
    parts = signature.split("=", 1)
    provided = parts[1] if len(parts) == 2 else parts[0]
    digest = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(provided, digest)


def process_event(evt: dict):
    # TODO: salvar no banco, disparar alerta, etc.
    logging.info("Processando evento: %s", evt)


@app.post("/webhook")
async def receive_webhook(
    request: Request,
    background: BackgroundTasks,
    authorization: str | None = Header(None),
    x_signature_256: str | None = Header(None, alias="X-Signature-256")
):
    # 1) Autenticação por token
    if WEBHOOK_TOKEN and authorization != f"Bearer {WEBHOOK_TOKEN}":
        raise HTTPException(status_code=401, detail="invalid token")

    # 2) Verificação HMAC
    body = await request.body()
    if WEBHOOK_SECRET and not verify_signature(body, x_signature_256):
        raise HTTPException(status_code=401, detail="invalid signature")

    # 3) Parse + processamento em background
    data = await request.json()
    background.add_task(process_event, data)

    # 4) Responder rápido
    return {"status": "accepted"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
