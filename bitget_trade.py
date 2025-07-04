import time
import hmac
import hashlib
import base64
import json
import uuid
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# === ENV VARIABLES ===
API_KEY = os.getenv("BITGET_API_KEY")
API_SECRET = os.getenv("BITGET_API_SECRET")
API_PASSPHRASE = os.getenv("BITGET_API_PASSPHRASE")
BASE_URL = "https://api.bitget.com"

# === SIGNATURE GENERATOR ===
def generate_signature(timestamp, method, request_path, body):
    prehash = f"{timestamp}{method}{request_path}{body}"
    hash_bytes = hmac.new(API_SECRET.encode(), prehash.encode(), hashlib.sha256).digest()
    signature = base64.b64encode(hash_bytes).decode()
    return signature

# === COMMON HEADERS ===
def get_headers(method, path, body):
    timestamp = str(int(time.time() * 1000))
    body_str = json.dumps(body) if body else ""
    sign = generate_signature(timestamp, method, path, body_str)
    return {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": sign,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": API_PASSPHRASE,
        "Content-Type": "application/json"
    }

# === GET CURRENT POSITIONS ===
def get_position(symbol):
    path = f"/api/mix/v1/position/singlePosition"
    url = BASE_URL + path
    params = {
        "symbol": symbol,
        "marginCoin": "USDT"
    }
    timestamp = str(int(time.time() * 1000))
    query = f"symbol={symbol}&marginCoin=USDT"
    sign = generate_signature(timestamp, "GET", path + "?" + query, "")
    headers = {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": sign,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": API_PASSPHRASE
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json()

# === PLACE ORDER ===
def place_order(action, symbol, quantity, leverage):
    try:
        print(f"📊 Current Position Info: {get_position(symbol)}")

        side = "open_long" if action == "buy" else "open_short"
        opposite_side = "close_short" if action == "buy" else "close_long"

        # Step 1: Close opposite if exists
        close_resp = close_position(symbol, quantity, opposite_side)
        if close_resp:
            print("🔁 Closed opposite position")

        # Step 2: Open new order
        print("🟢 Placing new order...")
        path = "/api/mix/v1/order/placeOrder"
        url = BASE_URL + path
        body = {
            "symbol": symbol,
            "marginCoin": "USDT",
            "side": side,
            "orderType": "market",
            "size": str(quantity),
            "leverage": str(leverage),
            "clientOid": str(uuid.uuid4())
        }
        headers = get_headers("POST", path, body)
        response = requests.post(url, headers=headers, data=json.dumps(body))
        result = response.json()
        print(f"✅ Order Response: {result}")
        return result
    except Exception as e:
        print(f"❌ Exception: {e}")
        return {"error": str(e)}

# === CLOSE POSITION ===
def close_position(symbol, quantity, side):
    try:
        path = "/api/mix/v1/order/placeOrder"
        url = BASE_URL + path
        body = {
            "symbol": symbol,
            "marginCoin": "USDT",
            "side": side,
            "orderType": "market",
            "size": str(quantity),
            "clientOid": str(uuid.uuid4())
        }
        headers = get_headers("POST", path, body)
        response = requests.post(url, headers=headers, data=json.dumps(body))
        return response.json()
    except Exception as e:
        print(f"❌ Close Position Error: {e}")
        return None
