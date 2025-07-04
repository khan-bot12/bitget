import time
import hmac
import hashlib
import requests
import uuid
import os
import json

# Load Bitget API credentials from environment variables
API_KEY = os.getenv("BITGET_API_KEY")
API_SECRET = os.getenv("BITGET_API_SECRET")
API_PASSPHRASE = os.getenv("BITGET_API_PASSPHRASE")

# Base URL for Bitget API
BASE_URL = "https://api.bitget.com"

# === Generate HMAC SHA256 Signature Header ===
def headers(method, request_path, body=""):
    timestamp = str(int(time.time() * 1000))
    pre_hash = timestamp + method.upper() + request_path + body
    sign = hmac.new(API_SECRET.encode(), pre_hash.encode(), hashlib.sha256).hexdigest()
    return {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": sign,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": API_PASSPHRASE,
        "Content-Type": "application/json"
    }

# === Get Position for the Symbol ===
def get_position(symbol):
    url = f"/api/mix/v1/position/singlePosition"
    params = f"?symbol={symbol}&marginCoin=USDT"
    full_url = BASE_URL + url + params
    try:
        response = requests.get(full_url, headers=headers("GET", url + params))
        print("📊 Current Position Info:", response.json())
        return response.json()
    except Exception as e:
        print("❌ Exception while fetching position:", str(e))
        return None

# === Place an Order ===
def place_order(action, symbol, quantity, leverage):
    try:
        opposite_side = "short" if action == "buy" else "long"

        # Step 1: Check if we need to close the opposite position
        position_info = get_position(symbol)
        if position_info and position_info.get("code") == "00000":
            positions = position_info.get("data", [])
            if isinstance(positions, list):
                for pos in positions:
                    if pos.get("holdSide") == opposite_side and float(pos.get("total", 0)) > 0:
                        print(f"🔁 Closing opposite position: {opposite_side}")
                        close_order = {
                            "symbol": symbol,
                            "marginCoin": "USDT",
                            "side": "close_" + opposite_side,
                            "orderType": "market",
                            "size": str(pos["total"]),
                            "clientOid": str(uuid.uuid4())
                        }
                        close_url = "/api/mix/v1/order/close-position"
                        response = requests.post(
                            BASE_URL + close_url,
                            headers=headers("POST", close_url, json.dumps(close_order)),
                            data=json.dumps(close_order)
                        )
                        print("🧹 Close Response:", response.json())

        # Step 2: Place new long or short order
        print("🟢 Placing new order...")
        side = "open_long" if action == "buy" else "open_short"
        order = {
            "symbol": symbol,
            "marginCoin": "USDT",
            "side": side,
            "orderType": "market",
            "size": str(quantity),
            "leverage": str(leverage),
            "clientOid": str(uuid.uuid4())
        }
        url = "/api/mix/v1/order/place-order"
        response = requests.post(
            BASE_URL + url,
            headers=headers("POST", url, json.dumps(order)),
            data=json.dumps(order)
        )
        print("✅ Order Response:", response.json())
        return response.json()

    except Exception as e:
        print("❌ Exception:", str(e))
        return {"error": str(e)}
