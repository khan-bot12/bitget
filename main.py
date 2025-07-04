from fastapi import FastAPI, Request
from bitget_trade import place_order

app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    print("Incoming webhook data:", data)

    action = data.get("action")
    symbol = data.get("symbol")
    quantity = data.get("quantity")
    leverage = data.get("leverage", 50)

    result = place_order(action, symbol, quantity, leverage)
    print("📤 Result from place_order:", result)
    return {"status": "ok", "result": result}
