import requests
import time
import hmac
import hashlib
import base64
import json
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.bitget.com"
API_KEY = os.getenv("BITGET_API_KEY")
API_SECRET = os.getenv("BITGET_API_SECRET")
API_PASSPHRASE = os.getenv("BITGET_API_PASSPHRASE")

HEADERS = {
    "ACCESS-KEY": API_KEY,
    "ACCESS-PASSPHRASE": API_PASSPHRASE,
    "Content-Type": "application/json"
}

def generate_signature(timestamp, method, request_path, body):
    body_str = body if body else ""
    pre_hash = f"{timestamp}{method.upper()}{request_path}{body_str}"
    signature = hmac.new(
        API_SECRET.encode('utf-8'),
        pre_hash.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(signature).decode()

def send_signed_request(method, path, body_dict=None):
    timestamp = str(int(time.time() * 1000))
    body = json.dumps(body_dict) if body_dict else ""
    sign = generate_signature(timestamp, method, path, body)
    headers = HEADERS.copy()
    headers["ACCESS-TIMESTAMP"] = timestamp
    headers["ACCESS-SIGN"] = sign

    url = BASE_URL + path
    if method == "POST":
        res = requests.post(url, headers=headers, data=body)
    else:
        res = requests.get(url, headers=headers)

    return res.json()

def get_position(symbol):
    path = f"/api/mix/v1/position/singlePosition?symbol={symbol}&marginCoin=USDT"
    return send_signed_request("GET", path)

def close_position(symbol, side):
    path = "/api/mix/v1/order/close-position"
    body = {
        "symbol": symbol,
        "marginCoin": "USDT",
        "productType": "umcbl",
        "side": side
    }
    print("📉 Closing position...")
    return send_signed_request("POST", path, body)

def place_order(action, symbol, quantity, leverage):
    position_info = get_position(symbol)
    print("📊 Current Position Info:", position_info)

    if "data" in position_info and position_info["data"]:
        pos = position_info["data"]
        if pos["total"] != "0":
            current_side = pos["holdSide"]
            if (action == "buy" and current_side == "short") or (action == "sell" and current_side == "long"):
                close_position(symbol, "close_" + current_side)

    path = "/api/mix/v1/order/place-order"
    body = {
        "symbol": symbol,
        "marginCoin": "USDT",
        "side": action,
        "orderType": "market",
        "size": str(quantity),
        "productType": "umcbl",
        "leverage": str(leverage)
    }
    print("🟢 Placing order...")
    result = send_signed_request("POST", path, body)
    print("✅ Order Response:", result)
    return result
