import requests
import time
import hmac
import hashlib
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
    pre_hash = f"{timestamp}{method}{request_path}{body}"
    return hmac.new(API_SECRET.encode(), pre_hash.encode(), hashlib.sha256).hexdigest()

def get_position(symbol):
    timestamp = str(int(time.time() * 1000))
    path = f"/api/mix/v1/position/singlePosition?symbol={symbol}&marginCoin=USDT"
    url = BASE_URL + path
    body = ""
    sign = generate_signature(timestamp, "GET", path, body)
    headers = HEADERS.copy()
    headers["ACCESS-TIMESTAMP"] = timestamp
    headers["ACCESS-SIGN"] = sign
    res = requests.get(url, headers=headers)
    data = res.json()
    return data

def close_position(symbol, side):
    timestamp = str(int(time.time() * 1000))
    path = "/api/mix/v1/order/close-position"
    url = BASE_URL + path
    body_dict = {
        "symbol": symbol,
        "marginCoin": "USDT",
        "productType": "umcbl",
        "side": side
    }
    body = json.dumps(body_dict)
    sign = generate_signature(timestamp, "POST", path, body)
    headers = HEADERS.copy()
    headers["ACCESS-TIMESTAMP"] = timestamp
    headers["ACCESS-SIGN"] = sign
    res = requests.post(url, headers=headers, data=body)
    print("📉 Closing position:", res.json())
    return res.json()

def place_order(action, symbol, quantity, leverage):
    # Check and close opposite position first
    position_info = get_position(symbol)
    print("📊 Current Position Info:", position_info)

    if "data" in position_info and position_info["data"]:
        pos = position_info["data"]
        if pos["total"] != "0":
            current_side = pos["holdSide"]
            if (action == "buy" and current_side == "short") or (action == "sell" and current_side == "long"):
                close_position(symbol, "close_" + current_side)

    # Place new order
    timestamp = str(int(time.time() * 1000))
    path = "/api/mix/v1/order/place-order"
    url = BASE_URL + path
    body_dict = {
        "symbol": symbol,
        "marginCoin": "USDT",
        "side": action,
        "orderType": "market",
        "size": str(quantity),
        "productType": "umcbl",
        "leverage": str(leverage)
    }
    body = json.dumps(body_dict)
    sign = generate_signature(timestamp, "POST", path, body)
    headers = HEADERS.copy()
    headers["ACCESS-TIMESTAMP"] = timestamp
    headers["ACCESS-SIGN"] = sign

    res = requests.post(url, headers=headers, data=body)
    print("✅ Order Response:", res.json())
    return res.json()
