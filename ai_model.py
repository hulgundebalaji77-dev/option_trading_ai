import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
import joblib
import os

class OptionAIEngine:
    def _init_(self, model_path="nifty_ai_model.pkl"):
        self.model_path = model_path
        self.model = XGBClassifier(
            n_estimators=100,
            learning_rate=0.03,
            max_depth=4,
            eval_metric="mlogloss",
            random_state=42
        )

    def prepare_labels(self, df: pd.DataFrame, target_pts=25):
        # 1: CE, 2: PE, 0: HOLD
        future_diff = df['close'].shift(-3) - df['close']
        conditions = [future_diff >= target_pts, future_diff <= -target_pts]
        df['target'] = np.select(conditions, [1, 2], default=0)
        return df.dropna()

    def train_and_save(self, X: pd.DataFrame, y: pd.Series):
        # Index alignment आणि स्वच्छ float डेटा तयार करणे
        common_idx = X.index.intersection(y.index)
        X_clean = X.loc[common_idx].astype(np.float32).values
        y_clean = y.loc[common_idx].astype(np.int64).values

        if len(X_clean) == 0:
            print("ट्रेनिंगसाठी डेटा उपलब्ध नाही!")
            return

        # Train-Test Split
        X_train, X_test, y_train, y_test = train_test_split(
            X_clean, y_clean, test_size=0.2, shuffle=False
        )

        # Fit मॉडेल
        self.model.fit(X_train, y_train)
        
        # सेव्ह करणे
        joblib.dump(self.model, self.model_path)
        print(f"✅ AI मॉडेल यशस्वीरित्या सेव्ह झाले: {self.model_path}")

    def load_model(self):
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            return True
        return False

    def predict(self, feature_row: pd.DataFrame):
        # NumPy ॲरेमध्ये रूपांतर
        if isinstance(feature_row, pd.DataFrame):
            x_in = feature_row.astype(np.float32).values
        else:
            x_in = np.array(feature_row, dtype=np.float32)

        pred = int(self.model.predict(x_in)[-1])
        probs = self.model.predict_proba(x_in)[-1]
        
        action_map = {0: "HOLD", 1: "BUY_CE", 2: "BUY_PE"}
        action = action_map.get(pred, "HOLD")
        confidence = float(probs[pred]) if pred < len(probs) else 0.0

        return action, confidence
