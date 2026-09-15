import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
import joblib
import os

class OptionAIEngine:
    def _init_(self, model_path="nifty_ai_model.pkl"):
        self.model_path = model_path
        # अत्यंत स्थिर आणि वेगवान ML अल्गोरिदम
        self.model = GradientBoostingClassifier(
            n_estimators=60,
            learning_rate=0.05,
            max_depth=3,
            random_state=42
        )

    def prepare_labels(self, df: pd.DataFrame, target_pts=25):
        # 1: CE, 2: PE, 0: HOLD
        future_diff = df['close'].shift(-3) - df['close']
        conditions = [future_diff >= target_pts, future_diff <= -target_pts]
        df['target'] = np.select(conditions, [1, 2], default=0)
        df = df.replace([np.inf, -np.inf], np.nan).dropna()
        return df

    def train_and_save(self, X: pd.DataFrame, y: pd.Series):
        # इंडेक्स जुळवून स्वच्छ ॲरे तयार करणे
        common_idx = X.index.intersection(y.index)
        X_df = X.loc[common_idx].copy().replace([np.inf, -np.inf], np.nan).fillna(0.0)
        y_s = y.loc[common_idx].copy()

        X_mat = np.asarray(X_df.values, dtype=np.float64)
        y_arr = np.asarray(y_s.values, dtype=np.int32)

        if len(X_mat) < 10:
            return

        # Train/Test Split
        X_train, X_test, y_train, y_test = train_test_split(
            X_mat, y_arr, test_size=0.2, shuffle=False
        )

        # मॉडेल फिटिंग
        self.model.fit(X_train, y_train)

        # सेव्ह करणे
        try:
            joblib.dump(self.model, self.model_path)
        except Exception:
            pass

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
