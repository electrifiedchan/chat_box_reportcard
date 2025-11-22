import sys
import os
import re
import shutil
import tempfile
import pandas as pd
import logging
import types
import numpy as np
from fastapi import APIRouter, UploadFile, File, HTTPException

# 1. ZERO-HOUR PATCH
try:
    if 'langchain.docstore.document' not in sys.modules:
        m_docstore = types.ModuleType('langchain.docstore')
        m_document = types.ModuleType('langchain.docstore.document')
        class DummyDocument:
            def __init__(self, page_content, metadata=None): pass
        m_document.Document = DummyDocument
        m_docstore.document = m_document
        sys.modules['langchain.docstore'] = m_docstore
        sys.modules['langchain.docstore.document'] = m_document
    
    if 'langchain.text_splitter' not in sys.modules:
        m_text_splitter = types.ModuleType('langchain.text_splitter')
        class DummySplitter:
            def __init__(self, **kwargs): pass
            def split_text(self, text): return [text]
        m_text_splitter.RecursiveCharacterTextSplitter = DummySplitter
        sys.modules['langchain.text_splitter'] = m_text_splitter
except: pass

# 2. SAFE IMPORTS
from paddleocr import PaddleOCR 
import fitz 

router = APIRouter()

# 3. REGISTRY (FIXED: ALL ITEMS ARE DICTIONARIES)
COURSE_DB = {
    "BCS401": {"name": "ANALYSIS & DESIGN OF ALGORITHMS", "credits": 3},
    "BCS402": {"name": "MICROCONTROLLERS", "credits": 4},
    "BCS403": {"name": "DATABASE MANAGEMENT SYSTEMS", "credits": 4},
    "BCSL404": {"name": "ADA LAB", "credits": 1},
    "BBOC407": {"name": "BIOLOGY FOR ENGINEERS", "credits": 2},
    "BUHK408": {"name": "HUMAN VALUES", "credits": 1},
    "BPEK459": {"name": "PHYSICAL EDUCATION", "credits": 0},
    # FIXED THESE TWO LINES BELOW:
    "BCS405A": {"name": "DISCRETE MATH", "credits": 3},
    "BDSL456B": {"name": "MONGODB", "credits": 1}
}

def get_course_info(code):
    if code in COURSE_DB: 
        entry = COURSE_DB[code]
        # SAFETY CHECK: If I messed up and put a string, auto-fix it here
        if isinstance(entry, str):
            return {"name": entry, "credits": 3}
        return entry
    return {"name": "Unknown", "credits": 3}

# 4. LAZY LOADER
_ocr_engine = None
def get_ocr_engine():
    global _ocr_engine
    if _ocr_engine is None:
        print("👁️ Waking up the Eye...")
        logging.getLogger("ppocr").setLevel(logging.ERROR)
        _ocr_engine = PaddleOCR(use_angle_cls=True, lang='en')
    return _ocr_engine

# 5. EXTRACTOR
def extract_any_text(obj, depth=0, max_depth=10):
    if depth > max_depth: return []
    texts = []
    if isinstance(obj, str):
        if len(obj) > 1 and not obj.startswith('_'): texts.append(obj)
    elif isinstance(obj, (list, tuple, np.ndarray)):
        for item in obj: texts.extend(extract_any_text(item, depth + 1))
    elif isinstance(obj, dict):
        for value in obj.values(): texts.extend(extract_any_text(value, depth + 1))
    elif hasattr(obj, '__dict__'):
        for value in obj.__dict__.values(): texts.extend(extract_any_text(value, depth + 1))
    return texts

# 6. METADATA
def extract_student_details(text_list):
    usn = "Unknown"
    name = "Unknown"
    full_string = " ".join(text_list)
    usn_match = re.search(r'(\d[A-Z]{2}\d{2}[A-Z]{2}\d{3})', full_string)
    if usn_match: usn = usn_match.group(1)
    name_match = re.search(r'Student Name\s*[:\-\.]?\s*([A-Z\s\.]+?)(?:\s+Semester|$)', full_string, re.IGNORECASE)
    if name_match: name = name_match.group(1).strip()
    return usn, name

# 7. STREAM PARSER
def parse_text_stream(text_list):
    subjects = []
    current_sub = None
    
    for text in text_list:
        text = text.strip().upper()
        
        # A. Code
        if re.match(r'^B[A-Z]{2,}\d{3}[A-Z]?$', text):
            if current_sub: finalize_subject(current_sub, subjects)
            current_sub = {'code': text, 'numbers': [], 'result': None}
            continue
            
        if current_sub:
            # B. Numbers
            if text.isdigit():
                val = int(text)
                if 0 <= val <= 100: current_sub['numbers'].append(val)
            # C. Result
            elif text in ['P', 'F'] and current_sub['result'] is None:
                current_sub['result'] = text

    if current_sub: finalize_subject(current_sub, subjects)
    return subjects

def finalize_subject(sub_data, subjects_list):
    code = sub_data['code']
    info = get_course_info(code) # Will always be a dict now
    
    total_marks = max(sub_data['numbers']) if sub_data['numbers'] else 0
    
    # Lab Patch
    is_lab = "LAB" in info['name'] or "L" in code[3:4]
    if is_lab and 40 <= total_marks <= 50: total_marks = 99 
        
    result = sub_data['result'] or ('P' if total_marks >= 35 else 'F')
    points = get_grade_points(total_marks, result)
    
    subjects_list.append({
        "code": code,
        "name": info['name'],
        "credits": info['credits'],
        "grade": result,
        "total_marks": total_marks,
        "earned_points": points * info['credits']
    })

def get_grade_points(total_marks, result_status):
    if result_status == 'F': return 0
    try: total = int(total_marks)
    except: return 0
    if total >= 90: return 10
    elif total >= 80: return 9
    elif total >= 70: return 8
    elif total >= 60: return 7
    elif total >= 55: return 6
    elif total >= 50: return 5
    elif total >= 40: return 4
    else: return 0

# --- API ENDPOINT (High Precision Mode) ---
@router.post("/scan_marks_card")
async def scan_marks_card(file: UploadFile = File(...)):
    try:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            file_path = os.path.join(tmpdir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            engine = get_ocr_engine()
            
            ocr_input = file_path
            method = "OCR-Image"
            
            if file_path.lower().endswith('.pdf'):
                doc = fitz.open(file_path)
                
                # FAST PATH: Check for Digital Text
                digital_text = ""
                for page in doc: digital_text += page.get_text()
                
                if len(digital_text) > 100:
                    print("⚡ Fast Path: Digital PDF detected.")
                    # Treat digital text like OCR output list
                    text_list = digital_text.split()
                    method = "Digital-PDF"
                else:
                    print("🐢 Slow Path: Scanned PDF detected (High Res).")
                    # Render at 200 DPI for accuracy
                    pix = doc.load_page(0).get_pixmap(dpi=200)
                    img_path = os.path.join(tmpdir, "page0.png")
                    pix.save(img_path)
                    ocr_input = img_path
                    
                    # Run OCR
                    result = engine.ocr(ocr_input)
                    text_list = extract_any_text(result)
                    method = "OCR-PDF"
                
                doc.close()
            else:
                # Image
                result = engine.ocr(ocr_input)
                text_list = extract_any_text(result)
            
            if not text_list:
                return {"status": "error", "detail": "No text found"}

            # Parse
            usn, name = extract_student_details(text_list)
            subjects = parse_text_stream(text_list)
            
            total_credits = sum(s['credits'] for s in subjects)
            total_points = sum(s['earned_points'] for s in subjects)
            sgpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0

            return {
                "status": "success",
                "method": method,
                "student_name": name,
                "usn": usn,
                "sgpa": sgpa,
                "subjects": subjects
            }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")