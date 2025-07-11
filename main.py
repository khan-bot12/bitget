from fastapi import FastAPI, Request
import uvicorn
import json
from bitget_trade import smart_trade

app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        print("📥 Webhook Received:", data)

        action = data.get("action")
        symbol = data.get("symbol")
        quantity = data.get("quantity")
        leverage = data.get("leverage")

        if not all([action, symbol, quantity, leverage]):
            return {"error": "Missing parameters"}

        result = smart_trade(action, symbol, quantity, leverage)
        return {"status": "executed", "result": result}

    except Exception as e:
        print("❌ Webhook Error:", str(e))
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=80)
