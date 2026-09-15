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
            n_estimators=150,
            learning_rate=0.03,
            max_depth=4,
            random_state=42
        )

    def prepare_labels(self, df: pd.DataFrame, target_pts=25):
        # 1: CE, 2: PE, 0: HOLD
        future_diff = df['close'].shift(-3) - df['close']
        conditions = [future_diff >= target_pts, future_diff <= -target_pts]
        df['target'] = np.select(conditions, [1, 2], default=0)
        return df.dropna()

    def train_and_save(self, X: pd.DataFrame, y: pd.Series):
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
        self.model.fit(X_train, y_train)
        joblib.dump(self.model, self.model_path)
        print(f"✅ AI मॉडेल यशस्वीरित्या ट्रेन आणि सेव्ह झाले: {self.model_path}")

    def load_model(self):
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            return True
        return False

    def predict(self, feature_row: pd.DataFrame):
        pred = self.model.predict(feature_row)[-1]
        probs = self.model.predict_proba(feature_row)[-1]
        action_map = {0: "HOLD", 1: "BUY_CE", 2: "BUY_PE"}
        return action_map[pred], probs[pred]
