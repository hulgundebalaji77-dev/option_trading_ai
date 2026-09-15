import streamlit as st
import pandas as pd
import numpy as np
import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import feedparser
import requests
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

# NLTK डेटा डाऊनलोड
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon', quiet=True)

# --- १. इनलाइन Risk Engine ---
class RiskEngine:
    def _init_(self, rr_ratio=2.0, *args, **kwargs):
        self.rr = float(rr_ratio)

    def get_trade_levels(self, price, atr, action):
        atr_val = 20.0 if (atr is None or atr <= 0 or np.isnan(atr)) else float(atr)
        sl_points = round(max(atr_val * 1.5, 20.0), 1)
        tgt_points = round(sl_points * self.rr, 1)

        if action == "BUY_CE":
            sl = round(price - sl_points, 1)
            tgt = round(price + tgt_points, 1)
        elif action == "BUY_PE":
            sl = round(price + sl_points, 1)
            tgt = round(price - tgt_points, 1)
        else:
            return {}

        return {
            "entry": round(price, 1),
            "sl": sl,
            "target": tgt,
            "sl_pts": sl_points,
            "tgt_pts": tgt_points
        }

# --- २. इनलाइन Feature Engine ---
def extract_features(df):
    features = pd.DataFrame(index=df.index)
    features['returns'] = df['close'].pct_change()
    features['hl_spread'] = (df['high'] - df['low']) / df['close']
    
    ema9 = df['close'].ewm(span=9).mean()
    ema21 = df['close'].ewm(span=21).mean()
    features['ema_ratio'] = (ema9 / ema21) - 1.0

    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    features['rsi'] = 100 - (100 / (1 + rs))

    tr1 = df['high'] - df['low']
    tr2 = (df['high'] - df['close'].shift()).abs()
    tr3 = (df['low'] - df['close'].shift()).abs()
    features['atr'] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1).rolling(14).mean()
    return features.replace([np.inf, -np.inf], np.nan).fillna(0.0)

# --- ३. इनलाइन AI मॉडेल ---
class OptionAI:
    def _init_(self):
        self.clf = RandomForestClassifier(n_estimators=80, max_depth=4, random_state=42)

    def train(self, df, features):
        future_diff = df['close'].shift(-3) - df['close']
        conditions = [future_diff >= 25, future_diff <= -25]
        targets = np.select(conditions, [1, 2], default=0)

        clean_df = df.copy()
        clean_df['target'] = targets
        clean_df = clean_df.dropna()

        X = features.loc[clean_df.index].values
        y = clean_df['target'].values.astype(int)

        if len(np.unique(y)) < 2:
            y[0] = 1

        self.clf.fit(X, y)

    def predict(self, feature_row):
        try:
            x_in = np.asarray(feature_row.values, dtype=np.float64)
            pred = int(self.clf.predict(x_in)[-1])
            probs = self.clf.predict_proba(x_in)[-1]
            action_map = {0: "HOLD", 1: "BUY_CE", 2: "BUY_PE"}
            classes = list(self.clf.classes_)
            conf = float(probs[classes.index(pred)]) if pred in classes else 0.0
            return action_map.get(pred, "HOLD"), conf
        except Exception:
            return "HOLD", 0.0

# --- ४. इनलाइन Excel रिपोर्ट जनरेटर ---
def create_excel_report(trades_df, capital, filename="AI_Option_Report.xlsx"):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Trade Summary"
    
    fill_hdr = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    font_hdr = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    
    headers = list(trades_df.columns)
    ws.append(headers)
    for c_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=c_idx)
        cell.fill = fill_hdr
        cell.font = font_hdr
        cell.alignment = Alignment(horizontal="center")

    for r_idx, row in enumerate(trades_df.itertuples(index=False), start=2):
        for c_idx, val in enumerate(row, start=1):
            cell = ws.cell(row=r_idx, column=c_idx, value=val)
            cell.alignment = Alignment(horizontal="center")

    wb.save(filename)
    return filename

# --- ५. Streamlit UI Layout ---
st.set_page_config(page_title="AI Option Trading", page_icon="📈", layout="wide")
st.title("🤖 Nifty 50 AI Option Trading & Backtest System")

st.sidebar.header("⚙️ Strategy Parameters")
capital = st.sidebar.number_input("Starting Capital (₹)", value=100000, step=10000)
lot_size = st.sidebar.number_input("Lot Size (Nifty)", value=50, step=25)
rr_ratio = st.sidebar.slider("Risk-Reward Ratio", 1.0, 3.0, 2.0, 0.5)
min_conf = st.sidebar.slider("Minimum AI Confidence", 0.50, 0.90, 0.70, 0.05)

tab1, tab2, tab3 = st.tabs(["📊 Backtest Engine", "📰 Live News Sentiment", "📁 Export Reports"])

with tab1:
    st.subheader("Historical 5-Min Strategy Backtest")
    if st.button("🚀 Run Backtest Now", type="primary"):
        with st.spinner("डेटा प्रोसेस आणि AI मॉडेल ट्रेन होत आहे..."):
            np.random.seed(42)
            prices = np.cumprod(1 + np.random.normal(0.0001, 0.002, 1500)) * 24500
            df = pd.DataFrame({
                "datetime": pd.date_range("2026-06-01 09:15", periods=1500, freq="5min"),
                "open": prices,
                "high": prices * 1.002,
                "low": prices * 0.998,
                "close": prices,
                "volume": np.random.randint(1000, 15000, 1500)
            })

            features = extract_features(df)
            
            # AI मॉडेल ट्रेन
            split_idx = int(len(df) * 0.75)
            train_df = df.iloc[:split_idx]
            train_feats = features.iloc[:split_idx]
            
            ai = OptionAI()
            ai.train(train_df, train_feats)

            # बॅकटेस्ट चालवणे
            risk = RiskEngine(rr_ratio=rr_ratio)
            test_df = df.iloc[split_idx:]
            trades = []
            in_trade = False
            trade_type, entry_p, sl_p, tgt_p = None, 0, 0, 0
            curr_cap = float(capital)
            t_id = 1

            for i in range(len(test_df) - 1):
                curr = test_df.iloc[i]
                feat = features.loc[[test_df.index[i]]]

                if in_trade:
                    h, l = curr['high'], curr['low']
                    exit_p, res = None, None
                    if trade_type == "BUY_CE":
                        if l <= sl_p: exit_p, res = sl_p, "SL_HIT"
                        elif h >= tgt_p: exit_p, res = tgt_p, "TARGET_HIT"
                    elif trade_type == "BUY_PE":
                        if h >= sl_p: exit_p, res = sl_p, "SL_HIT"
                        elif l <= tgt_p: exit_p, res = tgt_p, "TARGET_HIT"

                    if exit_p:
                        pts = (exit_p - entry_p) if trade_type == "BUY_CE" else (entry_p - exit_p)
                        pnl = round(pts * lot_size, 2)
                        curr_cap += pnl
                        trades.append({
                            "Trade ID": f"TRD_{t_id:03d}",
                            "Action": trade_type,
                            "Entry Price": entry_p,
                            "Result": res,
                            "Points": round(pts, 2),
                            "Net P&L (₹)": pnl,
                            "Capital Balance (₹)": round(curr_cap, 2)
                        })
                        t_id += 1
                        in_trade = False

                if not in_trade:
                    action, conf = ai.predict(feat)
                    if action in ["BUY_CE", "BUY_PE"] and conf >= min_conf:
                        atr_v = feat['atr'].values[0]
                        levels = risk.get_trade_levels(curr['close'], atr_v, action)
                        trade_type = action
                        entry_p, sl_p, tgt_p = levels['entry'], levels['sl'], levels['target']
                        in_trade = True

            st.session_state['trades_df'] = pd.DataFrame(trades)
            st.success("✅ बॅकटेस्ट यशस्वीरित्या पूर्ण झाले!")

    if 'trades_df' in st.session_state and not st.session_state['trades_df'].empty:
        tdf = st.session_state['trades_df']
        wins = tdf[tdf["Result"] == "TARGET_HIT"]
        win_rate = (len(wins) / len(tdf)) * 100
        total_pnl = tdf["Net P&L (₹)"].sum()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Trades", len(tdf))
        col2.metric("Win Rate", f"{win_rate:.1f}%")
        col3.metric("Net P&L (₹)", f"₹{total_pnl:,.2f}", delta=f"{total_pnl:,.2f}")
        col4.metric("Ending Capital", f"₹{tdf['Capital Balance (₹)'].iloc[-1]:,.2f}")

        st.subheader("📈 Capital Growth (Equity Curve)")
        st.line_chart(tdf.set_index("Trade ID")["Capital Balance (₹)"])
        st.subheader("📋 Trade Logs")
        st.dataframe(tdf, use_container_width=True)

with tab2:
    st.subheader("Market News & Sentiment Radar")
    if st.button("🔄 Check Live News Sentiment"):
        with st.spinner("ताज्या बातम्या वाचल्या जात आहेत..."):
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                res = requests.get("https://news.google.com/rss/search?q=Nifty+50+Stock+Market+India&hl=en-IN&gl=IN&ceid=IN:en", headers=headers, timeout=10)
                feed = feedparser.parse(res.content)
                sia = SentimentIntensityAnalyzer()
                scores = [sia.polarity_scores(e.title)['compound'] for e in feed.entries[:8] if hasattr(e, 'title')]
                avg = sum(scores) / len(scores) if scores else 0.0
                
                sentiment = "BULLISH" if avg >= 0.10 else ("BEARISH" if avg <= -0.10 else "NEUTRAL")
                c1, c2 = st.columns(2)
                c1.metric("Overall Sentiment", sentiment)
                c2.metric("Sentiment Score", round(avg, 3))
                if sentiment == "BULLISH":
                    st.success("बाजारात तेजीचे संकेत आहेत (CE Bias).")
                elif sentiment == "BEARISH":
                    st.error("बाजारात मंदीचे संकेत आहेत (PE Bias).")
                else:
                    st.info("बाजार सध्या न्यूट्रल/साइडवेज आहे.")
            except Exception as e:
                st.warning(f"न्यूज लोड करताना अडचण: {e}")

with tab3:
    st.subheader("Download Formatted Excel Report")
    if 'trades_df' in st.session_state and not st.session_state['trades_df'].empty:
        fname = create_excel_report(st.session_state['trades_df'], capital)
        with open(fname, "rb") as f:
            st.download_button("📥 Download Excel P&L Report", f, file_name=fname, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.warning("आधी बॅकटेस्ट रन करा, त्यानंतर एक्सेल डाउनलोड करता येईल.")
