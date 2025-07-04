import os
from bitget.rest.mix import MixClient

# Load credentials from environment variables
api_key = os.getenv("BITGET_API_KEY")
api_secret = os.getenv("BITGET_API_SECRET")
api_passphrase = os.getenv("BITGET_API_PASSPHRASE")

# Initialize Bitget client
client = MixClient(
    api_key=api_key,
    api_secret=api_secret,
    passphrase=api_passphrase,
    use_server_time=True,
    first=True
)

# Function to check current position
def get_current_position(symbol):
    try:
        response = client.mix_get_all_positions(productType="umcbl")
        positions = response['data']
        for pos in positions:
            if pos['symbol'] == symbol:
                long_pos = float(pos['long']['available']) if pos['long'] else 0
                short_pos = float(pos['short']['available']) if pos['short'] else 0
                if long_pos > 0:
                    return "long"
                elif short_pos > 0:
                    return "short"
                else:
                    return "none"
        return "none"
    except Exception as e:
        print(f"❌ Error checking position: {e}")
        return "error"

# Function to place a trade
def place_order(action, symbol, quantity, leverage):
    print(f"📩 Received webhook: action={action}, symbol={symbol}, qty={quantity}, leverage={leverage}")

    # Check existing position
    position_side = get_current_position(symbol)
    print(f"📊 Current position on {symbol}: {position_side}")

    # Close opposite position
    try:
        if action == "buy" and position_side == "short":
            print("🔁 Closing short position before opening long...")
            close_order = client.mix_place_order(
                symbol=symbol,
                productType="umcbl",
                marginMode="crossed",
                side="close_short",
                orderType="market",
                size=str(quantity),
                price="",
                reduceOnly=True
            )
            print(f"✅ Closed short position: {close_order}")

        elif action == "sell" and position_side == "long":
            print("🔁 Closing long position before opening short...")
            close_order = client.mix_place_order(
                symbol=symbol,
                productType="umcbl",
                marginMode="crossed",
                side="close_long",
                orderType="market",
                size=str(quantity),
                price="",
                reduceOnly=True
            )
            print(f"✅ Closed long position: {close_order}")
    except Exception as e:
        print(f"❌ Error closing position: {e}")

    # Set leverage
    try:
        leverage_response = client.mix_set_leverage(
            symbol=symbol,
            productType="umcbl",
            marginMode="crossed",
            leverage=leverage
        )
        print(f"⚙️ Leverage set to {leverage}x: {leverage_response}")
    except Exception as e:
        print(f"❌ Error setting leverage: {e}")

    # Open new position
    try:
        side = "open_long" if action == "buy" else "open_short"
        order_response = client.mix_place_order(
            symbol=symbol,
            productType="umcbl",
            marginMode="crossed",
            side=side,
            orderType="market",
            size=str(quantity),
            price="",
            reduceOnly=False
        )
        print(f"✅ New {action.upper()} order placed: {order_response}")
        return {
            "status": "success",
            "exchange_response": order_response
        }
    except Exception as e:
        print(f"❌ Order placement failed: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
