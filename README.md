# BlindPaper

**AI-Based Syllabus-Centric Question Paper Generation and Validation System**

BlindPaper is a college examination preparation system designed for faculty and academic departments. It generates examination question papers grounded in an uploaded syllabus, performs validation checks (semantic similarity, duplicate detection, and marks/unit distributions), and enables faculty to review, edit, and export approved question papers.

---

## Project Structure

```text
BlindPaper/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entrypoint and middleware
│   │   ├── api/
│   │   │   └── routes/          # Thin API route controllers (e.g., health.py)
│   │   ├── core/                # Configuration and environment settings
│   │   ├── schemas/             # Pydantic request and response schemas
│   │   ├── services/            # Business logic (PDF extraction, LLM, validation, export)
│   │   ├── models/              # Database document models (Phase 6)
│   │   └── repositories/        # Database access layers (Phase 6)
│   ├── tests/                   # Automated pytest suite
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example             # Environment variable template
│   └── .gitignore               # Backend gitignore rules
├── frontend/                    # React.js frontend interface (to be developed)
├── .gitignore                   # Root gitignore rules
└── README.md                    # Project documentation
```

---

## Phase 1 Implementation

Phase 1 provides the foundational FastAPI backend service:
- **FastAPI Application**: Configured with CORS for React frontend (`http://localhost:5173`).
- **Endpoints**:
  - `GET /`: API welcome and discovery route.
  - `GET /api/health`: Health status endpoint returning system health and version metadata.
- **Interactive Documentation**: Swagger UI at `/docs` and ReDoc at `/redoc`.
- **Automated Tests**: Unit tests covering root, health check, and CORS configuration.

---

## Setup & Running the Backend

### Prerequisites
- Python 3.10+ (Tested on Python 3.13)
- PowerShell, Command Prompt, or Bash

### 1. Navigate to the backend directory
```bash
cd backend
```

### 2. Create and activate a Python virtual environment
**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(If PowerShell restricts script execution, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`)*

**On Windows (CMD):**
```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

**On Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables (Optional for Phase 1)
Copy `.env.example` to `.env`:
```powershell
# Windows PowerShell:
Copy-Item .env.example .env

# Linux / macOS:
cp .env.example .env
```

### 5. Run the development server
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
The server will start at `http://127.0.0.1:8000`.

---

## Testing Endpoints

### 1. Browser / Swagger UI
- Welcome message: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- Health check: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
- Interactive API Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. cURL / PowerShell Test
```powershell
# Root endpoint
curl http://127.0.0.1:8000/

# Health check
curl http://127.0.0.1:8000/api/health

# Syllabus PDF upload and text extraction
curl -X POST http://127.0.0.1:8000/api/syllabus/upload -F "file=@path/to/syllabus.pdf"
```

### 3. Run Automated Tests
From the `backend` folder with the virtual environment activated:
```bash
pytest
```

---

## Incremental Roadmap
- [x] **Phase 1**: Basic FastAPI backend setup and health endpoints.
- [x] **Phase 2**: Syllabus PDF upload and text extraction using PyMuPDF.
- [ ] **Phase 3**: Examination configuration and AI question generation.
- [ ] **Phase 4**: Syllabus relevance, duplicate detection, and marks validation.
- [ ] **Phase 5**: Question paper PDF export.
- [ ] **Phase 6**: MongoDB integration and React frontend.
