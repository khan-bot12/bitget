import uuid
import time
from bitget.apis.mix_v1 import MixAccountApi, MixOrderApi, MixPositionApi
from bitget.config import Config
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Setup Bitget API credentials
api_key = os.getenv("BITGET_API_KEY")
api_secret = os.getenv("BITGET_API_SECRET")
api_passphrase = os.getenv("BITGET_API_PASSPHRASE")

# Initialize SDK configuration
Config.set_config({
    "API_KEY": api_key,
    "API_SECRET_KEY": api_secret,
    "PASSPHRASE": api_passphrase,
    "BASE_URL": "https://api.bitget.com"
})

# Initialize Bitget Futures APIs
order_api = MixOrderApi()
position_api = MixPositionApi()

# Market type (e.g., 'umcbl' = USDT-M Perpetual)
MARKET_TYPE = "umcbl"

# === Get current position side ===
def get_current_position(symbol: str):
    try:
        response = position_api.single_position(symbol=symbol, productType=MARKET_TYPE)
        print("📊 Current Position Info:", response)
        position_list = response.get("data", [])
        return position_list[0]["holdSide"] if position_list else None
    except Exception as e:
        print("❌ Error getting position:", e)
        return None

# === Place a long or short order ===
def place_order(action: str, symbol: str, quantity: float, leverage: int):
    try:
        print("📦 Parsed →", f"action: {action}, symbol: {symbol}, quantity: {quantity}, leverage: {leverage}")

        # Set leverage
        position_api.set_leverage(symbol=symbol, marginCoin="USDT", leverage=leverage, holdSide="long")
        position_api.set_leverage(symbol=symbol, marginCoin="USDT", leverage=leverage, holdSide="short")

        # Get current position side
        current_position = get_current_position(symbol)

        # Close opposite position if needed
        if action == "buy" and current_position == "short":
            print("🔁 Closing short position before going long...")
            order_api.place_order(
                symbol=symbol,
                marginCoin="USDT",
                side="buy",
                orderType="market",
                size=quantity,
                holdSide="close_short",
                clientOrderId=str(uuid.uuid4())
            )
            time.sleep(1)
        elif action == "sell" and current_position == "long":
            print("🔁 Closing long position before going short...")
            order_api.place_order(
                symbol=symbol,
                marginCoin="USDT",
                side="sell",
                orderType="market",
                size=quantity,
                holdSide="close_long",
                clientOrderId=str(uuid.uuid4())
            )
            time.sleep(1)

        print("🟢 Placing order...")
        order_response = order_api.place_order(
            symbol=symbol,
            marginCoin="USDT",
            side="buy" if action == "buy" else "sell",
            orderType="market",
            size=quantity,
            holdSide="open_long" if action == "buy" else "open_short",
            clientOrderId=str(uuid.uuid4())
        )

        print("✅ Order Response:", order_response)
        return order_response
    except Exception as e:
        print("❌ EXCEPTION:", e)
        return {"error": str(e)}
