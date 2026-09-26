import streamlit as st

# 1. आधी Streamlit Cloud Secrets तपासा, नसल्यास स्थानिक व्हॅल्यू वापरा
try:
    CONFIG = {
        "ANGEL_API_KEY": st.secrets["ANGEL_API_KEY"],
        "ANGEL_CLIENT_CODE": st.secrets["ANGEL_CLIENT_CODE"],
        "ANGEL_PASSWORD": st.secrets["ANGEL_PASSWORD"],
        "ANGEL_TOTP_TOKEN": st.secrets["ANGEL_TOTP_TOKEN"],
    }
except Exception:
    # स्थानिक (Local Testing) साठी बॅकअप:
    CONFIG = {
        "ANGEL_API_KEY": "YOUR_LOCAL_API_KEY",
        "ANGEL_CLIENT_CODE": "YOUR_LOCAL_CLIENT_CODE",
        "ANGEL_PASSWORD": "YOUR_LOCAL_PASSWORD",
        "ANGEL_TOTP_TOKEN": "YOUR_LOCAL_TOTP_TOKEN",
    }
