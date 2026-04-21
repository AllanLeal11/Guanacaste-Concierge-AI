# 🌴 Guanacaste Concierge AI

An AI-powered WhatsApp concierge for tourists visiting Guanacaste, Costa Rica. Built with FastAPI, OpenAI, and Twilio.

## Features

- **WhatsApp Integration** — Twilio webhook receives messages and responds via GPT-4o-mini
- **Local Expert AI** — System prompt tuned for Guanacaste: tours, weather, transportation, dining, and practical tips
- **Conversation Memory** — SQLite database tracks per-user conversation history and preferences
- **Analytics Dashboard** — Web-based dashboard showing user stats, message volume, and event tracking
- **Embeddable Widget** — Drop-in `<script>` tag that adds a WhatsApp CTA to any website
- **Bilingual** — Automatically detects and responds in English or Spanish

## Quick Start

### 1. Clone & install

```bash
git clone https://github.com/your-org/guanacaste-concierge.git
cd guanacaste-concierge
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key (GPT-4o-mini) |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token |
| `TWILIO_WHATSAPP_NUMBER` | Your Twilio WhatsApp number |

### 3. Run

```bash
python main.py
```

The server starts at `http://localhost:8000`.

### 4. Set up Twilio webhook

In your Twilio Console → WhatsApp Sandbox (or production number):
- **When a message comes in**: `https://your-domain.com/webhook/whatsapp` (POST)

Use [ngrok](https://ngrok.com) or Cloudflare Tunnel for local development.

## Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/webhook/whatsapp` | Twilio WhatsApp webhook |
| `GET` | `/` | Analytics dashboard |
| `GET` | `/api/stats` | JSON stats endpoint |
| `GET` | `/health` | Health check |
| `GET` | `/widget.js` | Embeddable widget script |
| `GET` | `/embed` | Widget integration demo page |

## Website Widget

Add the concierge to any website:

```html
<script src="https://your-domain.com/widget.js"
        data-phone="+506XXXXXXXX"
        data-message="Hi! I'd like info about Guanacaste 🌴"
        data-position="bottom-right"></script>
```

Visit `/embed` for a live demo and configuration docs.

## Project Structure

```
guanacaste_concierge/
├── main.py              # FastAPI app, routes, webhook
├── ai_engine.py         # OpenAI integration & system prompt
├── database.py          # SQLite async database layer
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
├── .gitignore
├── static/
│   └── widget.js        # Embeddable WhatsApp widget
├── templates/
│   ├── dashboard.html   # Analytics dashboard
│   └── embed_demo.html  # Widget demo page
└── tests/
    └── test_app.py      # Test suite
```

## Testing

```bash
python -m pytest tests/ -x -q
```

## License

MIT
