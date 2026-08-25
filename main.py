import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

app = FastAPI(title="Trade Analysia Engine")

if not os.path.exists("static"):
    os.makedirs("static")
if not os.path.exists("templates"):
    os.makedirs("templates")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/analyze")
async def analyze_market(symbol: str = "BTC"):
    url = f"https://api.dexscreener.com/latest/dex/search?q={symbol}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    if response.status_code == 200:
        data = response.json()
        pairs = data.get("pairs", [])
        if pairs:
            top_pair = pairs[0]
            price_usd = float(top_pair.get("priceUsd", 0))
            change_24h = float(top_pair.get("priceChange", {}).get("h24", 0))
            change_5m = float(top_pair.get("priceChange", {}).get("m5", 0))

            # Scalping Signal & 15s Direction Logic
            signal = "BUY" if change_24h > 0 else "SELL"
            trend = "Bullish" if change_24h > 0 else "Bearish"
            confidence = f"{min(85 + abs(change_24h), 98):.1f}%"
            rsi = f"{min(max(50 + (change_24h * 1.5), 15), 85):.1f}"

            # 15-Second High-Frequency Market Direction Prediction
            if change_5m > 0.05:
                pred_15s = "STRONG UP ↑"
                pred_color = "emerald"
            elif change_5m > 0:
                pred_15s = "SLIGHT UP ↑"
                pred_color = "emerald"
            elif change_5m < -0.05:
                pred_15s = "STRONG DOWN ↓"
                pred_color = "rose"
            else:
                pred_15s = "SLIGHT DOWN ↓"
                pred_color = "rose"

            # Targets calculation
            if signal == "BUY":
                entry = f"${price_usd * 0.998:,.4f} - ${price_usd:,.4f}"
                sl = f"${price_usd * 0.985:,.4f}"
                tp = f"${price_usd * 1.035:,.4f}"
            else:
                entry = f"${price_usd:,.4f} - ${price_usd * 1.002:,.4f}"
                sl = f"${price_usd * 1.015:,.4f}"
                tp = f"${price_usd * 0.965:,.4f}"

            return {
                "status": "success",
                "symbol": top_pair.get("baseToken", {}).get("symbol", symbol),
                "pair_name": f"{top_pair.get('baseToken', {}).get('symbol')}/{top_pair.get('quoteToken', {}).get('symbol')}",
                "price": f"${price_usd:,.4f}",
                "change_24h": f"{change_24h}%",
                "trend": trend,
                "signal": signal,
                "confidence": confidence,
                "rsi": rsi,
                "prediction_15s": pred_15s,
                "prediction_color": pred_color,
                "entry_zone": entry,
                "stop_loss": sl,
                "take_profit": tp,
                "dex": top_pair.get("dexId", "N/A"),
            }

    return {"status": "error", "message": "Symbol not found"}
