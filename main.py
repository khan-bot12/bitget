from fastapi import FastAPI, Request
from bitget_trade import place_order
import uvicorn

app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        action = data.get("action")
        symbol = data.get("symbol")
        quantity = data.get("quantity")
        leverage = data.get("leverage")
        token = data.get("token")  # Optional: only used if you added SECRET_TOKEN

        # Optional: Add token check here if SECRET_TOKEN is used
        # from os import getenv
        # if getenv("SECRET_TOKEN") and token != getenv("SECRET_TOKEN"):
        #     return {"status": "unauthorized", "message": "Invalid token"}

        # Call order placement logic
        result = place_order(action, symbol, quantity, leverage)
        return result

    except Exception as e:
        print(f"❌ Error handling webhook: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10000)
