# The Official Credit Registry (Updated with User Data)

# Your exact map
CREDITS_MAP = {
    'BCS401': 3, 'BCS402': 4, 'BCS403': 4, 'BCSL404': 1, 'BBOC407': 2,
    'BUHK408': 1, 'BPEK459': 0, 'BCS405A': 3, 'BDSL456B': 1, 'BCSL405': 1, 'BCSL406': 1,
    # Add common 3rd sem if needed
    'BCS301': 4, 'BCS302': 4, 'BCS303': 4
}

def get_course_info(course_code: str):
    """
    Returns the credit weight for a given subject code.
    """
    code = course_code.strip().upper()
    
    # Direct lookup
    if code in CREDITS_MAP:
        return {"name": f"Subject {code}", "credits": CREDITS_MAP[code]}
    
    # Fallback: Try to guess based on VTU Lab conventions (usually 1 credit)
    if "L" in code and len(code) > 5:
         return {"name": f"Lab {code}", "credits": 1}

    # Default fallback
    print(f"⚠️ Warning: Credits for {code} not found. Assuming 3.")
    return {"name": "Unknown Course", "credits": 3}