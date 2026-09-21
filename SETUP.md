# Local setup

## 1. Start MySQL

The simplest option is Docker Desktop:

```powershell
docker compose up -d
```

For an existing local MySQL installation, run `database/schema.sql` as a privileged MySQL user.

## 2. Start the FastAPI backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python seed.py
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

For Gmail result emails, edit `backend/.env` and set `SMTP_EMAIL` and `SMTP_APP_PASSWORD`. Use a Google App Password, not the normal account password.

## 3. Start the React frontend

Open a second terminal:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Open http://localhost:5173.

## Demo accounts

| Role | Email | Password |
|---|---|---|
| Admin | admin@onlinequiz.com | Admin123! |
| Teacher | teacher@onlinequiz.com | Teacher123! |
| Student | student@onlinequiz.com | Student123! |

Change demo passwords before any real deployment.

## Permissions

- Admin creates Admin, Teacher, or Student accounts and manages all quizzes.
- Teacher creates Student accounts and manages only their own quizzes.
- Student sees only published quizzes matching department, semester, and section.
- Three tab/window-switch violations automatically submit an attempt.
- Teacher/Admin can allow one retake after reviewing the integrity event.
