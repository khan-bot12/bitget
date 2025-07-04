def place_order(action, symbol, quantity, leverage):
    try:
        position_info = get_position(symbol)
        print("📊 Current Position Info:", position_info)

        current_side = None
        if "data" in position_info:
            pos_data = position_info["data"]
            if isinstance(pos_data, list) and len(pos_data) > 0:
                current_side = pos_data[0].get("holdSide")

        opposite_side = {
            "buy": "short",
            "sell": "long"
        }

        # Close opposite position if open
        if current_side == opposite_side.get(action):
            print(f"🔁 Closing {current_side} position before opening {action}...")

            close_side = "close_short" if current_side == "short" else "close_long"

            close_body = {
                "symbol": symbol,
                "marginCoin": "USDT",
                "size": str(quantity),
                "side": close_side,
                "orderType": "market",
                "force": "gtc",
                "clientOid": str(uuid.uuid4())
            }

            close_url = "/api/mix/v1/order/placeOrder"
            body_json = json.dumps(close_body)
            h_close = headers("POST", close_url, body_json)

            r_close = requests.post(BASE_URL + close_url, headers=h_close, data=body_json)
            print("❌ Close Response:", r_close.json())
            time.sleep(0.5)  # small delay

        # Now place the new order
        open_side = "open_long" if action == "buy" else "open_short"

        open_body = {
            "symbol": symbol,
            "marginCoin": "USDT",
            "size": str(quantity),
            "side": open_side,
            "orderType": "market",
            "force": "gtc",
            "leverage": str(leverage),
            "clientOid": str(uuid.uuid4())
        }

        body = json.dumps(open_body)
        h = headers("POST", "/api/mix/v1/order/placeOrder", body)

        print("🟢 Placing new order...")
        r = requests.post(BASE_URL + "/api/mix/v1/order/placeOrder", headers=h, data=body)
        print("✅ Order Response:", r.json())
        return r.json()

    except Exception as e:
        print(f"❌ Exception: {e}")
        return {"error": str(e)}
