# ArthSaathi

ArthSaathi is a **multi-agent financial-literacy platform** specifically designed for gig workers and agricultural laborers in India. It leverages a "Living Memory" (Blackboard) architecture orchestrating multiple AI agents to provide personalized financial guidance, scam detection, and government scheme matchmaking.

## Key Features

- **Conversational Onboarding:** A LangGraph agent that conducts a natural interview to extract user occupation, income, and financial pain points without tedious forms.
- **Scam Scanner:** An end-to-end RAG application that uses OCR (Tesseract) to extract text from screenshots of SMS/Contracts, and semantically matches them against known predatory clauses in a LanceDB vector database.
- **Guardian Agent (Upcoming):** A background watchdog that analyzes transaction logs to detect anomalies and generates proactive micro-savings nudges.
- **Scheme Matchmaker (Upcoming):** An agent that matches a user's specific profile and eligibility against Indian government welfare schemes.
- **Katha Mode (Upcoming):** A storyteller agent that weaves personalized financial literacy stories based on the user's behavioral summary.

## Architecture

- **Frontend:** Next.js 14 (App Router), React 18, Tailwind CSS, Zustand. Designed with a high-contrast **OLED Minimal** aesthetic for maximum legibility and battery saving on low-end devices.
- **Backend:** Modular monolith powered by **FastAPI** (Python).
- **AI/Orchestration:** **LangGraph** & **LangChain**, utilizing local or cloud LLMs.
- **Databases:** 
  - **SQLite:** Central relational database and "Living Memory" (via `aiosqlite`).
  - **LanceDB:** Embedded vector database for lightning-fast semantic search.

---

## Local Development Setup

### 1. Prerequisites
- **Node.js** (v18+)
- **Python** (v3.10+)
- **uv**: Python package manager (`pip install uv`)
- **Tesseract OCR**: Must be installed on your system for the Scam Scanner to extract text from images. (e.g., `apt-get install tesseract-ocr` on Linux, or via installer on Windows).

### 2. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Install dependencies using `uv`:
   ```bash
   uv sync
   ```
3. Configure environment variables:
   Create a `.env` file in the `backend` directory. You will need a `JWT_SECRET` and your LLM configurations (e.g., `LLM_PROVIDER=openai` and `LLM_API_KEY=sk-...` or use local Ollama).
   ```env
   JWT_SECRET=super_secret_key_change_me_in_prod
   LLM_PROVIDER=openai
   LLM_API_KEY=your_api_key_here
   ```
4. Initialize the SQLite Database:
   ```bash
   uv run python app/db/init_db.py
   ```
5. Seed the LanceDB Vector Database (Predatory Clauses):
   ```bash
   uv run python scripts/inject_real_datasets.py.py
   ```
6. Start the FastAPI server:
   ```bash
   uv run uvicorn app.main:app --reload
   ```
   *The backend will be available at `http://localhost:8000` (Swagger UI at `/docs`).*

### 3. Frontend Setup

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Start the Next.js development server:
   ```bash
   npm run dev
   ```
   *The frontend will be available at `http://localhost:3000`.*

## Testing

Both services have comprehensive test suites.
- **Backend:** `cd backend && uv run pytest`
- **Frontend:** `cd frontend && npm run test`

