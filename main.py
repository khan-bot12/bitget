from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from bitget_trade import smart_trade

app = FastAPI()

# Root endpoint
@app.get("/")
async def root():
    return {"status": "Bitget bot is live 🚀"}

# Health check for Render
@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

# Webhook to receive alerts from TradingView
@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        print("📥 Incoming webhook data:", data)

        action = data.get("action")
        symbol = data.get("symbol")
        quantity = data.get("quantity")
        leverage = data.get("leverage", 50)

        if not action or not symbol or not quantity:
            return JSONResponse(status_code=400, content={"error": "Missing action, symbol, or quantity"})

        # Add _UMCBL if not already present
        if not symbol.endswith("_UMCBL"):
            symbol += "_UMCBL"

        result = smart_trade(action, symbol, quantity, leverage)
        print("📤 Result from smart_trade:", result)

        return {"status": "ok", "result": result}

    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
