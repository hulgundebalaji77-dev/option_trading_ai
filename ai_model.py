import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
import os

class OptionAIEngine:
    def _init_(self, model_path="nifty_ai_model.pkl"):
        self.model_path = model_path
        # Scikit-learn चा मजबूत आणि सुपरफास्ट Random Forest क्लासिफायर
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
        return df.dropna()

    def train_and_save(self, X: pd.DataFrame, y: pd.Series):
        # इंडेक्स जुळवणे आणि सुरक्षित डेटा तयार करणे
        common_idx = X.index.intersection(y.index)
        X_clean = X.loc[common_idx].fillna(0).values
        y_clean = y.loc[common_idx].values.astype(int)

        if len(X_clean) == 0:
            print("ट्रेनिंगसाठी डेटा सापडला नाही.")
            return

        # Train Split
        X_train, X_test, y_train, y_test = train_test_split(
            X_clean, y_clean, test_size=0.2, shuffle=False
        )

        # मॉडेल फिट करणे
        self.model.fit(X_train, y_train)

        # सेव्ह करणे
        joblib.dump(self.model, self.model_path)
        print(f"✅ AI मॉडेल यशस्वीरित्या ट्रेन आणि सेव्ह झाले: {self.model_path}")

    def load_model(self):
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                return True
            except Exception:
                return False
        return False

    def predict(self, feature_row: pd.DataFrame):
        if isinstance(feature_row, pd.DataFrame):
            x_in = feature_row.fillna(0).values
        else:
            x_in = np.array(feature_row).reshape(1, -1)

        pred = int(self.model.predict(x_in)[-1])
        probs = self.model.predict_proba(x_in)[-1]

        action_map = {0: "HOLD", 1: "BUY_CE", 2: "BUY_PE"}
        action = action_map.get(pred, "HOLD")
        
        # सुरक्षित Probability मिळवणे
        classes = list(self.model.classes_)
        confidence = float(probs[classes.index(pred)]) if pred in classes else 0.0

        return action, confidence
