import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
import os

class OptionAIEngine:
    def _init_(self, model_path="nifty_ai_model.pkl"):
        self.model_path = model_path
        self.model = None

    def prepare_labels(self, df: pd.DataFrame, target_pts=25):
        # 1: CE, 2: PE, 0: HOLD
        future_diff = df['close'].shift(-3) - df['close']
        conditions = [future_diff >= target_pts, future_diff <= -target_pts]
        df['target'] = np.select(conditions, [1, 2], default=0)
        df = df.replace([np.inf, -np.inf], np.nan).dropna()
        return df

    def train_and_save(self, X: pd.DataFrame, y: pd.Series):
        # स्वच्छ आणि व्हॅलिड डेटा तयार करणे
        common_idx = X.index.intersection(y.index)
        X_df = X.loc[common_idx].copy().replace([np.inf, -np.inf], np.nan).fillna(0.0)
        y_s = y.loc[common_idx].copy()

        X_data = np.asarray(X_df.values, dtype=np.float64)
        y_data = np.asarray(y_s.values, dtype=np.int64)

        if len(X_data) < 10:
            return

        # Train/Test Split
        X_train, X_test, y_train, y_test = train_test_split(
            X_data, y_data, test_size=0.2, shuffle=False
        )

        # फ्रेश मॉडेल इन्स्टन्स तयार करून फिट करणे
        clf = RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            min_samples_split=5,
            random_state=42
        )
        
        clf.fit(X_train, y_train)
        self.model = clf

        # सेव्ह करणे
        try:
            joblib.dump(clf, self.model_path)
            print(f"✅ AI मॉडेल यशस्वीरित्या सेव्ह झाले: {self.model_path}")
        except Exception as e:
            print(f"सेव्ह एरर: {e}")

    def load_model(self):
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                return True
            except Exception:
                return False
        return False

    def predict(self, feature_row: pd.DataFrame):
        try:
            if self.model is None:
                if not self.load_model():
                    return "HOLD", 0.0

            feat_clean = feature_row.replace([np.inf, -np.inf], np.nan).fillna(0.0)
            x_in = np.asarray(feat_clean.values, dtype=np.float64)

            pred = int(self.model.predict(x_in)[-1])
            probs = self.model.predict_proba(x_in)[-1]

            action_map = {0: "HOLD", 1: "BUY_CE", 2: "BUY_PE"}
            action = action_map.get(pred, "HOLD")

            classes = list(self.model.classes_)
            conf = float(probs[classes.index(pred)]) if pred in classes else 0.0
            return action, conf
        except Exception:
            return "HOLD", 0.0
