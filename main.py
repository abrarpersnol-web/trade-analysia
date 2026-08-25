import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

app = FastAPI(title="Trade Analysia Engine")

# Ensure static and templates folders exist
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
async def analyze_market(symbol: str = "BTC"):
    """Fetches live market pair data via DexScreener API for Trade Analysia."""
    url = f"https://api.dexscreener.com/latest/dex/search?q={symbol}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    if response.status_code == 200:
        data = response.json()
        pairs = data.get("pairs", [])
        if pairs:
            top_pair = pairs[0]
            price_usd = float(top_pair.get("priceUsd", 0))
            change_24h = top_pair.get("priceChange", {}).get("h24", 0)

            signal = "BUY" if change_24h > 0 else "SELL"
            trend = "Bullish" if change_24h > 0 else "Bearish"

            return {
                "status": "success",
                "symbol": top_pair.get("baseToken", {}).get("symbol", symbol),
                "pair_name": (
                    f"{top_pair.get('baseToken', {}).get('symbol')}/"
                    f"{top_pair.get('quoteToken', {}).get('symbol')}"
                ),
                "price": f"${price_usd:,.4f}",
                "change_24h": f"{change_24h}%",
                "trend": trend,
                "signal": signal,
                "dex": top_pair.get("dexId", "N/A"),
            }

    return {"status": "error", "message": "Symbol not found"}
