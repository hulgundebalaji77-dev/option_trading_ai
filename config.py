# सुरुवातीला जिथे CONFIG इम्पोर्ट केला आहे, तिथे हा बदल करा:
try:
    # स्थानिक रनसाठी (Local testing)
    from config import CONFIG
    ANGEL_API_KEY = CONFIG.get("ANGEL_API_KEY")
    ANGEL_CLIENT_CODE = CONFIG.get("ANGEL_CLIENT_CODE")
    ANGEL_PASSWORD = CONFIG.get("ANGEL_PASSWORD")
    ANGEL_TOTP_TOKEN = CONFIG.get("ANGEL_TOTP_TOKEN")
except Exception:
    # Streamlit Cloud साठी (Deployment)
    ANGEL_API_KEY = st.secrets.get("ANGEL_API_KEY")
    ANGEL_CLIENT_CODE = st.secrets.get("ANGEL_CLIENT_CODE")
    ANGEL_PASSWORD = st.secrets.get("ANGEL_PASSWORD")
    ANGEL_TOTP_TOKEN = st.secrets.get("ANGEL_TOTP_TOKEN")
