import time
import uuid
import hmac
import hashlib
import base64
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Load API keys from environment
API_KEY = os.getenv("BITGET_API_KEY")
API_SECRET = os.getenv("BITGET_API_SECRET")
API_PASSPHRASE = os.getenv("BITGET_API_PASSPHRASE")

BASE_URL = "https://api.bitget.com"

def get_timestamp():
    return str(int(time.time() * 1000))

def sign_request(timestamp, method, request_path, body=""):
    message = f"{timestamp}{method}{request_path}{body}"
    signature = hmac.new(API_SECRET.encode(), message.encode(), hashlib.sha256).digest()
    return base64.b64encode(signature).decode()

def headers(method, path, body=""):
    timestamp = get_timestamp()
    signature = sign_request(timestamp, method, path, body)
    return {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": API_PASSPHRASE,
        "Content-Type": "application/json"
    }

def get_position(symbol):
    url = f"/api/mix/v1/position/singlePosition"
    full_url = f"{BASE_URL}{url}?symbol={symbol}&marginCoin=USDT"
    h = headers("GET", f"{url}?symbol={symbol}&marginCoin=USDT")
    r = requests.get(full_url, headers=h)
    return r.json()

def place_order(action, symbol, quantity, leverage):
    try:
        position_info = get_position(symbol)
        print("📊 Current Position Info:", position_info)

        if "data" in position_info:
            pos_data = position_info["data"]
            if isinstance(pos_data, list) and len(pos_data) > 0:
                current_side = pos_data[0].get("holdSide")
            elif isinstance(pos_data, dict):
                current_side = pos_data.get("holdSide")
            else:
                current_side = None
        else:
            current_side = None

        # Cancel opposite position
        if current_side == "long" and action == "sell":
            print("🔁 Closing long position before opening short.")
        elif current_side == "short" and action == "buy":
            print("🔁 Closing short position before opening long.")

        url = "/api/mix/v1/order/placeOrder"
        full_url = f"{BASE_URL}{url}"

        side = "open_long" if action == "buy" else "open_short"

        body_data = {
            "symbol": symbol,
            "marginCoin": "USDT",
            "size": str(quantity),
            "side": side,
            "orderType": "market",
            "force": "gtc",
            "leverage": str(leverage),
            "clientOid": str(uuid.uuid4())
        }

        body = json.dumps(body_data)
        h = headers("POST", url, body)
        print("🟢 Placing order...")
        r = requests.post(full_url, headers=h, data=body)
        print("✅ Order Response:", r.json())
        return r.json()

    except Exception as e:
        print(f"❌ Exception: {e}")
        return {"error": str(e)}
