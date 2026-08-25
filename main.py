from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

app = FastAPI(title="Trade Analysia Engine")

# Ensure static and templates folders are recognized
if not os.path.exists("static"):
    os.makedirs("static")
if not os.path.exists("templates"):
    os.makedirs("templates")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Renders the main Trade Analysia dashboard."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/analyze")
async def analyze_market(symbol: str = "BTCUSDT"):
    """
    Simulates real-time technical analysis engine.
    Returns trend status, RSI metric, and key trade target levels.
    """
    symbol_upper = symbol.upper()

    # Mock dynamic response for demonstration
    return {
        "status": "success",
        "symbol": symbol_upper,
        "rsi": 62.4,
        "trend": "Bullish",
        "signal": "BUY",
        "confidence": "88%",
        "entry_zone": "$92,400 - $92,800",
        "stop_loss": "$91,100",
        "take_profit": "$95,500"
    }
