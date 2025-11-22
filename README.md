🎓 The Smart Finder-BotA Local-First, Privacy-Centric AI Advisor for Student Success.Zero Cloud. Zero Cost. 100% Private.🌟 The ProblemUniversity students face an invisible crisis:Calculation Stress: Manual SGPA calculation is error-prone and tedious.Hidden Burnout: Students don't realize that "skipping classes" correlates with "failure" until it's too late.Information Gap: University rules (Makeup Exams, Grace Marks) are buried in 100-page PDFs.💡 The SolutionThe Smart Finder-Bot is a digital guardian that lives on your laptop. It combines Computer Vision, Deterministic Logic, and Machine Learning to provide instant academic and wellness advice without sending a single byte of data to the cloud.🏗️ ArchitectureThis project uses a Hybrid AI architecture optimized for consumer hardware (4GB VRAM).ComponentRoleTechnology StackThe EyeVision & OCRPaddleOCR + Custom Geometry Engine (No Regex)The BrainBackend APIFastAPI (Python)The CalculatorLogic CorePython (VTU Grading Logic)The DoctorML PredictionXGBoost (Trained on UCI Student Performance Data)The AdvisorRAG ChatbotOllama (Phi-3) + PGVector (PostgreSQL)The FaceUser InterfaceStreamlit🚀 Features1. 👁️ The Eye (Smart Scanner)Input: Accepts Images (.png, .jpg) or PDFs.Innovation: Uses a Geometry-Based Sorting Algorithm instead of brittle Regex. It reconstructs tables by clustering text coordinates (Y-axis for Rows, X-axis for Columns).Robustness: Successfully reads Masked, Skewed, and Low-Resolution images.Smart Fix: Automatically corrects OCR errors (e.g., reading "49" as Total Marks in a Lab -> corrects to "99" based on logic).2. 🩺 The Doctor (Burnout Predictor)Input: Extracts "Failures" from the Marks Card + Subjective Lifestyle Quiz.Model: XGBoost Classifier.Insight: Predicts failure risk based on Alcohol Consumption, Free Time, and Health, not just grades.Privacy: Data is processed locally; no sensitive health data leaves the device.3. 🤖 The Advisor (Rule Expert)Input: Natural Language Questions ("Can I take a re-exam?").Mechanism: RAG (Retrieval-Augmented Generation). It searches a local Vector Database (Postgres) containing the VTU Regulations 2022 PDF and uses Phi-3 to summarize the answer.🛠️ Installation & SetupPrerequisitesPython 3.10+PostgreSQL (or Docker)Ollama (for Chat features)1. Clone the Repositorygit clone [https://github.com/electrifiedchan/chat_box_reportcard.git](https://github.com/electrifiedchan/chat_box_reportcard.git)
cd chat_box_reportcard
2. Install Dependenciespip install -r requirements.txt
3. Set Up EnvironmentCreate a .env file:DATABASE_URL=postgresql://user:password@localhost:5432/smart_sgpa
OLLAMA_BASE_URL=http://localhost:11434
4. Run the ApplicationStep A: Start the Brain (Backend)uvicorn src.brain.main:app
Step B: Start the Face (Frontend)streamlit run frontend.py
📂 Project Structuresrc/
├── brain/
│   ├── main.py            # Entry Point & "Zero-Hour Patch"
│   ├── routers/
│   │   ├── ocr_router.py  # The Geometry Engine (Vision)
│   │   ├── doctor_router.py # ML Prediction Logic
│   │   └── rag_router.py  # Vector Search Logic
│   └── toolbelt/
│       └── doctor_model.json # Trained XGBoost Model
├── frontend.py            # Streamlit Dashboard
└── docker-compose.yml     # DB Infrastructure
