from fastapi import APIRouter, Request, Query
from fastapi.responses import PlainTextResponse, JSONResponse
import json

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])

VERIFY_TOKEN = "healthcare_webhook_2024"

@router.get("/webhook")
async def verify_webhook(
        hub_mode: str = Query(None, alias="hub.mode"),
        hub_token: str = Query(None, alias="hub.verify_token"),
        hub_challenge: int = Query(None, alias="hub.challenge")
):
    """GET endpoint for webhook verification"""
    if hub_mode == "subscribe" and hub_token == VERIFY_TOKEN:
        return PlainTextResponse(str(hub_challenge))
    return PlainTextResponse("Verification failed", status_code=403)

@router.post("/webhook")
async def handle_webhook(request: Request):
    try:
        body = await request.json()

        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})

                for message in value.get("messages", []):
                    from_number = message.get("from")
                    text = message.get("text", {}).get("body", "").upper()

                    print(f"📱 Message from {from_number}: {text}")

                    # Process reply
                    if text == "CONFIRM":
                        print(f"✅ Patient {from_number} confirmed appointment")
                        # Update appointment status in database

                    elif text == "CANCEL":
                        print(f"❌ Patient {from_number} cancelled appointment")
                        # Cancel appointment in database

        return JSONResponse(content={"status": "ok"})

    except Exception as e:
        print(f"❌ Error: {e}")
        return JSONResponse(content={"status": "error"}, status_code=500)