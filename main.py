from fastapi import FastAPI, Request
from bitget_trade import smart_trade

app = FastAPI()

@app.get("/")
def read_root():
    return {"msg": "Bitget AutoBot is running 🎉"}

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    print(f"📬 Incoming webhook: {data}")

    action = data.get("action")
    symbol = data.get("symbol")
    quantity = data.get("quantity")
    leverage = data.get("leverage", 50)

    result = smart_trade(action, symbol, quantity, leverage)
    print(f"📤 smart_trade result: {result}")

    return {"status": "ok", "details": result}
