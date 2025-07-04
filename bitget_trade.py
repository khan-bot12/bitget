import time
import uuid
import hmac
import hashlib
import base64
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("BITGET_API_KEY")
API_SECRET = os.getenv("BITGET_API_SECRET")
API_PASSPHRASE = os.getenv("BITGET_API_PASSPHRASE")
BASE_URL = "https://api.bitget.com"
PRODUCT_TYPE = "umcbl"  # USDT-M futures

def sign_request(timestamp, method, path, body=""):
    message = f"{timestamp}{method}{path}{body}"
    signature = hmac.new(API_SECRET.encode(), message.encode(), hashlib.sha256).digest()
    return base64.b64encode(signature).decode()

def get_headers(method, path, body=""):
    timestamp = str(int(time.time() * 1000))
    signature = sign_request(timestamp, method, path, body)
    return {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": API_PASSPHRASE,
        "Content-Type": "application/json"
    }

def get_position(symbol):
    path = f"/api/mix/v1/position/singlePosition?productType={PRODUCT_TYPE}&symbol={symbol}"
    url = BASE_URL + path
    headers = get_headers("GET", path)
    response = requests.get(url, headers=headers)
    data = response.json()
    print("📊 Current Position Info:", data)
    if data["code"] == "00000" and data["data"]:
        return data["data"][0]["holdSide"]
    return None

def set_leverage(symbol, leverage):
    path = "/api/mix/v1/account/setLeverage"
    body = {
        "symbol": symbol,
        "marginCoin": "USDT",
        "leverage": str(leverage),
        "holdSide": "long"
    }
    body_json = json.dumps(body)
    headers = get_headers("POST", path, body_json)
    requests.post(BASE_URL + path, headers=headers, data=body_json)

    body["holdSide"] = "short"
    body_json = json.dumps(body)
    headers = get_headers("POST", path, body_json)
    requests.post(BASE_URL + path, headers=headers, data=body_json)

def place_order(action, symbol, quantity, leverage):
    import json
    try:
        print(f"📦 Parsed → action: {action}, symbol: {symbol}, quantity: {quantity}, leverage: {leverage}")
        set_leverage(symbol, leverage)

        current_pos = get_position(symbol)
        print("🔍 Current side:", current_pos)

        # Close opposite position if any
        if action == "buy" and current_pos == "short":
            print("🔁 Closing short position")
            close_order("buy", symbol, quantity, "close_short")
            time.sleep(1)
        elif action == "sell" and current_pos == "long":
            print("🔁 Closing long position")
            close_order("sell", symbol, quantity, "close_long")
            time.sleep(1)

        # Place new order
        print("🟢 Placing order...")
        return create_order(
            action="buy" if action == "buy" else "sell",
            symbol=symbol,
            quantity=quantity,
            hold_side="open_long" if action == "buy" else "open_short"
        )
    except Exception as e:
        print("❌ Exception:", str(e))
        return {"error": str(e)}

def close_order(side, symbol, quantity, hold_side):
    return create_order(side, symbol, quantity, hold_side)

def create_order(action, symbol, quantity, hold_side):
    import json
    path = "/api/mix/v1/order/placeOrder"
    body = {
        "symbol": symbol,
        "marginCoin": "USDT",
        "size": str(quantity),
        "side": action,
        "orderType": "market",
        "clientOid": str(uuid.uuid4()),
        "holdSide": hold_side
    }
    body_json = json.dumps(body)
    headers = get_headers("POST", path, body_json)
    response = requests.post(BASE_URL + path, headers=headers, data=body_json)
    result = response.json()
    print("✅ Order Response:", result)
    return result
