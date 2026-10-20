# BlindPaper — Setup Guide

How to get BlindPaper running on a fresh PC. These are the exact steps used to set up the original machine (Windows 11, PowerShell), with every command.

BlindPaper has three parts, each on its own port:

| Part | What it is | Address |
|---|---|---|
| MongoDB | Stores users, syllabi and question papers | `127.0.0.1:27017` |
| Backend | FastAPI (Python) | `http://127.0.0.1:8000` (API docs at `/docs`) |
| Frontend | React + Vite + Tailwind | `http://localhost:5173` or `http://127.0.0.1:5173` |

You also need two things of your own: a **Groq API key** (free, from https://console.groq.com/keys) for writing the questions, and a **password for the admin account**.

Time needed: about 15 minutes, plus a 750 MB MongoDB download.

---

## 0. Versions this was set up and tested with

| Tool | Version |
|---|---|
| Windows | 11 Pro |
| Python | 3.14.7 (the README says 3.10+ is fine) |
| Node.js / npm | v24.21.0 / 11.19.0 |
| MongoDB | 8.0.13 (portable zip) |

`backend/requirements.txt` is not pinned, so pip installs the newest versions. These were what pip resolved on the original machine, in case something breaks later:

```text
fastapi 0.151.0        starlette 1.9.0         uvicorn 0.54.0
pydantic 2.14.1        pydantic-settings 2.16.0 python-dotenv 1.2.4
httpx 0.28.1           pymongo 4.19.0          pymupdf 2.0
reportlab 5.0.1        python-multipart 0.0.32 pytest 9.1.1
pdfplumber 0.11.10     mongomock 4.3.0 (tests only)
```

PyMuPDF reads the syllabus text and pdfplumber reads its tables (the course-outcomes table). Both are needed: PyMuPDF's own table finder missed or mangled these tables on the sample syllabi.

Frontend (from `package.json` and the lockfile): React 19.3.1, Vite 8.3.4, Tailwind CSS 4.3, React Router 7, lucide-react.

The PDF uses **DejaVu Sans**, which is bundled in `backend/app/assets/fonts` (with its licence), so Greek letters, subscripts like x₁, ₹ and maths symbols print the same on every machine. Nothing needs installing for this.

Question generation uses Groq's `openai/gpt-oss-120b`, with `qwen/qwen3.8-27b` as the automatic fallback. Groq's free tier allows about 1,000 requests a day and 8,000 tokens a minute, which is plenty for generating papers.

---

## 1. Prerequisites

You need **Git**, **Python 3.10+** and **Node.js 20+** (Node 24 was used). Check what you already have:

```powershell
git --version
python --version
node --version
npm --version
```

Install whatever is missing. Either use the installers from git-scm.com, python.org and nodejs.org, or winget (these winget IDs were **not** run on the original machine, which already had the tools):

```powershell
winget install Git.Git
winget install Python.Python.3.14
winget install OpenJS.NodeJS
```

Close and reopen PowerShell afterwards so `PATH` updates.

---

## 2. Get the code

```powershell
git clone https://github.com/laxmikant-jawadwar/BlindPaper
cd BlindPaper
```

All commands below are run from this `BlindPaper` folder unless they say otherwise.

---

## 3. Backend

### 3.1 Create the virtual environment and install packages

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

This calls the venv's Python directly, so you do **not** need to "activate" the venv and you avoid PowerShell's script execution policy error. All later backend commands use `.\.venv\Scripts\python.exe` for the same reason.

(If you prefer activating it: `.\.venv\Scripts\Activate.ps1`. If PowerShell blocks it, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` first.)

### 3.2 Create the `.env` file

```powershell
Copy-Item .env.example .env
```

Then open `backend\.env` and set these values:

```text
# the admin account; it is created when the backend starts. The admin panel opens only with these.
ADMIN_NAME=Admin
ADMIN_EMAIL=admin@blindpaper.com
ADMIN_PASSWORD=<choose a strong password>

# question generation (free key from https://console.groq.com/keys)
GROQ_API_KEY=<your key>
```

Everything else can stay as is: `ALLOWED_ORIGINS` already allows both `localhost:5173` and `127.0.0.1:5173`, and `MONGODB_URI=mongodb://127.0.0.1:27017` / `MONGODB_DATABASE=blindpaper` match step 4.

`.env` is gitignored, so it is never committed. **It now holds a secret (your Groq key) and the admin password: never share the file, and leave it out of any zip you send.** The admin account is created only if it does not exist yet, so changing `ADMIN_PASSWORD` later does not change an existing admin's password.

### 3.3 Run the backend tests (optional but a good check)

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Expected: `172 passed`. These tests need neither MongoDB (they use an in-memory copy) nor your Groq key (the AI service is replaced by a stand-in), so they are safe to run any time. A few of them read the two real syllabi in the repo's `sample/` folder; if that folder is missing, those 3 tests are skipped instead (`169 passed, 3 skipped`).

```powershell
cd ..
```

---

## 4. MongoDB

The backend expects MongoDB at `mongodb://127.0.0.1:27017`. Pick **one** option. Option A is what was done on the original machine because it needs no admin rights and installs nothing system-wide.

### Option A — Portable MongoDB, no admin needed (used originally)

Downloads the official zip, checks its SHA-256, and extracts only `mongod.exe` (the zip is 752 MB because it contains debug symbols; you only need one file from it).

```powershell
$root = "$HOME\mongodb-local"
$dl   = "$root\download"
New-Item -ItemType Directory -Force $dl, "$root\bin", "$root\data", "$root\log" | Out-Null

# 1. Download (about 752 MB)
curl.exe -L --fail -o "$dl\mongodb-8.0.13.zip" "https://fastdl.mongodb.org/windows/mongodb-windows-x86_64-8.0.13.zip"

# 2. Verify the checksum. Must print: sha256 match: True
$expected = "06eb225e91ad79ef92de74b0b6e14f02118236327815c02145c297f653d9c8cc"
$actual   = (Get-FileHash "$dl\mongodb-8.0.13.zip" -Algorithm SHA256).Hash.ToLower()
"sha256 match: $($actual -eq $expected)"
```

Do not continue unless it prints `True`. Then extract just `mongod.exe` and delete the zip:

```powershell
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead("$dl\mongodb-8.0.13.zip")
try {
  $entry = $zip.Entries | Where-Object { $_.FullName -match '/bin/mongod\.exe$' } | Select-Object -First 1
  [System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry, "$root\bin\mongod.exe", $true)
} finally { $zip.Dispose() }
Remove-Item -Recurse -Force $dl

& "$root\bin\mongod.exe" --version      # should print: db version v8.0.13
```

Create a small start script so you never retype the long command:

```powershell
@'
# Starts the local MongoDB used by BlindPaper (127.0.0.1:27017, localhost only).
# Leave this window open; Ctrl+C stops the server. Data persists in .\data
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
& "$root\bin\mongod.exe" --dbpath "$root\data" --logpath "$root\log\mongod.log" --bind_ip 127.0.0.1 --port 27017
'@ | Set-Content -Encoding utf8 "$root\start-mongo.ps1"
```

Start it (leave this window open):

```powershell
& "$HOME\mongodb-local\start-mongo.ps1"
```

Notes:
- It listens on `127.0.0.1` only, so it is not reachable from other machines.
- It is **not** a Windows service. It stops when you close the window or reboot; run `start-mongo.ps1` again to bring it back. Data is kept in `%USERPROFILE%\mongodb-local\data`.
- If you changed `$root`, use that folder in place of `$HOME\mongodb-local` everywhere.

### Option B — Normal MongoDB install (needs admin, runs as a Windows service)

*Not used on the original machine.* In an **Administrator** PowerShell:

```powershell
winget install MongoDB.Server
```

The installer sets up a service that starts automatically on port 27017. No start script needed.

### Option C — Docker

*Not tested on the original machine (it had no Docker).*

```powershell
docker run -d --name blindpaper-mongo -p 127.0.0.1:27017:27017 -v blindpaper-mongo:/data/db mongo:8
```

Later: `docker start blindpaper-mongo` / `docker stop blindpaper-mongo`.

### Option D — MongoDB Atlas (hosted)

*Not tested.* Create a free cluster, then put its connection string in `backend\.env` as `MONGODB_URI=...` (keep that file private, it contains your password).

### Check the backend can reach MongoDB

With MongoDB running (not needed to run, but useful to confirm), from the repo root:

```powershell
cd backend
.\.venv\Scripts\python.exe -c "from app.database.mongodb import check_database_connection; print('mongo ping ok:', check_database_connection())"
cd ..
```

Expected: `mongo ping ok: True`.

---

## 5. Frontend

```powershell
cd frontend
npm install
Copy-Item .env.example .env
```

`frontend\.env` contains `VITE_API_BASE_URL=http://127.0.0.1:8000`, which already matches the backend, so no edit is needed. (Vite reads this at startup. If you change it, restart the dev server.)

**Heads-up:** with npm 11, `npm install` may rewrite the tracked `frontend/package-lock.json` (on the original machine it removed two optional entries, `@types/node` and `undici-types`). That is harmless noise. To discard it:

```powershell
git checkout -- package-lock.json
```

Optional check that the toolchain works (both should finish with no errors):

```powershell
npm run lint
npm run build
```

`npm run build` creates `frontend/dist/`, which is gitignored.

```powershell
cd ..
```

---

## 6. Run everything

Open **three PowerShell windows**, in this order. Each stays open while the app runs.

**Window 1 — MongoDB** (skip if you used Option B, or Option C with the container running):

```powershell
& "$HOME\mongodb-local\start-mongo.ps1"
```

**Window 2 — Backend** (from the repo root):

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Add `--reload` if you are editing backend code and want auto-restart. It reads `backend\.env` only at startup, so restart it after changing `.env`.

**Window 3 — Frontend** (from the repo root):

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Then open **http://127.0.0.1:5173** in your browser. (Plain `npm run dev` serves `http://localhost:5173`, which also works with the default `ALLOWED_ORIGINS`.)

---

## 7. Verify it works

With all three windows running, in a fourth window:

```powershell
curl.exe http://127.0.0.1:8000/api/health
```

Expected:

```json
{"status":"healthy","app_name":"BlindPaper","version":"0.2.0","database":"connected"}
```

`"database":"connected"` is the important part. The `status` field says `healthy` even when the database is down, so look at `database`.

Other checks:
- http://127.0.0.1:8000/docs opens the interactive API documentation.
- http://127.0.0.1:5173 shows the BlindPaper sign-in page.
- **Admin:** sign in with `ADMIN_EMAIL` / `ADMIN_PASSWORD` from `backend\.env`. You land on the admin dashboard. (Faculty accounts are sent to their own area and cannot open the admin one.)
- **Faculty:** sign out, click *Create an account*, register, then *Generate Paper* → upload a text-based syllabus PDF, for example `sample/OR Syllabus.pdf` → configure the paper → *Generate Question Paper*. After a few seconds you see the paper, which you can correct and *Submit for approval*. Sign in as the admin to review and approve it, then sign back in as the faculty member to download the PDF.

What is stored, in the `blindpaper` database: `users` (accounts), `sessions` (logins, by hashed token), `syllabi` (each upload: raw text plus the structured course) and `papers` (every generated paper with its template, questions and review history).

---

## 8. Question generation (Groq)

Papers are written by Groq's `openai/gpt-oss-120b`. It needs `GROQ_API_KEY` in `backend\.env` (step 3.2); without it, *Generate Question Paper* answers "Question generation is not configured" and nothing is saved. If the main model is busy or gives an unusable answer, `qwen/qwen3.8-27b` is tried automatically. Both can be changed with `GROQ_MODEL` and `GROQ_FALLBACK_MODEL`.

Restart the backend after changing `.env`. If Groq's free limit is reached, the page tells you how many seconds to wait.

---

## 9. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| Browser console shows a CORS error | `ALLOWED_ORIGINS` in `backend\.env` doesn't include the address in your address bar. It should be `http://localhost:5173,http://127.0.0.1:5173`; then restart the backend. |
| `/api/health` shows `"database":"disconnected"` | MongoDB isn't running. Start it (step 6, Window 1). Check with `Get-NetTCPConnection -LocalPort 27017 -State Listen`. |
| Backend requests to MongoDB take about 2 seconds then fail | Same as above: the driver waits 2 s for a server before giving up. |
| `Activate.ps1 cannot be loaded because running scripts is disabled` | Skip activation and use `.\.venv\Scripts\python.exe ...` as in this guide, or run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`. |
| `Address already in use` / port busy | Something else holds the port. Find it: `Get-NetTCPConnection -LocalPort 8000 -State Listen` (or 5173 / 27017), then `Stop-Process -Id <OwningProcess>`. |
| `ModuleNotFoundError` when starting the backend | You ran system Python instead of the venv's. Use `.\.venv\Scripts\python.exe` from inside `backend\`. |
| Upload says the PDF needs OCR | The PDF is a scan/image with no text layer. OCR isn't supported yet. Use a text-based PDF. |
| The admin cannot sign in | `ADMIN_EMAIL` / `ADMIN_PASSWORD` were not set when the backend first started, or the admin was created earlier with another password. The account is created only once; change its password by deleting it (`db.users` in MongoDB Compass, the document with `role: "admin"`) and restarting the backend. |
| "Question generation is not configured" | `GROQ_API_KEY` is empty in `backend\.env`, or the backend was not restarted after you set it. |
| "Groq rejected the API key" | The key is wrong or revoked. Create a new one at https://console.groq.com/keys and update `backend\.env`. |
| "The AI service is busy (rate limit reached)" | Groq's free tier limit was hit. Wait the number of seconds shown and generate again. |
| The PDF shows `lambda`, `mu`... instead of Greek letters, or `?` for a symbol | The bundled font files in `backend\app\assets\fonts` (DejaVu Sans) are missing or damaged, so the PDF fell back to plain Helvetica. Restore that folder from the repository. A `?` means a character that no font can print (such as an emoji). |
| Frontend can't reach the API after you changed `frontend\.env` | Vite only reads `.env` at startup. Restart `npm run dev`. |
| `mongod` exits immediately | Check `%USERPROFILE%\mongodb-local\log\mongod.log`. The usual causes are port 27017 already in use or an unwritable data folder. |

---

## 10. Stopping, resetting, uninstalling

- **Stop:** press `Ctrl+C` in each window.
- **Wipe all saved syllabi** (Option A): stop MongoDB, then `Remove-Item -Recurse -Force "$HOME\mongodb-local\data\*"`, and start it again. Or, with MongoDB running, from `backend\`:
  `.\.venv\Scripts\python.exe -c "from app.database.mongodb import get_database; get_database().client.drop_database('blindpaper')"`
- **Remove MongoDB (Option A):** stop it, then `Remove-Item -Recurse -Force "$HOME\mongodb-local"`. Nothing else was installed system-wide.
- **Remove the project's local installs:** delete `backend\.venv`, `backend\.env`, `frontend\node_modules`, `frontend\.env` and `frontend\dist`. All are gitignored.

---

## 11. macOS / Linux differences

*Not tested; the original setup was on Windows.* The steps are the same with these changes:

```bash
# backend
cd backend
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env            # then edit ALLOWED_ORIGINS as in step 3.2
./.venv/bin/python -m pytest -q
./.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# frontend (in another terminal, from the repo root)
cd frontend
npm install
cp .env.example .env
npm run dev -- --host 127.0.0.1 --port 5173
```

For MongoDB, use your package manager (for example `brew tap mongodb/brew && brew install mongodb-community`) or the Docker option in step 4.

---

## Quick reference: daily start

```powershell
# Window 1
& "$HOME\mongodb-local\start-mongo.ps1"

# Window 2
cd BlindPaper\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Window 3
cd BlindPaper\frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Then open http://127.0.0.1:5173.
