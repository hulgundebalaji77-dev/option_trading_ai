import streamlit as st
import pandas as pd
import numpy as np
import io
from feature_engine import FeatureEngine
from ai_model import OptionAIEngine
from risk_engine import RiskEngine
from news_engine import NewsEngine
from historical_backtest import get_or_create_5min_data
from excel_reporter import generate_excel_report

st.set_page_config(
    page_title="AI Option Trading Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("🤖 Nifty 50 AI Option Trading & Backtest System")
st.markdown("XGBoost Machine Learning + Sentiment NLP + 1:2 Risk-Reward Architecture")

# Sidebar Configuration
st.sidebar.header("⚙️ Strategy Parameters")
capital = st.sidebar.number_input("Starting Capital (₹)", value=100000, step=10000)
lot_size = st.sidebar.number_input("Lot Size (Nifty)", value=50, step=25)
rr_ratio = st.sidebar.slider("Risk-Reward Ratio", min_value=1.0, max_value=3.0, value=2.0, step=0.5)
min_conf = st.sidebar.slider("Minimum AI Confidence", min_value=0.50, max_value=0.90, value=0.70, step=0.05)

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Backtest Engine", "📰 Live News Sentiment", "📁 Export Reports"])

# --- TAB 1: BACKTEST ENGINE ---
with tab1:
    st.subheader("Historical 5-Min Strategy Backtest")
    
    if st.button("🚀 Run Backtest Now", type="primary"):
        with st.spinner("डेटा प्रोसेस आणि AI मॉडेल ट्रेन होत आहे..."):
            df = get_or_create_5min_data(days=45)
            fe = FeatureEngine()
            features = fe.extract_features(df)
            
            ai = OptionAIEngine()
            labeled_df = ai.prepare_labels(df.copy(), target_pts=25)
            
            split_idx = int(len(labeled_df) * 0.80)
            train_df = labeled_df.iloc[:split_idx]
            test_df = labeled_df.iloc[split_idx:]
            
            X_train = features.loc[train_df.index]
            y_train = train_df['target']
            ai.train_and_save(X_train, y_train)
            
            # Backtesting
            risk = RiskEngine(rr_ratio=rr_ratio)
            trades = []
            in_trade = False
            trade_type = None
            entry_price, sl_price, tgt_price = 0, 0, 0
            entry_time = None
            trade_id = 1
            curr_cap = float(capital)
            
            test_indices = list(test_df.index)
            for i in range(len(test_indices) - 1):
                idx = test_indices[i]
                curr_candle = df.loc[idx]
                curr_feat = features.loc[[idx]]
                
                if in_trade:
                    high, low = curr_candle['high'], curr_candle['low']
                    exit_price, res = None, None
                    
                    if trade_type == "BUY_CE":
                        if low <= sl_price: exit_price, res = sl_price, "SL_HIT"
                        elif high >= tgt_price: exit_price, res = tgt_price, "TARGET_HIT"
                    elif trade_type == "BUY_PE":
                        if high >= sl_price: exit_price, res = sl_price, "SL_HIT"
                        elif low <= tgt_price: exit_price, res = tgt_price, "TARGET_HIT"
                        
                    if exit_price:
                        pts = (exit_price - entry_price) if trade_type == "BUY_CE" else (entry_price - exit_price)
                        pnl = round(pts * lot_size, 2)
                        curr_cap += pnl
                        trades.append({
                            "Trade ID": f"TRD_{trade_id:04d}",
                            "Date": str(curr_candle['datetime'])[:10],
                            "Time": str(entry_time)[11:16],
                            "Action": trade_type,
                            "Spot Price": entry_price,
                            "Result": res,
                            "Points": round(pts, 2),
                            "Net P&L (₹)": pnl,
                            "Capital Balance (₹)": round(curr_cap, 2)
                        })
                        trade_id += 1
                        in_trade = False
                        
                if not in_trade:
                    action, conf = ai.predict(curr_feat)
                    if action in ["BUY_CE", "BUY_PE"] and conf >= min_conf:
                        atr_val = curr_feat['atr'].values[0]
                        levels = risk.get_trade_levels(curr_candle['close'], atr_val, action)
                        trade_type = action
                        entry_price, sl_price, tgt_price = levels['entry'], levels['sl'], levels['target']
                        entry_time = curr_candle['datetime']
                        in_trade = True
                        
            st.session_state['trades_df'] = pd.DataFrame(trades)
            st.success("✅ बॅकटेस्ट पूर्ण झाले!")

    if 'trades_df' in st.session_state and not st.session_state['trades_df'].empty:
        tdf = st.session_state['trades_df']
        wins = tdf[tdf["Result"] == "TARGET_HIT"]
        losses = tdf[tdf["Result"] == "SL_HIT"]
        win_rate = (len(wins) / len(tdf)) * 100
        total_pnl = tdf["Net P&L (₹)"].sum()
        
        # Metrics Display
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Trades", len(tdf))
        col2.metric("Win Rate", f"{win_rate:.1f}%")
        col3.metric("Net P&L (₹)", f"₹{total_pnl:,.2f}", delta=f"{total_pnl:,.2f}")
        col4.metric("Ending Capital", f"₹{tdf['Capital Balance (₹)'].iloc[-1]:,.2f}")
        
        # Equity Curve Chart
        st.subheader("📈 Capital Growth (Equity Curve)")
        st.line_chart(tdf.set_index("Trade ID")["Capital Balance (₹)"])
        
        # Trade Log Table
        st.subheader("📋 Trade Logs")
        st.dataframe(tdf, use_container_width=True)

# --- TAB 2: LIVE NEWS SENTIMENT ---
with tab2:
    st.subheader("Market News & Sentiment Radar")
    if st.button("🔄 Check Live News Sentiment"):
        with st.spinner("बाजारपेठेतील ताज्या बातम्या वाचल्या जात आहेत..."):
            news = NewsEngine()
            sent_data = news.get_live_sentiment()
            
            c1, c2 = st.columns(2)
            c1.metric("Overall Sentiment", sent_data['sentiment'])
            c2.metric("Sentiment Score", sent_data['score'])
            
            if sent_data['sentiment'] == "BULLISH":
                st.success("बाजारात तेजीचे वातावरण आहे (Bullish Bias for CE).")
            elif sent_data['sentiment'] == "BEARISH":
                st.error("बाजारात मंदीचे वातावरण आहे (Bearish Bias for PE).")
            else:
                st.info("बाजार सध्या न्यूट्रल/साइडवेज आहे.")

# --- TAB 3: EXPORT REPORTS ---
with tab3:
    st.subheader("Download Formatted Excel Report")
    if 'trades_df' in st.session_state and not st.session_state['trades_df'].empty:
        filename = "AI_Backtest_Streamlit_Report.xlsx"
        generate_excel_report(st.session_state['trades_df'], initial_capital=capital, output_name=filename)
        
        with open(filename, "rb") as f:
            st.download_button(
                label="📥 Download Excel P&L Report",
                data=f,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.warning("कृपया आधी बॅकटेस्ट रन करा, त्यानंतर एक्सेल डाउनलोड करता येईल.")
