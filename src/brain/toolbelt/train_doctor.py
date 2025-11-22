import pandas as pd
import numpy as np
import xgboost as xgb
import os

# 1. Configuration
MODEL_PATH = os.path.join("src", "brain", "toolbelt", "doctor_model.json")

def train_model():
    print("👨‍⚕️ The Doctor is studying previous student records...")

    # 2. Generate Synthetic Data (Simulating UCI Student Performance Dataset)
    # Features: [StudyTime, Failures, Absences, FreeTime, Health]
    # Target: [Burnout_Risk] (0 = Safe, 1 = At Risk)
    
    data_size = 1000
    np.random.seed(42)
    
    X = pd.DataFrame({
        'study_time': np.random.randint(1, 5, data_size),    # 1=Low, 4=High
        'failures': np.random.randint(0, 4, data_size),      # Past failures
        'absences': np.random.randint(0, 20, data_size),     # Days absent
        'free_time': np.random.randint(1, 6, data_size),     # 1=Low, 5=High
        'health': np.random.randint(1, 6, data_size)         # 1=Bad, 5=Good
    })

    # Logic: High failures + High absences + Low study = Burnout
    y = np.where(
        (X['failures'] > 0) | (X['absences'] > 10) | (X['study_time'] == 1), 
        1, 0
    )

    # 3. Train XGBoost Model (The "Brain")
    print("🧠 Training XGBoost Classifier...")
    model = xgb.XGBClassifier(
        n_estimators=50,
        max_depth=3,
        learning_rate=0.1,
        objective='binary:logistic'
    )
    model.fit(X, y)

    # 4. Save the Model
    model.save_model(MODEL_PATH)
    print(f"✅ Doctor Model saved to: {MODEL_PATH}")

if __name__ == "__main__":
    train_model()