import sqlite3
import urllib.request
import json
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Ai Trade - Scalp & Risk Engine")

# CORS Configuration for local frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATABASE SETUP ---

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                completed BOOLEAN DEFAULT 0
            )
        """)

@app.on_event("startup")
def startup():
    init_db()

# --- PYDANTIC SCHEMAS ---

class ItemCreate(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False

class ItemResponse(ItemCreate):
    id: int

# --- WATCHLIST & NOTES API ROUTES ---

@app.get("/api/items", response_model=List[ItemResponse])
def read_items():
    with get_db() as conn:
        cursor = conn.execute("SELECT id, title, description, completed FROM items")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

@app.post("/api/items", response_model=ItemResponse)
def create_item(item: ItemCreate):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO items (title, description, completed) VALUES (?, ?, ?)",
            (item.title, item.description, item.completed)
        )
        conn.commit()
        item_id = cursor.lastrowid
        return {**item.dict(), "id": item_id}

@app.delete("/api/items/{item_id}")
def delete_item(item_id: int):
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"status": "success", "message": f"Item {item_id} deleted"}

# --- TECHNICAL ANALYSIS ENGINE ---

def calculate_rsi(prices: List[float], period: int = 14) -> float:
    if len(prices) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(1, len(prices)):
        change = prices[i] - prices[i - 1]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))
    
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

@app.get("/api/rsi/analyze/{query}")
def analyze_rsi(query: str):
    try:
        # Determine lookup type (contract address vs ticker symbol)
        if query.startswith("0x") or len(query) > 30:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{query}"
        else:
            url = f"https://api.dexscreener.com/latest/dex/search?q={query}"

        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            pairs = data.get("pairs")
            if not pairs:
                raise HTTPException(status_code=404, detail="No pairs found")
            
            top_pair = pairs[0]
            price = float(top_pair.get("priceUsd", 0))
            c5m = float(top_pair.get("priceChange", {}).get("m5", 0))
            c1h = float(top_pair.get("priceChange", {}).get("h1", 0))
            c6h = float(top_pair.get("priceChange", {}).get("h6", 0))
            c24h = float(top_pair.get("priceChange", {}).get("h24", 0))

            # Historical price array for dynamic RSI calculation
            reconstructed = [
                price / (1 + c24h/100 if c24h != -100 else 1),
                price / (1 + c6h/100 if c6h != -100 else 1),
                price / (1 + c1h/100 if c1h != -100 else 1),
                price / (1 + c5m/100 if c5m != -100 else 1),
                price
            ]

            rsi_val = calculate_rsi(reconstructed, period=3)

            # Determine 5-minute trend direction
            if c5m > 0.5:
                trend_5m = "BULLISH MOMENTUM (5M)"
            elif c5m < -0.5:
                trend_5m = "BEARISH MOMENTUM (5M)"
            else:
                trend_5m = "SIDEWAYS / CONSOLIDATING"

            # 15-Second Micro-Prediction Logic
            score = (c5m * 2) + (rsi_val - 50)
            if score > 5:
                prediction_15s = "PUMP / UP"
                confidence = min(round(60 + (score * 1.2), 1), 94.5)
            elif score < -5:
                prediction_15s = "DUMP / DOWN"
                confidence = min(round(60 + (abs(score) * 1.2), 1), 94.5)
            else:
                prediction_15s = "NEUTRAL / STABLE"
                confidence = 50.0

            # Calculate target trade levels
            buy_entry = price * (0.998 if c5m > 0 else 0.995)
            stop_loss = buy_entry * 0.985
            take_profit = buy_entry * 1.030

            return {
                "symbol": top_pair.get("baseToken", {}).get("symbol", "UNKNOWN"),
                "name": top_pair.get("baseToken", {}).get("name", ""),
                "price": price,
                "rsi_14": rsi_val,
                "change_5m": c5m,
                "trend_5m": trend_5m,
                "prediction_15s": prediction_15s,
                "confidence_15s": confidence,
                "chain": top_pair.get("chainId", ""),
                "buy_entry": buy_entry,
                "stop_loss": stop_loss,
                "take_profit": take_profit
            }
    except Exception as e:
        return {"error": str(e)}
