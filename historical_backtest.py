import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from feature_engine import FeatureEngine
from ai_model import OptionAIEngine
from risk_engine import RiskEngine
from excel_reporter import generate_excel_report

def get_or_create_5min_data(file_path="nifty_5min_data.csv", days=60) -> pd.DataFrame:
    """जर CSV फाईल उपलब्ध असेल तर ती वाचेल, अन्यथा ६० दिवसांचा ५-मिनिट डेटा तयार करेल"""
    if os.path.exists(file_path):
        print(f"📂 उपलब्ध फाईल लोड होत आहे: {file_path}")
        df = pd.read_csv(file_path)
        df['datetime'] = pd.to_datetime(df['datetime'])
        return df

    print(f"⚙️ '{file_path}' सापडली नाही. ६० दिवसांचा ५-मिनिट हिस्टॉरिकल डेटा जनरेट होत आहे...")
    np.random.seed(101)
    
    records = []
    base_price = 24500.0
    start_date = datetime.now() - timedelta(days=days)
    
    current_day = start_date
    while current_day <= datetime.now():
        # शनिवार आणि रविवार वगळणे
        if current_day.weekday() < 5:
            # ०९:१५ ते १५:३० (एकूण ७५ कॅण्डल्स प्रति दिवस)
            day_time = current_day.replace(hour=9, minute=15, second=0, microsecond=0)
            for _ in range(75):
                drift = np.random.normal(0.00005, 0.0018)
                close_p = round(base_price * (1 + drift), 2)
                high_p = round(close_p + abs(np.random.normal(5, 8)), 2)
                low_p = round(close_p - abs(np.random.normal(5, 8)), 2)
                open_p = round(np.random.uniform(low_p, high_p), 2)
                vol = np.random.randint(5000, 45000)

                records.append({
                    "datetime": day_time,
                    "open": open_p,
                    "high": high_p,
                    "low": low_p,
                    "close": close_p,
                    "volume": vol
                })
                base_price = close_p
                day_time += timedelta(minutes=5)
        current_day += timedelta(days=1)
        
    df = pd.DataFrame(records)
    df.to_csv(file_path, index=False)
    print(f"💾 ऐतिहासिक ५-मिनिट डेटा सेव्ह झाला: {file_path} (एकूण कॅण्डल्स: {len(df)})")
    return df

def run_backtest_pipeline(csv_path="nifty_5min_data.csv"):
    # १. ५-मिनिट डेटा लोड करणे
    df = get_or_create_5min_data(csv_path)

    # २. फीचर्स काढणे
    print("🔄 टेक्निकल आणि व्होलॅटॅलिटी फीचर्स तयार होत आहेत...")
    fe = FeatureEngine()
    features = fe.extract_features(df)

    # ३. ट्रेनिंग आणि टेस्टिंग डेटा स्प्लिट (८०% ट्रेन, २०% टेस्ट)
    ai = OptionAIEngine()
    labeled_df = ai.prepare_labels(df.copy(), target_pts=25)
    
    split_idx = int(len(labeled_df) * 0.80)
    train_df = labeled_df.iloc[:split_idx]
    test_df = labeled_df.iloc[split_idx:]

    X_train = features.loc[train_df.index]
    y_train = train_df['target']

    print(f"🧠 AI मॉडेल {len(train_df)} कॅण्डल्सवर ट्रेन होत आहे...")
    ai.train_and_save(X_train, y_train)

    # ४. २०% अनसीन डेटावर बॅकटेस्टिंग सुरू करणे
    print(f"📊 {len(test_df)} कॅण्डल्सवर लाइव्ह सिम्युलेशन बॅकटेस्ट सुरू...")
    risk = RiskEngine(rr_ratio=2.0)
    lot_size = 50
    capital = 100000.0

    trades = []
    in_trade = False
    trade_type = None
    entry_price, sl_price, tgt_price = 0.0, 0.0, 0.0
    entry_time = None
    trade_id = 1

    test_indices = list(test_df.index)

    for i in range(len(test_indices) - 1):
        idx = test_indices[i]
        curr_candle = df.loc[idx]
        curr_feat = features.loc[[idx]]

        # ट्रेड सुरू असल्यास एक्झिट तपासणे
        if in_trade:
            high = curr_candle['high']
            low = curr_candle['low']
            exit_price = None
            result = None

            if trade_type == "BUY_CE":
                if low <= sl_price:
                    exit_price = sl_price
                    result = "SL_HIT"
                elif high >= tgt_price:
                    exit_price = tgt_price
                    result = "TARGET_HIT"
            elif trade_type == "BUY_PE":
                if high >= sl_price:
                    exit_price = sl_price
                    result = "SL_HIT"
                elif low <= tgt_price:
                    exit_price = tgt_price
                    result = "TARGET_HIT"

            if exit_price:
                pts = (exit_price - entry_price) if trade_type == "BUY_CE" else (entry_price - exit_price)
                pnl = round(pts * lot_size, 2)
                capital += pnl
                
                trades.append({
                    "Trade ID": f"TRD_{trade_id:04d}",
                    "Date": str(curr_candle['datetime'])[:10],
                    "Entry Time": str(entry_time)[11:16],
                    "Exit Time": str(curr_candle['datetime'])[11:16],
                    "Action": trade_type,
                    "Spot Price": entry_price,
                    "SL": sl_price,
                    "Target": tgt_price,
                    "Result": result,
                    "Points": round(pts, 2),
                    "Net P&L (₹)": pnl,
                    "Balance (₹)": round(capital, 2)
                })
                trade_id += 1
                in_trade = False

        # नवीन ट्रेड एंट्री (सिग्नल आणि कॉन्फिडन्स >= ७०%)
        if not in_trade:
            action, conf = ai.predict(curr_feat)
            if action in ["BUY_CE", "BUY_PE"] and conf >= 0.70:
                atr_val = curr_feat['atr'].values[0]
                levels = risk.get_trade_levels(curr_candle['close'], atr_val, action)
                
                trade_type = action
                entry_price = levels['entry']
                sl_price = levels['sl']
                tgt_price = levels['target']
                entry_time = curr_candle['datetime']
                in_trade = True

    trades_df = pd.DataFrame(trades)

    # ५. रिझल्ट्स सारांश दाखवणे
    if not trades_df.empty:
        wins = trades_df[trades_df["Result"] == "TARGET_HIT"]
        losses = trades_df[trades_df["Result"] == "SL_HIT"]
        win_rate = (len(wins) / len(trades_df)) * 100
        total_pnl = trades_df["Net P&L (₹)"].sum()

        print("\n" + "="*45)
        print("          📈 BACKTEST PERFORMANCE SUMMARY")
        print("="*45)
        print(f"एकूण ट्रेड्स (Total Trades) : {len(trades_df)}")
        print(f"जिंकलेले ट्रेड्स (Wins)      : {len(wins)}")
        print(f"हरलेले ट्रेड्स (Losses)      : {len(losses)}")
        print(f"विन रेट (Win Rate)         : {win_rate:.2f}%")
        print(f"निव्वळ नफा (Net P&L)       : ₹{total_pnl:,.2f}")
        print(f"अंतिम भांडवल (Final Cap)    : ₹{capital:,.2f}")
        print("="*45)

        # ऑटोमॅटिक एक्सेल रिपोर्ट जनरेट करणे
        today_str = datetime.now().strftime("%Y-%m-%d")
        excel_name = f"Backtest_5Min_Report_{today_str}.xlsx"
        generate_excel_report(trades_df, initial_capital=100000.0, output_name=excel_name)
    else:
        print("⚠️ दिलेल्या निकषांवर (७०% Confidence) एकही ट्रेड ट्रिगर झाला नाही.")

if __name__ == "__main__":
    run_backtest_pipeline()
