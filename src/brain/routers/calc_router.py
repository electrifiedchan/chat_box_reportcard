from fastapi import APIRouter, HTTPException
from typing import List
from src.brain.toolbelt.planner import Planner, CourseInput, SgpaResult

router = APIRouter()

# 1. The Calculation Endpoint
@router.post("/calculate_sgpa", response_model=SgpaResult)
async def calculate_sgpa(courses: List[CourseInput]):
    """
    Takes a list of courses (Name, Credits, Grade) and returns the exact SGPA.
    """
    try:
        # Call the static method we wrote in planner.py
        result = Planner.calculate_sgpa(courses)
        
        print(f"🧮 Calculated SGPA: {result.sgpa}")
        return result

    except Exception as e:
        print(f"❌ Calculation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))