import pandas as pd
import numpy as np
from config import CONFIG
from feature_engine import FeatureEngine
from news_engine import NewsEngine
from ai_model import OptionAIEngine
from risk_engine import RiskEngine
from excel_reporter import generate_excel_report

def main():
    print("🚀 AI Option Trading Pipeline सुरू होत आहे...")
    import pandas as pd
from angel_client import get_angel_session, get_nifty_candles
from ai_model import OptionAIEngine

# 1. Angel One कनेक्ट करा
api = get_angel_session()

# 2. कँडल डेटा मिळवा व DataFrame मध्ये रूपांतरित करा
raw_data = get_nifty_candles(api)
if raw_data and raw_data.get('status'):
    cols = ["timestamp", "open", "high", "low", "close", "volume"]
    df = pd.DataFrame(raw_data['data'], columns=cols)
    
    # 3. AI Engine चालवा
    ai = OptionAIEngine()
    # df = feature_engine.calculate_indicators(df)
    # prediction = ai.predict(df)
    print("डेटा यशस्वीरित्या AI मॉडेलला जोडला गेला.")
   
    # १. डमी/सॅम्पल कॅन्डल डेटा (टेस्टिंगसाठी)
    # जेव्हा लाइव्ह कराल, तेव्हा इथे ब्रोकर API वरून डेटा येईल
    np.random.seed(42)
    sample_size = 200
    prices = np.cumprod(1 + np.random.normal(0, 0.002, sample_size)) * 24500
    sample_df = pd.DataFrame({
        "open": prices,
        "high": prices * 1.002,
        "low": prices * 0.998,
        "close": prices,
        "volume": np.random.randint(1000, 5000, sample_size)
    })

    # २. फीचर्स तयार करणे
    fe = FeatureEngine()
    features = fe.extract_features(sample_df)

    # ३. मॉडेल ट्रेनिंग (मॉडेल नसेल तर ट्रेन करा)
    ai = OptionAIEngine(CONFIG["MODEL_FILE"])
    if not ai.load_model():
        print("मॉडेल सापडले नाही, नवीन मॉडेल ट्रेन होत आहे...")
        labeled_df = ai.prepare_labels(sample_df.copy(), target_pts=20)
        X = features.loc[labeled_df.index]
        y = labeled_df['target']
        ai.train_and_save(X, y)
    else:
        print("✅ सेव्ह केलेले AI मॉडेल लोड झाले.")

    # ४. लाइव्ह न्यूज सेंटिमेंट तपासणे
    news = NewsEngine()
    sentiment_data = news.get_live_sentiment()
    print(f"📰 ताज्या बातम्यांचे सेंटिमेंट: {sentiment_data['sentiment']} (Score: {sentiment_data['score']})")

    # ५. ताज्या कॅन्डलवर AI प्रेडिक्शन
    latest_feature = features.iloc[[-1]]
    signal, conf = ai.predict(latest_feature)
    print(f"🤖 AI डिसिजन: {signal} | खात्री (Confidence): {round(conf*100, 2)}%")

    # ६. रिस्क मॅनेजमेंट आणि लेव्हल्स
    risk = RiskEngine(rr_ratio=CONFIG["RISK_REWARD_RATIO"])
    current_price = sample_df['close'].iloc[-1]
    current_atr = features['atr'].iloc[-1]

    if conf >= CONFIG["MIN_AI_CONFIDENCE"] and signal != "HOLD":
        trade_levels = risk.get_trade_levels(current_price, current_atr, signal)
        print("\n🎯 --- TRADE EXECUTED ---")
        print(f"प्रकार     : {signal}")
        print(f"एंट्री भाव  : {trade_levels['entry']}")
        print(f"Stop Loss  : {trade_levels['sl']} (-{trade_levels['sl_pts']} pts)")
        print(f"Target     : {trade_levels['target']} (+{trade_levels['tgt_pts']} pts)")
    else:
        print("\n⏳ सध्या स्पष्ट ट्रेड सिग्नल नाही किंवा खात्री कमी आहे. (No Trade)")

if _name_ == "_main_":
    main()
