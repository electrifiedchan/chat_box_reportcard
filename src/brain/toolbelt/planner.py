from pydantic import BaseModel
from typing import List, Optional

# 1. The Official VTU Grading Scale (From PDF Clause 220B 6.1)
# We hardcode this to ensure 100% accuracy. Phi-3 doesn't guess.
GRADE_POINTS = {
    "O": 10,   # Outstanding
    "A+": 9,   # Excellent
    "A": 8,    # Very Good
    "B+": 7,   # Good
    "B": 6,    # Above Average
    "C": 5,    # Average
    "P": 4,    # Pass
    "F": 0,    # Fail
    "AB": 0,   # Absent
}

class CourseInput(BaseModel):
    name: str
    credits: int
    grade: str  # User inputs "A", "B+", etc.

class SgpaResult(BaseModel):
    total_credits: int
    earned_points: int
    sgpa: float
    status: str

class Planner:
    """
    The Logic Unit. It performs the strict math that the LLM cannot be trusted with.
    """
    
    @staticmethod
    def calculate_sgpa(courses: List[CourseInput]) -> SgpaResult:
        total_credits = 0
        total_points = 0
        failed_courses = []

        print(f"🧮 Calculating SGPA for {len(courses)} courses...")

        for course in courses:
            # Normalize grade input (handle "a+" vs "A+")
            grade_key = course.grade.upper().strip()
            
            if grade_key not in GRADE_POINTS:
                # If invalid grade, assume 0 but log warning
                print(f"⚠️ Warning: Unknown grade '{grade_key}' for {course.name}. Treating as 0.")
                points = 0
            else:
                points = GRADE_POINTS[grade_key]

            # The Formula: Σ(Credit * GradePoint)
            product = course.credits * points
            
            total_credits += course.credits
            total_points += product
            
            # Track failures for advice
            if points == 0:
                failed_courses.append(course.name)

        if total_credits == 0:
            return SgpaResult(total_credits=0, earned_points=0, sgpa=0.0, status="No credits registered")

        # Final Calculation (Rounded to 2 decimals as per PDF)
        sgpa = round(total_points / total_credits, 2)
        
        # Determine Status
        status = "Pass"
        if failed_courses:
            status = f"Fail ({', '.join(failed_courses)})"

        return SgpaResult(
            total_credits=total_credits,
            earned_points=total_points,
            sgpa=sgpa,
            status=status
        )