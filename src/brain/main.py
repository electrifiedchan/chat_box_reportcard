# =============================================================================
# 🚑 GLOBAL ZERO-HOUR PATCH: Fix PaddleOCR vs LangChain Conflict
# This MUST run before any imports of paddleocr anywhere in the project.
# =============================================================================
import sys
import types

try:
    # 1. Mock 'langchain.docstore.document'
    if 'langchain.docstore.document' not in sys.modules:
        m_langchain = types.ModuleType('langchain')
        m_docstore = types.ModuleType('langchain.docstore')
        m_document = types.ModuleType('langchain.docstore.document')
        
        class DummyDocument:
            def __init__(self, page_content, metadata=None): pass
            
        m_document.Document = DummyDocument
        m_docstore.document = m_document
        sys.modules['langchain.docstore'] = m_docstore
        sys.modules['langchain.docstore.document'] = m_document

    # 2. Mock 'langchain.text_splitter'
    if 'langchain.text_splitter' not in sys.modules:
        m_text_splitter = types.ModuleType('langchain.text_splitter')
        class DummySplitter:
            def __init__(self, **kwargs): pass
            def split_text(self, text): return [text]
        m_text_splitter.RecursiveCharacterTextSplitter = DummySplitter
        sys.modules['langchain.text_splitter'] = m_text_splitter

    print("✅ GLOBAL PATCH APPLIED: LangChain dependencies mocked for PaddleOCR.")
except Exception as e:
    print(f"⚠️ Patch Warning: {e}")

# =============================================================================
# STANDARD APP IMPORTS
# =============================================================================
from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Import Routers
from src.brain.routers import rag_router, chat_router, calc_router, doctor_router, ocr_router

# Load Environment
load_dotenv()

# Initialize Brain
app = FastAPI(
    title="Smart Finder-Bot Brain",
    version="1.0.0",
    description="The Logic Unit: RAG + MCP + Calculations + Predictions + Vision"
)

# Include Routers
app.include_router(rag_router.router, prefix="/api/v1", tags=["Librarian"])
app.include_router(chat_router.router, prefix="/api/v1", tags=["Chat"])
app.include_router(calc_router.router, prefix="/api/v1", tags=["Calculator"])
app.include_router(doctor_router.router, prefix="/api/v1", tags=["The Doctor"])
app.include_router(ocr_router.router, prefix="/api/v1", tags=["The Eye"])

@app.get("/")
async def root():
    return {"status": "online", "system": "Brain", "message": "I am ready to process data."}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)