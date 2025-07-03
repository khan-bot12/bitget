# bitget_trade.py

import requests
import time
import hmac
import hashlib
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("BITGET_API_KEY")
API_SECRET = os.getenv("BITGET_API_SECRET")
API_PASSPHRASE = os.getenv("BITGET_API_PASSPHRASE")
BASE_URL = "https://api.bitget.com"

def get_timestamp():
    return str(int(time.time() * 1000))

def sign(method, path, timestamp, body=""):
    msg = f"{timestamp}{method}{path}{body}"
    signature = hmac.new(
        API_SECRET.encode("utf-8"),
        msg.encode("utf-8"),
        digestmod=hashlib.sha256
    ).hexdigest()
    return signature

def place_futures_order(action, symbol, quantity, leverage):
    path = "/api/mix/v1/order/place"
    url = BASE_URL + path
    timestamp = get_timestamp()

    side = "open_long" if action.lower() == "buy" else "open_short"

    body = {
        "symbol": symbol,
        "marginCoin": "USDT",
        "size": str(quantity),
        "price": "",  # market order
        "side": side,
        "orderType": "market",
        "productType": "umcbl",
        "leverage": str(leverage)
    }

    body_json = json.dumps(body)
    headers = {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": sign("POST", path, timestamp, body_json),
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": API_PASSPHRASE,
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, data=body_json)
    return response.json()
