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
    print(f"🟢 Placing new order: {action.upper()} {quantity} {symbol} @ {leverage}x")

    side = "open_long" if action == "buy" else "open_short"

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

# === CLOSE POSITION ===
def close_position(symbol, quantity, side):
    print(f"🔁 Closing position: {side} {quantity} {symbol}")
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
    result = response.json()
    print(f"✅ Close order response: {result}")
    return result

# === SMART TRADE ===
def smart_trade(action, symbol, quantity, leverage):
    # Add suffix if missing
    if not symbol.endswith("_UMCBL"):
        symbol = f"{symbol}_UMCBL"

    print(f"📩 smart_trade → Action: {action.upper()}, Symbol: {symbol}, Qty: {quantity}, Leverage: {leverage}")

    try:
        position_data = get_position(symbol)
        print("🔍 Position API Raw:", position_data)

        long_pos = 0
        short_pos = 0

        if 'data' in position_data and isinstance(position_data['data'], list):
            for pos in position_data['data']:
                side = pos.get('holdSide')
                available = float(pos.get('available', 0))
                if side == 'long':
                    long_pos += available
                elif side == 'short':
                    short_pos += available

        print(f"➡️ Current: Long: {long_pos}, Short: {short_pos}")

        if action == "buy" and long_pos > 0:
            print("✅ Long already open. No new trade needed.")
            return {"msg": "Long already open. No new trade placed."}

        if action == "sell" and short_pos > 0:
            print("✅ Short already open. No new trade needed.")
            return {"msg": "Short already open. No new trade placed."}

        if action == "buy" and short_pos > 0:
            print("🔁 Closing short before opening long...")
            close_position(symbol, quantity, "close_short")

        if action == "sell" and long_pos > 0:
            print("🔁 Closing long before opening short...")
            close_position(symbol, quantity, "close_long")

    except Exception as e:
        print(f"❌ Failed to check/close positions: {e}")

    print("🟢 Opening new position...")
    return place_order(action, symbol, quantity, leverage)
