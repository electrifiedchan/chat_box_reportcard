from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector
import os

router = APIRouter()

# 1. Re-connect to the Memory
# We use the same settings as the ingestion script
DB_CONNECTION = "postgresql+psycopg://user:password@localhost:5432/smart_sgpa"
COLLECTION_NAME = "university_rules"

# 2. Load the Translator (Embedding Model)
# It needs this to understand the math behind your question
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# 3. Initialize the Vector Store Interface
vector_store = PGVector(
    embeddings=embeddings,
    collection_name=COLLECTION_NAME,
    connection=DB_CONNECTION,
    use_jsonb=True,
)

# 4. Define the Request Format
class QueryRequest(BaseModel):
    question: str

# 5. The Search Endpoint
@router.post("/search")
async def search_rules(query: QueryRequest):
    """
    Searches the 'Librarian' (Database) for rules related to the question.
    """
    print(f"🔍 Searching for: {query.question}")
    
    # Perform Similarity Search
    # k=3 means "give me the top 3 most relevant chunks"
    results = vector_store.similarity_search(query.question, k=3)
    
    if not results:
        return {"message": "No relevant rules found.", "context": []}
    
    # Extract just the text content so the LLM can read it later
    context_data = [doc.page_content for doc in results]
    
    return {
        "message": "Found relevant rules.",
        "context": context_data
    }