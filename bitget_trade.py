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

# === TRAILING SL CONFIG ===
TRAILING_SL_CONFIG = {
    "SOLUSDT_UMCBL": [
        {"trigger": 0.5, "sl": 0.0},
        {"trigger": 1.0, "sl": 0.5},
        {"trigger": 2.0, "sl": 1.0}
    ],
    "ETHUSDT_UMCBL": [
        {"trigger": 0.6, "sl": 0.2},
        {"trigger": 1.2, "sl": 0.6},
        {"trigger": 2.5, "sl": 1.0}
    ]
}

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

# === Entry Price Helpers ===
def save_entry_price(symbol, entry_price):
    with open(f"{symbol}_entry.txt", "w") as f:
        f.write(str(entry_price))

def get_current_price(symbol):
    url = f"{BASE_URL}/api/mix/v1/market/ticker?symbol={symbol}"
    response = requests.get(url)
    return response.json().get("data", {}).get("last")

# === Trailing SL Monitor for Symbol ===
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

def monitor_symbol_trailing_stop(symbol):
    steps = TRAILING_SL_CONFIG.get(symbol, [])
    if not steps:
        print(f"⚠️ No trailing config for {symbol}")
        return

    while True:
        try:
            with open(f"{symbol}_entry.txt", "r") as f:
                entry_price = float(f.read())

            current_price = float(get_current_price(symbol))
            direction = get_position(symbol).get("data", [{}])[0].get("holdSide", "")

            for step in reversed(steps):
                trigger = step["trigger"]
                sl = step["sl"]

                if direction == "long" and current_price >= entry_price * (1 + trigger / 100):
                    place_stop_loss(symbol, "long", entry_price * (1 + sl / 100))
                    break
                elif direction == "short" and current_price <= entry_price * (1 - trigger / 100):
                    place_stop_loss(symbol, "short", entry_price * (1 - sl / 100))
                    break

        except FileNotFoundError:
            return
        except Exception as e:
            print(f"❌ Trailing SL error for {symbol}: {e}")

        time.sleep(5)

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

    # Start trailing SL monitor for this trade
    threading.Thread(target=monitor_symbol_trailing_stop, args=(symbol,), daemon=True).start()

    return result
