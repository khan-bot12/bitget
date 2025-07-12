from fastapi import FastAPI, Request
import uvicorn
import json
from bitget_trade import smart_trade

app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        action = data["action"]
        symbol = data["symbol"]
        quantity = data["quantity"]
        leverage = data.get("leverage", 20)

        print(f"🚀 Webhook received: {data}")
        result = smart_trade(action, symbol, quantity, leverage)
        return {"status": "ok", "result": result}

    except Exception as e:
        print(f"❌ Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=80)
