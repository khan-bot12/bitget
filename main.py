# main.py

from fastapi import FastAPI, Request, HTTPException
from bitget_trade import place_futures_order
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

SECRET_TOKEN = os.getenv("SECRET_TOKEN")  # Optional security

@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        
        # Optional: Check secret token
        if SECRET_TOKEN and data.get("token") != SECRET_TOKEN:
            raise HTTPException(status_code=401, detail="Unauthorized")

        action = data.get("action")
        symbol = data.get("symbol")
        quantity = data.get("quantity")
        leverage = data.get("leverage", 5)

        if not all([action, symbol, quantity]):
            raise HTTPException(status_code=400, detail="Missing required fields")

        response = place_futures_order(action, symbol, quantity, leverage)
        return {"status": "success", "exchange_response": response}

    except Exception as e:
        return {"status": "error", "message": str(e)}
