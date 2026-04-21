import os
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator

from database import init_db, get_or_create_user, save_message, get_conversation_history, log_analytics, get_dashboard_stats
from ai_engine import generate_response

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("Database initialized")
    yield


app = FastAPI(
    title="Guanacaste Concierge AI",
    description="WhatsApp AI concierge for tourists in Guanacaste, Costa Rica",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def validate_twilio_request(request: Request, form_data: dict) -> bool:
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    if not auth_token:
        return True  # Skip validation in dev
    validator = RequestValidator(auth_token)
    url = str(request.url)
    signature = request.headers.get("X-Twilio-Signature", "")
    return validator.validate(url, form_data, signature)


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(
    request: Request,
    Body: str = Form(""),
    From: str = Form(""),
    To: str = Form(""),
    ProfileName: str = Form(""),
):
    form_data = {"Body": Body, "From": From, "To": To, "ProfileName": ProfileName}

    if not validate_twilio_request(request, form_data):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    if not Body.strip():
        resp = MessagingResponse()
        resp.message("¡Pura Vida! 🌴 Send me a message and I'll help you explore Guanacaste!")
        return HTMLResponse(content=str(resp), media_type="application/xml")

    phone = From.replace("whatsapp:", "")
    user = await get_or_create_user(phone)
    user_id = user["id"]

    await save_message(user_id, "user", Body)
    await log_analytics("message_received", {"phone": phone, "length": len(Body)})

    history = await get_conversation_history(user_id, limit=20)
    ai_reply = await generate_response(history[:-1], Body)

    await save_message(user_id, "assistant", ai_reply)
    await log_analytics("response_sent", {"phone": phone, "length": len(ai_reply)})

    resp = MessagingResponse()
    resp.message(ai_reply)

    logger.info(f"Processed message from {phone}: {Body[:50]}...")
    return HTMLResponse(content=str(resp), media_type="application/xml")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    stats = await get_dashboard_stats()
    return templates.TemplateResponse("dashboard.html", {"request": request, "stats": stats})


@app.get("/api/stats")
async def api_stats():
    stats = await get_dashboard_stats()
    return JSONResponse(content=stats)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "guanacaste-concierge"}


@app.get("/widget.js")
async def widget_js():
    js_content = open("static/widget.js").read()
    return HTMLResponse(content=js_content, media_type="application/javascript")


@app.get("/embed", response_class=HTMLResponse)
async def embed_demo(request: Request):
    stats = await get_dashboard_stats()
    return templates.TemplateResponse("embed_demo.html", {"request": request, "stats": stats})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", "8000")),
        reload=True,
    )
