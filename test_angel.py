# test_angel.py
from datetime import datetime, timedelta
import pyotp
from SmartApi import SmartConnect
from config import CONFIG

print("--- Angel One लॉगिन तपासत आहे ---")

try:
    # 1. Credentials तपासणी
    api_key = CONFIG.get("ANGEL_API_KEY")
    client_code = CONFIG.get("ANGEL_CLIENT_CODE")
    password = CONFIG.get("ANGEL_PASSWORD")
    totp_secret = CONFIG.get("ANGEL_TOTP_TOKEN")

    # 2. TOTP तयार करणे
    totp = pyotp.TOTP(totp_secret).now()
    print(f"तयार झालेला OTP: {totp}")

    # 3. Session इनिशिअलाइज करणे
    smart_api = SmartConnect(api_key=api_key)
    session_data = smart_api.generateSession(client_code, password, totp)
    print(f"Session Response: {session_data}")

    if not session_data.get("status"):
        print(f"❌ लॉगिन अयशस्वी: {session_data.get('message')}")
        exit()

    print("✅ लॉगिन यशस्वी झाले! आता डेटा फेच करत आहे...")

    # 4. डेटा फेच टेस्ट (Nifty 50)
    to_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    from_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d 09:15")

    param = {
        "exchange": "NSE",
        "symboltoken": "99926000",
        "interval": "FIVE_MINUTE",
        "fromdate": from_date,
        "todate": to_date,
    }

    res = smart_api.getCandleData(param)
    print(f"Candle Data Response: {res}")

    if res and res.get("status") and res.get("data"):
        print(f"🎉 डेटा मिळाला! एकूण {len(res['data'])} कँडल्स मिळाल्या.")
    else:
        print(f"❌ डेटा मिळाला नाही: {res.get('message')}")

except Exception as e:
    print(f"⚠️ अपवाद (Exception): {e}")
