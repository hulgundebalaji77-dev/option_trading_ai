import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
import os

class OptionAIEngine:
    def _init_(self, model_path="nifty_ai_model.pkl"):
        self.model_path = model_path
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            min_samples_split=5,
            random_state=42
        )

    def prepare_labels(self, df: pd.DataFrame, target_pts=25):
        # 1: CE, 2: PE, 0: HOLD
        future_diff = df['close'].shift(-3) - df['close']
        conditions = [future_diff >= target_pts, future_diff <= -target_pts]
        df['target'] = np.select(conditions, [1, 2], default=0)
        # NaN किंवा इन्फिनिटी काढून टाकणे
        df = df.replace([np.inf, -np.inf], np.nan).dropna()
        return df

    def train_and_save(self, X: pd.DataFrame, y: pd.Series):
        # इंडेक्स जुळवणे
        common_idx = X.index.intersection(y.index)
        X_df = X.loc[common_idx].copy()
        y_s = y.loc[common_idx].copy()

        # सर्व NaN आणि इन्फिनिटी व्हॅल्यूज शून्य (0.0) करणे
        X_df = X_df.replace([np.inf, -np.inf], np.nan).fillna(0.0)
        X_clean = np.nan_to_num(X_df.values.astype(np.float64))
        y_clean = y_s.values.astype(int)

        if len(X_clean) < 10:
            print("ट्रेनिंगसाठी पुरेसा डेटा नाही.")
            return

        # Train-Test Split (Shuffle False for time-series)
        X_train, X_test, y_train, y_test = train_test_split(
            X_clean, y_clean, test_size=0.2, shuffle=False
        )

        # जर y_train मध्ये फक्त एकच क्लास असेल तर किमान डमी व्हॅल्यूज ॲड करून सेफ्टी देणे
        unique_classes = np.unique(y_train)
        if len(unique_classes) < 2:
            # किमान २ क्लास (0 आणि 1) असल्याची खात्री
            y_train[0] = 0
            y_train[1] = 1

        # फिट करणे
        self.model.fit(X_train, y_train)

        # सुरक्षित सेव्ह
        try:
            joblib.dump(self.model, self.model_path)
            print(f"✅ AI मॉडेल यशस्वीरित्या सेव्ह झाले: {self.model_path}")
        except Exception as e:
            print(f"मॉडेल सेव्ह एरर: {e}")

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
            x_in = np.nan_to_num(feat_clean.values.astype(np.float64))
            
            pred = int(self.model.predict(x_in)[-1])
            probs = self.model.predict_proba(x_in)[-1]

            action_map = {0: "HOLD", 1: "BUY_CE", 2: "BUY_PE"}
            action = action_map.get(pred, "HOLD")
            
            classes = list(self.model.classes_)
            confidence = float(probs[classes.index(pred)]) if pred in classes else 0.0
            return action, confidence
        except Exception:
            return "HOLD", 0.0
