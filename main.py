from fastapi import FastAPI, Request
from bitget_trade import smart_trade
import uvicorn

app = FastAPI()

@app.get("/")
def home():
    return {"msg": "✅ Bitget Smart Bot is running."}

@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        print(f"📬 Incoming webhook: {data}")

        action = data.get("action")
        symbol = data.get("symbol")
        quantity = data.get("quantity")
        leverage = data.get("leverage", 50)

        # Basic validation
        if not all([action, symbol, quantity]):
            print("❌ Missing required fields in webhook data.")
            return {"status": "error", "msg": "Missing required fields"}

        # Call the smart trading logic
        result = smart_trade(action, symbol, quantity, leverage)
        return {"status": "ok", "result": result}

    except Exception as e:
        print(f"❌ Webhook handling error: {e}")
        return {"status": "error", "msg": str(e)}

# Run app on port 80 so TradingView can reach it
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=80)
