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
