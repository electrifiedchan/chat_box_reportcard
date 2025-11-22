from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import xgboost as xgb
import pandas as pd
import os

router = APIRouter()

# 1. Load the Trained Brain
MODEL_PATH = os.path.join("src", "brain", "toolbelt", "doctor_model.json")
doctor_model = xgb.XGBClassifier()

# Load immediately if file exists
if os.path.exists(MODEL_PATH):
    doctor_model.load_model(MODEL_PATH)
    print("👨‍⚕️ The Real Doctor is IN.")
else:
    print("⚠️ Doctor model not found! Did you run train_real_doctor.py?")

# 2. Patient Intake Form (Updated for UCI Dataset)
class StudentHealth(BaseModel):
    study_time: int     # 1 (<2 hrs) to 4 (>10 hrs)
    failures: int       # 0 to 3
    absences: int       # 0 to 93
    free_time: int      # 1 (Low) to 5 (High)
    health: int         # 1 (Bad) to 5 (Good)
    alcohol_daily: int  # 1 (Very Low) to 5 (Very High) <-- NEW FIELD

# 3. Diagnosis Endpoint
@router.post("/predict_burnout")
async def predict_burnout(student: StudentHealth):
    """
    Analyzes student habits (including alcohol/health) to predict failure risk.
    """
    try:
        # Convert input to DataFrame (Must match training columns exactly)
        input_data = pd.DataFrame([{
            'study_time': student.study_time,
            'failures': student.failures,
            'absences': student.absences,
            'free_time': student.free_time,
            'health': student.health,
            'alcohol_daily': student.alcohol_daily
        }])

        # Predict (0 = Safe, 1 = At Risk of G3 < 10)
        prediction = doctor_model.predict(input_data)[0]
        probability = doctor_model.predict_proba(input_data)[0][1] # Confidence score

        # Customize advice based on the specific trigger
        advice = "Keep up the good work!"
        if student.alcohol_daily > 3:
            advice = "High daily alcohol consumption is strongly linked to grade drops. Consider cutting back."
        elif student.failures > 0:
            advice = "Past failures are a risk factor. Focus on backlog clearance."
        elif student.absences > 10:
            advice = "Your attendance is low. You are at risk of being detained (DX Grade)."

        status = "High Risk of Failure 🚩" if prediction == 1 else "On Track ✅"
        
        return {
            "diagnosis": status,
            "risk_probability": f"{round(probability * 100, 1)}%",
            "advice": advice
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnosis failed: {str(e)}")