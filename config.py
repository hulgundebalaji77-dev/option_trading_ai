# कॉन्फिगरेशन आणि ट्रेडिंग नियम
CONFIG = {
    "SYMBOL": "NIFTY",
    "LOT_SIZE": 50,
    "INITIAL_CAPITAL": 100000.0,
    "RISK_REWARD_RATIO": 2.0,      # 1:2 Risk to Reward
    "MIN_AI_CONFIDENCE": 0.70,     # किमान ७०% AI खात्री असेल तरच ट्रेड
    "MODEL_FILE": "nifty_ai_model.pkl",
    "TELEGRAM_BOT_TOKEN": "YOUR_BOT_TOKEN",  # ऐच्छिक (अलर्ट्ससाठी)
    "TELEGRAM_CHAT_ID": "YOUR_CHAT_ID"
}
ANGEL_API_KEY = "तुमची_API_KEY"
ANGEL_CLIENT_CODE = "तुमचा_CLIENT_CODE"
ANGEL_PASSWORD = "तुमचा_PIN_किंवा_PASSWORD"
ANGEL_TOTP_TOKEN = "तुमचा_TOTP_QR_चा_SECRET_KEY"
