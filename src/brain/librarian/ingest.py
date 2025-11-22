import os
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector
from langchain_core.documents import Document

# 1. Configuration
PDF_PATH = os.path.join("data", "docs_raw", "vtu_regulations_2022.pdf")
# Note: We use 'localhost' because this script runs on your Host Machine, talking to Docker port 5432
DB_CONNECTION = "postgresql+psycopg://user:password@localhost:5432/smart_sgpa"
COLLECTION_NAME = "university_rules"

def main():
    print(f"🔍 Checking for document at: {PDF_PATH}")
    if not os.path.exists(PDF_PATH):
        print("❌ Error: File not found! Please check the path.")
        return

    # 2. Load the PDF (The "Eye")
    print("📖 Reading PDF...")
    loader = PyMuPDFLoader(PDF_PATH)
    raw_documents = loader.load()
    print(f"✅ Loaded {len(raw_documents)} pages.")

    # 3. Split Text (The "Chewing")
    # We cut pages into smaller chunks so the AI doesn't get overwhelmed.
    print("✂️  Splitting text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", " "]
    )
    chunks = text_splitter.split_documents(raw_documents)
    print(f"✅ Created {len(chunks)} chunks of text.")

    # 4. Initialize the Embedding Model (The "Translator")
    # This converts text -> numbers using your CPU.
    print("🧠 Loading AI Model (all-MiniLM-L6-v2)...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # 5. Inject into Memory (PostgreSQL)
    print("💾 Saving to Database (This may take a moment)...")
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=COLLECTION_NAME,
        connection=DB_CONNECTION,
        use_jsonb=True,
    )
    
    vector_store.add_documents(chunks)
    print("🎉 SUCCESS: The Brain has memorized the University Rules!")

if __name__ == "__main__":
    main()