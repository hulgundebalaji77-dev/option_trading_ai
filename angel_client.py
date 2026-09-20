from SmartApi import SmartConnect
import pyotp
import config

def get_angel_session():
    try:
        # SmartConnect इनिशियलाइझ करा
        smart_api = SmartConnect(api_key=config.ANGEL_API_KEY)
        
        # TOTP जनरेट करा
        totp = pyotp.TOTP(config.ANGEL_TOTP_TOKEN).now()
        
        # सेशन लॉगिन
        data = smart_api.generateSession(
            config.ANGEL_CLIENT_CODE, 
            config.ANGEL_PASSWORD, 
            totp
        )
        
        if data['status']:
            print("Angel One लॉगिन यशस्वी झाले!")
            return smart_api
        else:
            print("लॉगिन अयशस्वी:", data['message'])
            return None
            
    except Exception as e:
        print(f"एरर आला: {e}")
        return None

# हिस्टॉरिकल किंवा लाईव्ह कॅन्डल डेटा मिळवण्यासाठी फंक्शन
def get_nifty_candles(smart_api, token="99926000", interval="FIVE_MINUTE", from_date="2026-09-15 09:15", to_date="2026-09-20 15:30"):
    historic_param = {
        "exchange": "NSE",
        "symboltoken": token,
        "interval": interval,
        "fromdate": from_date,
        "todate": to_date
    }
    candle_data = smart_api.getCandleData(historic_param)
    return candle_data
