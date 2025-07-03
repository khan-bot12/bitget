# Bitget Auto-Trader Bot

A webhook-based FastAPI bot to receive TradingView alerts and execute Bitget USDT-M futures trades.

## How to Use

1. Deploy to [Render.com](https://render.com) (auto-detects render.yaml)
2. Add required environment variables:
   - BITGET_API_KEY
   - BITGET_API_SECRET
   - BITGET_API_PASSPHRASE
   - SECRET_TOKEN (optional)

3. Set your TradingView webhook URL to:
   https://your-bot-name.onrender.com/webhook

Example alert JSON:
```json
{
  "action": "buy",
  "symbol": "SOLUSDT",
  "quantity": 15,
  "leverage": 5,
  "token": "your_shared_secret_token"
}


4. Click **“Commit new file”**

---

✅ Done — now your GitHub repo will be fully ready for Render.

Let me know if you want me to check your repo or help you push it via terminal instead.
