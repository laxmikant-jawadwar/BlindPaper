# BlindPaper

**AI-based, syllabus-centric question paper generation, review and approval for colleges.**

Faculty upload a syllabus PDF, set up an examination template, and BlindPaper writes the question paper with a generative AI model, strictly from that syllabus. The paper is checked, corrected by the faculty member, and sent to the Exam Cell (the admin), who approves it or sends it back with a reason.

---

## Who uses it

| Role | Signs in with | Can |
|---|---|---|
| **Faculty** | An account they register themselves | Upload syllabi, configure and generate papers, correct and submit them, download approved papers |
| **Admin** (Exam Cell) | The one account created from `ADMIN_EMAIL` / `ADMIN_PASSWORD` in `backend/.env` | Review submitted papers, approve or reject them, see faculty and departments |

The admin panel opens only with the admin credentials. Every admin API is checked on the server, so a faculty member cannot reach it.

## How it works

**Faculty**

1. **Dashboard**: their papers and statuses.
2. **Upload syllabus**: the PDF is read (PyMuPDF for text, pdfplumber for tables) and structured into course name, description, course outcomes (with Bloom's level) and units with topics. Both the raw text and the structure are stored in MongoDB.
3. **Configure**: course details, MSE or ESE, difficulty, question types (MCQ, Descriptive, Numericals), units, and an editable template (question groups, "Attempt any two", sub-questions with CO, marks and unit).
4. **Generate**: Groq's `openai/gpt-oss-120b` writes one question per template slot, grounded in the chosen unit's topics, the course outcome and its Bloom's level.
5. **Validate**: the paper is checked for structure, marks, question types, MCQ format, unit coverage, syllabus relevance, duplicates and formatting.
6. **Preview and finalize**: correct questions in place, regenerate a single question (the rest of the paper is untouched) or the whole paper, save as a Draft.
7. **Submit**: status becomes *Pending Approval*.

**Admin**

8. **Dashboard** with a department filter, pending approvals, recent submissions and department-wise numbers.
9. **View** a submitted paper with its details.
10. **Review** the questions, marks distribution, syllabus relevance and structure.
11. **Approve** (the faculty member can then download the PDF) or **Reject** with a reason.
12. The faculty sees the decision; a rejected paper is corrected and resubmitted, which returns it to *Pending Approval*.

## Tech stack

- **Backend**: FastAPI, MongoDB (pymongo), PyMuPDF, pdfplumber, ReportLab (PDFs use the bundled DejaVu Sans font, so Greek letters and maths symbols print everywhere), httpx
- **AI**: Groq (`openai/gpt-oss-120b`, with `qwen/qwen3.8-27b` as automatic fallback)
- **Frontend**: React 19, Vite, Tailwind CSS, Lucide icons, React Router
- **Auth**: email and password, PBKDF2-hashed passwords, session tokens stored (hashed) in MongoDB

## Project structure

```text
BlindPaper/
├── backend/
│   ├── app/
│   │   ├── api/routes/      auth, syllabus, papers (faculty), admin
│   │   ├── services/        auth, syllabus extraction and structuring, paper rules,
│   │   │                    Groq generation, analysis, PDF, admin
│   │   ├── repositories/    MongoDB access (users, sessions, syllabi, papers)
│   │   └── schemas/         request and response models
│   ├── tests/               pytest suite (runs on an in-memory MongoDB)
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── src/
│       ├── pages/           auth, faculty, admin
│       ├── components/      layout, ui, paper
│       └── api/ auth/ lib/  API client, session handling, helpers
├── sample/                  two real syllabus PDFs used by the tests
├── references/              the UI designs the screens follow
├── application workflow.md  the faculty workflow
├── Part B — Admin workflow.txt
└── setup.md                 full setup on a new machine
```

## Getting started

See **[setup.md](setup.md)** for every step on a fresh machine (Python, Node, MongoDB, the admin account and the Groq key). In short:

```powershell
# 1. MongoDB running on 127.0.0.1:27017
# 2. backend
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env        # then set ADMIN_PASSWORD and GROQ_API_KEY
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 3. frontend (another terminal)
cd frontend
npm install
Copy-Item .env.example .env
npm run dev -- --host 127.0.0.1 --port 5173
```

Open http://127.0.0.1:5173. Register as faculty, or sign in with the admin credentials from `backend/.env`.

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest        # backend (in-memory MongoDB, Groq mocked)
cd ..\frontend
npm run lint; npm run build
```

API documentation is served at http://127.0.0.1:8000/docs while the backend runs.
