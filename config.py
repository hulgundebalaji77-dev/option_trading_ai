CONFIG = {
    "SYMBOL": "NIFTY",
    "LOT_SIZE": 50,
    "INITIAL_CAPITAL": 100000.0,
    "RISK_REWARD_RATIO": 2.0,       # 1:2 Risk to Reward
    "MIN_AI_CONFIDENCE": 0.70,      # किमान ७०% AI खात्री असेल तरच ट्रेड
    "MODEL_FILE": "nifty_ai_model.pkl",
    "TELEGRAM_BOT_TOKEN": "YOUR_BOT_TOKEN",  # ऐच्छिक
    "TELEGRAM_CHAT_ID": "YOUR_CHAT_ID",

    # Angel One SmartAPI क्रेडेंशियल्स:
    "ANGEL_API_KEY": "7H7EQMOW6JFK2OPXWZYGY7UCOA",
    "ANGEL_CLIENT_CODE": "B130919",
    "ANGEL_PASSWORD": "2727",
    "ANGEL_TOTP_TOKEN": "इथे_TOTP_QR_खालील_SECRET_KEY_टाका"
```[span_8](start_span)[span_8](end_span)[span_9](start_span)[span_9](end_span)

---

### TOTP Secret Key कुठे सापडेल?
तुमच्या ब्राउझरमध्ये *SmartAPI* चा टॅब उघडा आहे[span_10](start_span)[span_10](end_span). 
1. त्या टॅबमध्ये जाऊन *Enable TOTP* पेजवर जा.
2. तिथे जो QR कोड येतो, त्याच्या खाली *Secret Key* किंवा *Key for manual entry* लिहिलेली असते.
3. ती Secret Key कॉपी करून *ANGEL_TOTP_TOKEN* च्या समोर पेस्ट करा.

हे सेव्ह (Commit) केल्यानंतर *API Key* आणि *TOTP* दोन्ही योग्य मॅच होतील आणि ॲप थेट कनेक्ट होईल[span_11](start_span)[span_11](end_span)[span_12](start_span)[span_12](end_span).
