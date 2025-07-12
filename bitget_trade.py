from fastapi import FastAPI, Request
from bitget_trade import smart_trade
import uvicorn

app = FastAPI()

@app.get("/")
def home():
    return {"msg": "✅ Bitget Smart Bot is running."}

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    print(f"📬 Incoming webhook: {data}")

    action = data.get("action")
    symbol = data.get("symbol")
    quantity = data.get("quantity")
    leverage = data.get("leverage", 50)

    result = smart_trade(action, symbol, quantity, leverage)
    return {"status": "ok", "result": result}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=80)
