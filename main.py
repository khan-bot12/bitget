import uvicorn
from fastapi import FastAPI, Request
import json
from bitget_trade import smart_trade

app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    print(f"📥 ALERT RECEIVED: {json.dumps(data)}")
    action = data.get("action")
    symbol = data.get("symbol")
    quantity = data.get("quantity")
    leverage = data.get("leverage")
    return smart_trade(action, symbol, quantity, leverage)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=80)
