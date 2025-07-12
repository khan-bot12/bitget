import time
import hmac
import hashlib
import base64
import json
import uuid
import requests
import os
import threading
from dotenv import load_dotenv

load_dotenv()

# === ENV VARIABLES ===
API_KEY = os.getenv("BITGET_API_KEY")
API_SECRET = os.getenv("BITGET_API_SECRET")
API_PASSPHRASE = os.getenv("BITGET_API_PASSPHRASE")
BASE_URL = "https://api.bitget.com"

# === SIGNATURE ===
def generate_signature(timestamp, method, request_path, body):
    prehash = f"{timestamp}{method}{request_path}{body}"
    hash_bytes = hmac.new(API_SECRET.encode(), prehash.encode(), hashlib.sha256).digest()
    signature = base64.b64encode(hash_bytes).decode()
    return signature

# === HEADERS ===
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

# === GET POSITION ===
def get_position(symbol):
    path = "/api/mix/v1/position/singlePosition"
    url = BASE_URL + path
    params = {"symbol": symbol, "marginCoin": "USDT"}
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

# === CLOSE POSITION ===
def close_position(symbol, quantity, side):
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
    print(f"✅ Close order response: {response.json()}")
    return response.json()

# === PLACE ORDER ===
def place_order(action, symbol, quantity, leverage):
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
    print(f"✅ New order response: {response.json()}")
    return response.json()

# === SMART TRADE ===
def smart_trade(action, symbol, quantity, leverage):
    print(f"📩 smart_trade → Action: {action.upper()}, Symbol: {symbol}, Qty: {quantity}, Leverage: {leverage}")

    pos = get_position(symbol)
    print(f"🔍 Position API Raw: {pos}")

    long_pos = 0
    short_pos = 0

    if pos["code"] == "00000" and pos.get("data"):
        for p in pos["data"]:
            side = p.get("holdSide")
            size = float(p.get("total", 0))
            if side == "long":
                long_pos += size
            elif side == "short":
                short_pos += size

    print(f"➡️ Current: Long: {long_pos}, Short: {short_pos}")

    if action == "buy":
        if short_pos > 0:
            print(f"🔁 Closing short before opening long ({short_pos} contracts)...")
            close_position(symbol, short_pos, "close_short")
        if long_pos > 0:
            print("✅ Long already open. No new trade needed.")
            return {"msg": "Long already open. No new trade placed."}

    elif action == "sell":
        if long_pos > 0:
            print(f"🔁 Closing long before opening short ({long_pos} contracts)...")
            close_position(symbol, long_pos, "close_long")
        if short_pos > 0:
            print("✅ Short already open. No new trade needed.")
            return {"msg": "Short already open. No new trade placed."}

    print("🟢 Opening new position...")
    result = place_order(action, symbol, quantity, leverage)
    entry_price = float(get_current_price(symbol))
    save_entry_price(symbol, entry_price)
    return result

# === Entry Price Helpers ===
def save_entry_price(symbol, entry_price):
    with open(f"{symbol}_entry.txt", "w") as f:
        f.write(str(entry_price))

def get_current_price(symbol):
    url = f"{BASE_URL}/api/mix/v1/market/ticker?symbol={symbol}"
    response = requests.get(url)
    return response.json().get("data", {}).get("last")

# === Trailing SL Monitor (Fixed TP/SL Logic) ===
def place_stop_loss(symbol, hold_side, stop_price):
    path = "/api/mix/v1/plan/placeTPSL"
    url = BASE_URL + path
    body = {
        "symbol": symbol,
        "marginCoin": "USDT",
        "planType": "pos_profit",
        "triggerPrice": str(stop_price),
        "holdSide": hold_side,
        "triggerType": "mark_price"
    }
    headers = get_headers("POST", path, body)
    response = requests.post(url, headers=headers, data=json.dumps(body))
    print(f"📉 SL Updated: {symbol} → {stop_price}")
    return response.json()

def monitor_trailing_stop():
    while True:
        for file in os.listdir("."):
            if file.endswith("_entry.txt"):
                symbol = file.replace("_entry.txt", "")
                try:
                    with open(file, "r") as f:
                        entry_price = float(f.read())
                    current_price = float(get_current_price(symbol))
                    side = "long" if current_price > entry_price else "short"

                    print(f"📊 Checking: {symbol} | Entry: {entry_price} | Current: {current_price} | Side: {side}")

                    sl_pct = 0.25 / 100
                    if side == "long":
                        sl_price = entry_price * (1 - sl_pct)
                    else:
                        sl_price = entry_price * (1 + sl_pct)

                    place_stop_loss(symbol, side, sl_price)

                except Exception as e:
                    print(f"❌ SL Monitor Error for {symbol}: {e}")

        time.sleep(1)

threading.Thread(target=monitor_trailing_stop, daemon=True).start()
