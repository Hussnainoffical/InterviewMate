# InterviewMate

AI-powered mock interview platform with a FastAPI backend and Flutter frontend.

## Project Structure

- `backend/` - FastAPI API, interview orchestration, realtime session endpoints, evaluation, reports.
- `frontend/` - Flutter app for resume/profile setup, live interview, and reports.

## Backend Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn main:app --reload
```

Put your own OpenAI key in `backend/.env`. Do not commit `.env`.

## Frontend Setup

```powershell
cd frontend
flutter pub get
flutter run -d chrome
```

The frontend currently expects the backend at `http://localhost:8000`.
