from fastapi import FastAPI, Request
from bitget_trade import place_order
import uvicorn

app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        print("🔍 Incoming webhook data:", data)

        action = data.get("action")
        symbol = data.get("symbol")
        quantity = data.get("quantity")
        leverage = data.get("leverage")
        token = data.get("token")

        print(f"📦 Parsed → action: {action}, symbol: {symbol}, quantity: {quantity}, leverage: {leverage}")

        if None in [action, symbol, quantity, leverage]:
            print("❌ Missing one or more required fields.")
            return {"status": "error", "message": "Missing field in webhook payload."}

        result = place_order(action, symbol, quantity, leverage)
        print("📤 Result from place_order:", result)
        return result

    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10000)
