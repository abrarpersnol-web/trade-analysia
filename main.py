from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Trade Analysia</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-900 text-white min-h-screen flex flex-col items-center justify-center p-4">
        <div class="max-w-xl w-full bg-slate-800 rounded-xl p-6 shadow-2xl border border-slate-700">
            <h1 class="text-3xl font-bold text-emerald-400 mb-2 text-center">Trade Analysia</h1>
            <p class="text-slate-400 text-center mb-6">Real-time market insights & technical indicators.</p>
            
            <div class="grid grid-cols-2 gap-4 mb-6">
                <div class="bg-slate-700/50 p-4 rounded-lg border border-slate-600">
                    <span class="text-xs text-slate-400 uppercase tracking-wider">Status</span>
                    <p class="text-lg font-semibold text-emerald-400">Online</p>
                </div>
                <div class="bg-slate-700/50 p-4 rounded-lg border border-slate-600">
                    <span class="text-xs text-slate-400 uppercase tracking-wider">Server</span>
                    <p class="text-lg font-semibold text-blue-400">FastAPI / Render</p>
                </div>
            </div>

            <button class="w-full py-3 bg-emerald-500 hover:bg-emerald-600 font-bold rounded-lg transition-all duration-200 shadow-lg shadow-emerald-500/20">
                Analyze Market Data
            </button>
        </div>
    </body>
    </html>
    """
