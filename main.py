from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from bitget_trade import place_order

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "Bitget bot is live 🚀"}

@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        print("📥 Incoming webhook data:", data)

        # Extract parameters from webhook
        action = data.get("action")
        symbol = data.get("symbol")
        quantity = data.get("quantity")
        leverage = data.get("leverage", 50)

        if not action or not symbol or not quantity:
            return JSONResponse(status_code=400, content={
                "error": "Missing required fields: action, symbol, quantity"
            })

        # Place order via Bitget
        result = place_order(action, symbol, quantity, leverage)
        print("📤 Result from place_order:", result)

        return JSONResponse(content={"status": "ok", "result": result})
    
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
