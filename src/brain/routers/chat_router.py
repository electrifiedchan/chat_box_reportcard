from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector
import ollama 
import os

router = APIRouter()

# 1. Database Connection (The Librarian)
DB_CONNECTION = "postgresql+psycopg://user:password@localhost:5432/smart_sgpa"
COLLECTION_NAME = "university_rules"

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_store = PGVector(
    embeddings=embeddings,
    collection_name=COLLECTION_NAME,
    connection=DB_CONNECTION,
    use_jsonb=True,
)

# 2. Request Model
class ChatRequest(BaseModel):
    question: str

# 3. The "Smart Reply" Endpoint
@router.post("/ask")
async def ask_bot(request: ChatRequest):
    print(f"🤔 User asked: {request.question}")

    # A. SEARCH (RAG)
    # Retrieve top 3 relevant chunks from the PDF
    results = vector_store.similarity_search(request.question, k=3)
    
    if not results:
        context_text = "No specific university rules found."
    else:
        # Combine the chunks into one block of text
        context_text = "\n\n".join([doc.page_content for doc in results])

    # B. THINK (Prompt Engineering)
    # We give the AI a 'Role' and the 'Evidence'
    system_prompt = f"""
    You are a helpful University Advisor Bot. 
    Use the following official rules to answer the student's question.
    If the answer is not in the context, say "I don't see a specific rule for that in the handbook."
    
    CONTEXT RULES:
    {context_text}
    """

    # C. SPEAK (Ollama Generation)
    # This talks to your local RTX 3050 via the Ollama app
    try:
        response = ollama.chat(model='phi3:mini', messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': request.question},
        ])
        
        bot_reply = response['message']['content']
        print("🗣️  Bot replied.")
        
        return {
            "answer": bot_reply,
            "source_context": [doc.page_content for doc in results] # Show proof
        }

    except Exception as e:
        print(f"❌ Ollama Error: {e}")
        raise HTTPException(status_code=500, detail="The Mouth (Ollama) is not responding. Is the app running?")