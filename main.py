from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
        <head><title>Trade Analysia</title></head>
        <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
            <h1>Welcome to Trade Analysia</h1>
            <p>Your FastAPI backend is live!</p>
        </body>
    </html>
    """
