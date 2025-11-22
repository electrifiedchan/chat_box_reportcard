import pandas as pd
import xgboost as xgb
import os

# 1. Configuration
CSV_PATH = os.path.join("data", "student-mat.csv")
MODEL_PATH = os.path.join("src", "brain", "toolbelt", "doctor_model.json")

def train_real_model():
    print("👨‍⚕️ The Doctor is analyzing the UCI Dataset...")

    # 2. Load Real Data
    if not os.path.exists(CSV_PATH):
        print("❌ Error: student-mat.csv not found in data folder!")
        return

    # The UCI dataset uses ';' as a separator, not ','
    df = pd.read_csv(CSV_PATH, sep=';')
    
    print(f"✅ Loaded {len(df)} student records.")

    # 3. Select Features (The "Symptoms")
    # We map UCI column names to our API's expected names
    features = df[['studytime', 'failures', 'absences', 'freetime', 'health', 'Dalc']].copy()
    features.columns = ['study_time', 'failures', 'absences', 'free_time', 'health', 'alcohol_daily']

    # 4. Define the Target (The "Diagnosis")
    # In UCI, G3 is the final grade (0-20). < 10 is a Fail.
    # Logic: If G3 < 10, Burnout Risk = 1 (True)
    y = df['G3'].apply(lambda grade: 1 if grade < 10 else 0)

    # 5. Train the Brain
    print("🧠 Training XGBoost on real patterns...")
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        objective='binary:logistic'
    )
    model.fit(features, y)

    # 6. Save the Model
    model.save_model(MODEL_PATH)
    print(f"✅ REAL Doctor Model saved to: {MODEL_PATH}")

if __name__ == "__main__":
    train_real_model()