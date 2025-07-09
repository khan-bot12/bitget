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

API_KEY = os.getenv("BITGET_API_KEY")
API_SECRET = os.getenv("BITGET_API_SECRET")
API_PASSPHRASE = os.getenv("BITGET_API_PASSPHRASE")
BASE_URL = "https://api.bitget.com"

def generate_signature(timestamp, method, request_path, body):
    prehash = f"{timestamp}{method}{request_path}{body}"
    hash_bytes = hmac.new(API_SECRET.encode(), prehash.encode(), hashlib.sha256).digest()
    signature = base64.b64encode(hash_bytes).decode()
    return signature

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
        print(f"🔁 Close {side.upper()} → response: {response.json()}")
        return response.json()
    except Exception as e:
        print(f"❌ Close Position Error: {e}")
        return None

def smart_trade(action, symbol, quantity, leverage):
    print(f"📩 smart_trade → Action: {action.upper()}, Symbol: {symbol}, Qty: {quantity}, Leverage: {leverage}")

    try:
        position_data = get_position(symbol)
        positions = position_data.get("data", [])
        long_pos = 0
        short_pos = 0

        for p in positions:
            side = p.get("holdSide")
            available = float(p.get("available", 0) or 0)
            if side == "long":
                long_pos = available
            elif side == "short":
                short_pos = available

        print(f"📊 Position Check → LONG: {long_pos}, SHORT: {short_pos}")

        if action == "buy":
            if long_pos > 0:
                print("✅ Already in LONG → No action taken.")
                return {"status": "already_long"}
            if short_pos > 0:
                print(f"🔁 Closing SHORT of {short_pos}")
                close_position(symbol, short_pos, "close_short")
            print("🟢 Opening LONG position...")
            side = "open_long"

        elif action == "sell":
            if short_pos > 0:
                print("✅ Already in SHORT → No action taken.")
                return {"status": "already_short"}
            if long_pos > 0:
                print(f"🔁 Closing LONG of {long_pos}")
                close_position(symbol, long_pos, "close_long")
            print("🔴 Opening SHORT position...")
            side = "open_short"

        else:
            print(f"❌ Invalid action: {action}")
            return {"error": "invalid action"}

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
        print(f"✅ New order response: {result}")
        return result

    except Exception as e:
        print(f"❌ Error in smart_trade: {e}")
        return {"error": str(e)}
