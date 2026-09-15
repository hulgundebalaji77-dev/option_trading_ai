import pandas as pd
import numpy as np

class FeatureEngine:
    @staticmethod
    def extract_features(df: pd.DataFrame, chain_df: pd.DataFrame = None) -> pd.DataFrame:
        features = pd.DataFrame(index=df.index)
        
        # Returns & Volatility
        features['returns'] = df['close'].pct_change()
        features['hl_spread'] = (df['high'] - df['low']) / df['close']
        
        # EMA Ratios
        ema9 = df['close'].ewm(span=9).mean()
        ema21 = df['close'].ewm(span=21).mean()
        ema50 = df['close'].ewm(span=50).mean()
        features['ema_fast_spread'] = (ema9 / ema21) - 1.0
        features['ema_trend_spread'] = (ema21 / ema50) - 1.0
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        features['rsi'] = 100 - (100 / (1 + rs))
        
        # ATR
        tr1 = df['high'] - df['low']
        tr2 = (df['high'] - df['close'].shift()).abs()
        tr3 = (df['low'] - df['close'].shift()).abs()
        features['atr'] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1).rolling(14).mean()
        
        # Option Chain PCR
        if chain_df is not None and not chain_df.empty:
            call_oi = chain_df[chain_df['option_type'] == 'CE']['open_interest'].sum()
            put_oi = chain_df[chain_df['option_type'] == 'PE']['open_interest'].sum()
            features['pcr'] = put_oi / (call_oi + 1e-9)
        else:
            features['pcr'] = 1.0
            
        return features.fillna(0)
