import time
import hmac
import hashlib
import requests
import uuid
import os
import json  # ✅ Fix: required for sending JSON body

# Load API credentials from environment variables
API_KEY = os.getenv("BITGET_API_KEY")
API_SECRET = os.getenv("BITGET_API_SECRET")
API_PASSPHRASE = os.getenv("BITGET_API_PASSPHRASE")

# Bitget base API URL
BASE_URL = "https://api.bitget.com"


# Create headers with HMAC signature
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


# Get the current position for the symbol
def get_position(symbol):
    url = f"/api/mix/v1/position/singlePosition"
    params = f"?symbol={symbol}&marginCoin=USDT"
    full_url = BASE_URL + url + params
    try:
        response = requests.get(full_url, headers=headers("GET", url + params))
        print("📊 Current Position Info:", response.json())
        return response.json()
    except Exception as e:
        print("❌ Exception getting position:", str(e))
        return None


# Place a new order (and optionally close the opposite position)
def place_order(action, symbol, quantity, leverage):
    try:
        # Step 1: Get current open positions
        position_info = get_position(symbol)
        opposite_side = "short" if action == "buy" else "long"

        # Step 2: Check for opposite position and close it
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
                        url = "/api/mix/v1/order/close-position"
                        response = requests.post(
                            BASE_URL + url,
                            json=close_order,
                            headers=headers("POST", url, json.dumps(close_order))
                        )
                        print("🧹 Close Response:", response.json())

        # Step 3: Place the new order
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
            json=order,
            headers=headers("POST", url, json.dumps(order))
        )
        print("✅ Order Response:", response.json())
        return response.json()

    except Exception as e:
        print("❌ Exception:", str(e))
        return {"error": str(e)}
