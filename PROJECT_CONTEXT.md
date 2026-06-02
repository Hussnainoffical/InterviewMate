# InterviewMate Project Context For Codex

Last updated: 2026-06-02

Use this file as the first context document for any future Codex session working on InterviewMate. It explains what the project is, what has already been built, what the real goal is, what assets exist, what must not be faked, and which issues are still important.

## One Sentence Summary

InterviewMate is an AI-powered mock interview platform where a candidate uploads a resume or GitHub profile, the system extracts skills and profile context, generates personalized interview questions, runs a live voice/avatar interview, evaluates answers, and produces performance reports.

## Product Goal

The real goal is not a simple quiz app.

The target product is a live AI interviewer experience:

- The candidate opens the interview session.
- The browser asks for microphone access.
- The AI interviewer greets the candidate.
- The interviewer asks if the candidate is ready.
- The candidate replies naturally by voice.
- The interviewer starts the interview.
- Questions are asked by voice through an avatar-like interviewer.
- The candidate speaks naturally without pressing record/stop/next.
- The system detects when the candidate has finished an answer.
- The system saves/evaluates the answer and moves to the next question automatically.
- The only normal manual control during the live session should be End Interview, with confirmation.

The UI should feel like a Google Meet style live session with an AI interviewer, not a form, quiz, recorder, or upload workflow.

## Current Repo

GitHub repository:

```text
https://github.com/Hussnainoffical/InterviewMate.git
```

Local clean repository:

```text
C:\Users\hussn\PycharmProjects\InterviewMateRepo
```

Original backend workspace:

```text
C:\Users\hussn\PycharmProjects\Interview
```

Original frontend workspace:

```text
C:\Users\hussn\PycharmProjects\interviewmate_2
```

The clean GitHub repo is organized as:

```text
InterviewMateRepo/
  backend/
    app/
    models/piper/
    test_samples/
    tests/
    main.py
    requirements.txt
    .env.example
    MODEL_ASSETS.md
  frontend/
    lib/
    assets/
    web/
    pubspec.yaml
  README.md
  PROJECT_CONTEXT.md
```

## What Was Pushed To GitHub

[Verified]

The GitHub repo contains:

- Backend FastAPI source.
- Frontend Flutter source.
- Piper TTS runtime under `backend/models/piper/`, tracked with Git LFS.
- Resume test samples under `backend/test_samples/`.
- `.env.example`, but not real `.env`.
- Backend tests.
- Basic README and model asset notes.

The latest known Git commits at the time this context was written:

```text
7c2f03b Add Piper runtime assets and sample resumes
4f67e8d Initial InterviewMate project
```

## What Was Not Pushed To GitHub

[Verified]

These were intentionally not pushed to GitHub:

- Real `.env` files and API keys.
- `interviewmate.db`.
- Backend logs.
- Generated `storage/tts` cache.
- Flutter `build/`.
- Flutter `.dart_tool/`.
- Full local Whisper model folder.
- Full local FLAN-T5 model folder.

Reason:

- `.env` contains secrets.
- `interviewmate.db` contains local user data, including emails, phone numbers, and plaintext passwords in the current prototype.
- Logs contain local runtime activity.
- Storage/build/.dart_tool are generated and machine-specific.
- Whisper and FLAN-T5 are too large for normal GitHub history.

## Remaining Local Assets Package

[Verified]

A zip was created on the Desktop:

```text
C:\Users\hussn\OneDrive\Desktop\remaining.zip
```

It contains:

```text
remaining/
  backend/.env
  backend/interviewmate.db
  backend/logs/
  backend/models/
  backend/storage/tts/
  frontend/build/
  frontend/.dart_tool/
  README.txt
```

Important:

- Share `remaining.zip` privately only.
- It contains secrets and local database data.
- Do not commit its contents blindly to GitHub.
- If a collaborator needs it, they should extract it carefully into matching backend/frontend locations.

## Backend Stack

[Verified]

Backend framework:

- FastAPI
- Uvicorn
- SQLAlchemy
- SQLite
- Pydantic
- httpx
- Transformers
- Torch
- Librosa
- SoundFile
- Piper local TTS runtime
- OpenAI Realtime API integration

Backend entry point:

```text
backend/main.py
```

Main API prefix:

```text
/api/v1
```

Health endpoint:

```text
GET /health
```

Swagger UI when backend is running:

```text
http://localhost:8000/docs
```

Backend setup:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn main:app --reload
```

## Frontend Stack

[Verified]

Frontend framework:

- Flutter
- Flutter web
- GoRouter
- http package
- file_picker
- record
- video_player
- flutter_tts
- audioplayers
- HTML iframe integration for local TalkingHead avatar
- WebRTC and WebSocket usage through `dart:html`

Frontend setup:

```powershell
cd frontend
flutter pub get
flutter run -d chrome
```

Current frontend backend URL:

```dart
const String kBaseUrl = 'http://localhost:8000';
```

File:

```text
frontend/lib/services/api_service.dart
```

## Data Model

[Verified]

The SQLite database models are in:

```text
backend/app/db_models.py
```

Tables:

- `users`
- `interview_sessions`
- `performance_reports`

User model fields include:

- `uid`
- `fullName`
- `email`
- `password`
- `phoneNumber`
- `role`
- `jobTitle`
- `city`
- `skills`
- timestamps

Important risk:

- Current prototype stores passwords in plaintext.
- This is acceptable only for a local FYP/demo prototype.
- Before real deployment, password hashing is mandatory.

Interview session model fields include:

- `sessionId`
- `userId`
- `skills`
- `questions`
- `answers`
- `status`
- `score`
- `summary`
- `startTime`
- `endTime`

Report model fields include:

- `reportId`
- `userId`
- `sessionId`
- `overallScore`
- `summary`
- `strengths`
- `improvements`
- `questionScores`
- `createdAt`

## Main Backend Routers

[Verified]

Routers registered in `backend/main.py`:

```text
/api/v1/auth
/api/v1/profile
/api/v1/resume
/api/v1/github
/api/v1/interview
/api/v1/report
/api/v1/admin
/api/v1/avatar
```

WebSocket route also registered:

```text
/ws/interview-agent/{session_id}
```

The same WebSocket is also available under:

```text
/api/v1/interview/ws/interview-agent/{session_id}
```

because it is declared in the interview router and also registered as a root websocket route.

## Authentication And Users

[Verified]

Auth is prototype-level:

- Register.
- Login.
- Forgot password.
- User roles: `user` and `admin`.

Important:

- This is not production auth.
- Passwords are plaintext in the current database model.
- There is no real JWT enforcement across all endpoints.

Recommended future work:

- Hash passwords with bcrypt/argon2.
- Add access tokens and route protection.
- Remove public admin endpoints or protect them.
- Stop allowing wildcard CORS for production.

## Resume And GitHub Skill Extraction

[Verified]

Resume upload route:

```text
POST /api/v1/resume/upload?uid={uid}
```

Supported file types:

- PDF
- DOC
- DOCX

Resume parsing flow:

```text
frontend resume upload
  -> backend /resume/upload
  -> candidate_profile.parse_resume_file
  -> resume_parser.extract_text_from_file
  -> resume_parser.parse_resume
  -> skills saved to user profile
```

GitHub skill extraction route:

```text
POST /api/v1/github/extract-skills?uid={uid}
```

The system merges resume/GitHub/manual skills for interview setup.

Important behavior:

- Tests verify resume upload should not invent default fake skills when extraction fails.
- Tests verify GitHub analysis errors should not silently become fake skills.

## Interview Start Flow

[Verified]

Interview start route:

```text
POST /api/v1/interview/start?uid={uid}
```

Request includes:

- `skills`
- `questionCount`
- optional `candidateProfile`

Current backend clamps question count:

```text
1 to 15
```

Questions are generated through:

```text
backend/app/services/question_generation.py
```

Question generation strategy:

1. Search dataset bank first by default.
2. If dataset cannot satisfy enough questions, try local FLAN-T5 generation.
3. If model generation fails, use fallback question bank.

Question bank:

```text
backend/app/data/interview_questions.json
```

Question bank stats endpoint:

```text
GET /api/v1/interview/question-bank/stats
```

Previously observed question bank size:

```text
33462 questions
```

## Model Assets

[Verified]

Piper TTS runtime is included in GitHub through Git LFS:

```text
backend/models/piper/
```

Full large local model folders are not in GitHub:

```text
backend/models/whisper-large-paksouth/
backend/models/interviewmate_flanT5_final/
```

They are in the local `remaining.zip` package and/or original backend workspace.

Environment variables for custom model paths:

```env
WHISPER_MODEL_PATH=C:\path\to\whisper-large-paksouth
FLAN_T5_MODEL_PATH=C:\path\to\interviewmate_flanT5_final
PIPER_EXE_PATH=C:\path\to\piper.exe
PIPER_MODEL_PATH=C:\path\to\en_US-amy-medium.onnx
```

OpenAI Realtime variables:

```env
OPENAI_SECRET_KEY=sk-...
OPENAI_REALTIME_MODEL=gpt-realtime-mini
OPENAI_REALTIME_VOICE=marin
```

Never print or commit real API keys.

## Whisper And Audio Transcription

[Verified]

Transcription service:

```text
backend/app/services/transcription.py
```

Default Whisper model path:

```text
backend/models/whisper-large-paksouth
```

Important environment variable:

```env
INTERVIEWMATE_DISABLE_WHISPER=false
```

Critical behavior:

- If `INTERVIEWMATE_DISABLE_WHISPER=true`, transcription returns a mock transcript.
- Backend now rejects mock transcription before evaluation in `/submit-answer`.
- Backend rejects empty/no-speech/too-short/near-silent audio.
- Backend rejects meaningless transcripts such as "thank you" or "okay thanks".

Current audio quality thresholds:

```text
Minimum audio duration: 1.5 seconds
Minimum peak: 0.01
Minimum RMS: 0.002
```

Important lesson:

The system must never evaluate a fake/mock transcript as if the user actually answered.

## Evaluation

[Verified]

Evaluation service:

```text
backend/app/services/evaluation.py
```

Current evaluation is rule-based:

- Keyword overlap with the question.
- Answer length/completeness.
- Basic clarity scoring.
- Filler penalty.
- Meaningfulness validation.

Current scoring fields:

- `relevanceScore`
- `clarityScore`
- `completenessScore`
- `overallScore`
- `keywordsMatched`
- `feedback`

Current limitations:

- It is not a true deep interview evaluator.
- It does not use an LLM rubric yet.
- It can underrate good answers if vocabulary differs from the question.
- It can overfocus on keywords.

Recommendation:

For a strong demo, keep the rule-based validator as a guardrail, but add an LLM evaluator using OpenAI for final scoring when API budget allows. The evaluator should grade:

- Relevance to the exact question.
- Technical correctness.
- Specificity.
- Structure.
- Depth.
- Communication.
- Examples and impact.
- Whether the candidate avoided or answered the question.

Do not evaluate silence, random words, mic tests, greetings, or unrelated input as valid answers.

## Report Generation

[Verified]

Complete interview route:

```text
POST /api/v1/interview/complete
```

Current backend protections:

- Session must exist.
- Session must belong to user if UID is supplied.
- Session must be active.
- A report must not already exist for the same session.
- At least one answer is required.
- All questions in the session must have answers before completion.

Reports route:

```text
GET /api/v1/report/list?uid={uid}
GET /api/v1/report/{report_id}
```

Important product requirement:

Reports must show real backend results only. Avoid static/fake score cards, fake sessions, or hard-coded "best subject" values.

## Live Agent Mode

This is the most important feature direction.

The desired behavior:

1. User opens `/interview-session`.
2. App automatically requests microphone permission.
3. App automatically connects backend live agent WebSocket.
4. App creates OpenAI Realtime session through backend.
5. AI greets the candidate.
6. AI asks if candidate is ready.
7. Candidate speaks naturally.
8. AI detects readiness.
9. AI asks first question.
10. Candidate answers continuously by voice.
11. Turn detection determines when candidate is done.
12. Transcript is saved/evaluated.
13. AI moves to next question automatically.
14. No manual Next button in live mode.
15. No manual upload button in live mode.
16. No press-to-record workflow in live mode.
17. Only manual control should be End Interview, with confirmation.

Current implementation status:

[Verified]

- `backend/app/services/realtime.py` builds OpenAI Realtime session payload.
- Backend endpoint `/api/v1/interview/realtime/session` exchanges browser SDP offer for OpenAI answer SDP.
- Realtime payload uses:
  - `gpt-realtime-mini`
  - voice `marin`
  - input transcription model `gpt-realtime-whisper`
  - semantic VAD
  - low eagerness
  - `create_response: true`
  - `interrupt_response: true`
- Frontend has WebRTC/DataChannel code in `interview_session_screen.dart`.
- Frontend has `realtime_event_parser.dart` for OpenAI realtime events.
- Frontend has live status concepts:
  - connecting
  - agent speaking
  - listening
  - thinking
  - continuous mic live
- Backend exposes `/ws/interview-agent/{session_id}` but it is currently more of a control/status WebSocket, not a full audio streaming orchestrator.

Important gap:

The system is not yet a complete backend-orchestrated realtime interview state machine. Some older manual record/upload/next paths still exist in `interview_session_screen.dart`. Future work should remove or fully hide those from live agent mode.

## Intended Realtime Event Types

The user explicitly requested these backend event types:

```text
agent_greeting
agent_question
agent_speaking_start
agent_speaking_end
user_speech_start
user_speech_partial
user_speech_final
user_thinking
answer_completed
next_question
repeat_question
interview_ending_confirmation
interview_ended
evaluation_started
evaluation_completed
error_recovery
```

Current backend constant:

```text
AGENT_EVENT_TYPES
```

File:

```text
backend/app/routers/interview.py
```

## Intended Interview State Machine

The user requested these states:

```text
connecting
greeting
waiting_for_ready
asking_question
listening_for_answer
detecting_completion
transitioning_next_question
ending_confirmation
ended
evaluating
```

Recommendation:

Implement the state machine in backend as an explicit session orchestrator class, not scattered frontend flags.

Possible file:

```text
backend/app/services/interview_agent.py
```

State transitions should be deterministic and testable.

## Avatar System

[Verified]

There are two avatar ideas in the current project:

1. Local TalkingHead iframe/avatar in Flutter web.
2. Optional D-ID video generation through backend `/api/v1/avatar/talk`.

Avatar backend:

```text
backend/app/services/avatar.py
backend/app/routers/avatar.py
```

D-ID is disabled unless:

```env
D_ID_ENABLED=true
```

If D-ID is disabled, backend returns local-demo mode.

Piper TTS endpoint:

```text
POST /api/v1/avatar/speech
GET /api/v1/avatar/speech?text=...
```

Piper cache:

```text
backend/storage/tts
```

Product requirement:

The avatar should feel professional and live. Avoid a fake-looking static/manual flow. The interviewer should look like it is hosting a real interview session.

Practical recommendation:

For the FYP demo, prioritize reliable live audio + polished UI + good status states over expensive generated video for every utterance. A lightweight animated avatar with accurate speaking/listening states is better than slow video generation that breaks the flow.

## Answer Ownership And Attempts

[Verified]

Current answer storage:

```text
session.answers[questionId] = latest answer object
```

Current behavior:

- Re-answering the same question replaces the prior saved answer.
- `attemptNumber` increments.
- Only the latest answer per question is used for report completion.

Product recommendation:

In live agent mode:

- The final completed answer for the current question should be evaluated.
- If the candidate repeats/restarts before answer completion, treat it as the same attempt.
- If the candidate clearly asks to redo after completion, create a new attempt and replace the scored answer, while preserving attempt history if implemented.

Best future data model:

```text
answers: {
  questionId: {
    currentAttemptId,
    submittedAttemptId,
    attempts: [
      {
        attemptNumber,
        transcript,
        startedAt,
        endedAt,
        source,
        evaluation,
        status
      }
    ]
  }
}
```

Do not evaluate multiple partial drafts as separate final answers unless the product explicitly asks for attempt history scoring.

## Important Known Issues

These should be treated as high-priority future tasks.

### 1. GitHub Repo Schema Import Risk

[Verified]

Several backend files import:

```python
from app.models import ...
```

but in the current clean repo listing, there is no:

```text
backend/app/models.py
```

The schema classes appear to be in:

```text
backend/app/__init__.py
```

Risk:

- Backend imports may fail in a fresh clone.

Recommended fix:

- Create `backend/app/models.py` with the Pydantic schemas.
- Keep `app/__init__.py` minimal.
- Ensure `StartInterviewRequest` includes `skills`, `questionCount`, and `candidateProfile`.
- Ensure `SubmitAnswerResponse` includes transcript, source, error, and evaluation fields.
- Ensure `ResumeUploadResponse` includes `candidateProfile`.
- Ensure `UpdateSkillsRequest` exists.

### 2. Live Agent WebSocket Is Not Complete Yet

[Verified]

`/ws/interview-agent/{session_id}` accepts JSON control messages like:

- `end_interview`
- `confirm_end`
- `repeat_question`

but it does not yet stream mic audio chunks itself, and does not yet fully orchestrate all requested states/events.

Recommendation:

- Decide whether audio is handled through browser-to-OpenAI WebRTC or browser-to-backend-to-OpenAI.
- For low latency and simplicity, browser-to-OpenAI WebRTC through backend SDP minting is reasonable.
- Backend should still own interview state and persistence.
- Frontend should not be the authority for question progression.

### 3. Manual Record UI Still Exists In Code

[Verified]

`interview_session_screen.dart` still contains manual recording/upload answer paths:

- `_toggleRecording`
- `_pickAnswerAudio`
- `_answerAudioBytes`
- `_answerAudioName`
- `_nextQuestion`
- `_submitCurrentAnswerIfReady`

Some of this may be hidden in live mode, but the code still exists.

Product requirement:

- Live agent mode should remove/hide manual Next/upload/record controls.
- Only End Interview should be visible during live interview.

### 4. Evaluation Needs Upgrade

[Verified]

Current evaluation is rule-based and not interview-quality enough for a strong demo.

Recommendation:

- Keep rule-based validation for rejecting bad/noisy answers.
- Add LLM rubric evaluation for real answers.
- Use a budget model carefully.
- Cache/store evaluations.
- Return structured JSON only.

### 5. Reports Must Stay Truthful

[High Confidence]

Earlier audit found report UI had some static/fake-looking values. Future Codex should verify current frontend report screen and ensure every score/session/strength is from backend data.

### 6. Security Is Prototype-Level

[Verified]

Current database model stores plaintext passwords.

Recommendation:

- For FYP local demo, document this clearly.
- For any public deployment, add hashing and auth enforcement first.

## Recommended Development Priorities

Priority 1: Fix fresh clone backend import health.

- Add/restore `backend/app/models.py`.
- Run backend tests.
- Confirm `/health`, `/docs`, `/api/v1/interview/start`, and `/api/v1/avatar/speech`.

Priority 2: Make live agent mode deterministic.

- Create backend interview agent state machine.
- Make backend the authority for question index.
- Emit the requested event types.
- Persist final transcripts.
- Save/evaluate automatically after answer completion.

Priority 3: Remove old manual interview controls from live mode.

- No Next button.
- No upload answer button.
- No recorded_answer.m4a label.
- No draft ready UI.
- No tap-to-record.
- Only End Interview with confirmation.

Priority 4: Upgrade evaluation.

- Reject invalid input before evaluation.
- Add LLM rubric when API key is present.
- Fall back to rule-based if API unavailable.
- Store evaluator source and failure reason.

Priority 5: Clean report truthfulness.

- Remove fake report cards and hard-coded numbers.
- Show only real backend sessions/reports.
- Add empty states.

Priority 6: Polish avatar/live UX.

- Use professional full-screen interview layout.
- Accurate speaking/listening/thinking states.
- Smooth question display.
- Dev-only transcript/debug panel.

## Suggested Live Agent Architecture

Recommended architecture for a reliable FYP demo:

```text
Flutter browser
  - Requests mic permission
  - Opens backend WebSocket for interview state/events
  - Creates WebRTC offer
  - Sends SDP offer to backend
  - Receives OpenAI answer SDP
  - Sends/receives realtime audio through WebRTC
  - Sends OpenAI transcript events to backend when needed

FastAPI backend
  - Owns session state
  - Owns question index
  - Owns persistence
  - Creates OpenAI Realtime sessions securely
  - Emits interview state events over WebSocket
  - Receives final transcript events
  - Evaluates and stores answers
  - Completes report

OpenAI Realtime API
  - Handles voice conversation
  - Handles turn detection
  - Produces user transcripts
  - Produces AI speech
```

Why this is recommended:

- Keeps API key server-side.
- Avoids backend audio relay complexity.
- Uses OpenAI's low-latency realtime stack.
- Allows backend to remain authority for session state and reports.

Drawback:

- Frontend and backend must coordinate events carefully.
- Browser WebRTC error handling must be robust.

Alternative:

- Stream raw audio chunks to backend WebSocket and have backend relay to OpenAI.

Drawback of alternative:

- More latency.
- More complexity.
- More CPU/network load.
- Harder to debug for FYP.

## Required Edge Cases For Live Interview

Future Codex should explicitly handle:

- User denies microphone permission.
- User has no microphone device.
- Backend not running.
- OpenAI key missing.
- OpenAI Realtime quota/rate error.
- WebRTC offer/answer failure.
- DataChannel opens but audio does not flow.
- User is silent after greeting.
- User says "repeat the question".
- User says "I am not ready".
- User asks unrelated questions.
- User speaks Urdu/random/off-topic input.
- User answers too briefly.
- User starts answering while agent is speaking.
- User interrupts agent.
- User stops mid-answer and resumes.
- User accidentally says "next" without answering.
- User clicks End Interview.
- User confirms or cancels end.
- User reloads page mid-session.
- Session is already completed.
- Duplicate completion request.
- Submit transcript after completion.
- Missing question ID.
- Invalid session/user mismatch.

## API Endpoints To Know

Core:

```text
GET  /health
GET  /
```

Auth:

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/forgot-password
```

Profile:

```text
GET /api/v1/profile/{uid}
PUT /api/v1/profile/{uid}
```

Resume:

```text
POST /api/v1/resume/upload?uid={uid}
GET  /api/v1/resume/skills/{uid}
PUT  /api/v1/resume/skills/{uid}
```

GitHub:

```text
POST /api/v1/github/extract-skills?uid={uid}
```

Interview:

```text
GET  /api/v1/interview/question-bank/stats
POST /api/v1/interview/start?uid={uid}
POST /api/v1/interview/submit-answer
POST /api/v1/interview/submit-transcript
POST /api/v1/interview/realtime/session
POST /api/v1/interview/complete
GET  /api/v1/interview/history?uid={uid}
GET  /api/v1/interview/session/{session_id}
```

Realtime:

```text
WS /ws/interview-agent/{session_id}
WS /api/v1/interview/ws/interview-agent/{session_id}
```

Avatar:

```text
POST /api/v1/avatar/talk
GET  /api/v1/avatar/talk/{talk_id}
POST /api/v1/avatar/speech
GET  /api/v1/avatar/speech?text={text}
```

Reports:

```text
GET /api/v1/report/list?uid={uid}
GET /api/v1/report/{report_id}
```

Admin:

```text
GET    /api/v1/admin/stats
GET    /api/v1/admin/users
PUT    /api/v1/admin/users/{uid}/role
DELETE /api/v1/admin/users/{uid}
```

## Testing Status

[Verified from previous work]

Backend tests previously passed:

```text
Ran 21 tests ... OK
```

Flutter web build previously passed:

```text
flutter build web --no-pub --no-wasm-dry-run
```

Important:

- These should be rerun after any fresh clone or after restoring `app/models.py`.
- Do not claim the system works without running tests again.

Useful backend test command:

```powershell
cd backend
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Useful frontend commands:

```powershell
cd frontend
flutter pub get
flutter analyze
flutter build web --no-pub --no-wasm-dry-run
```

## How A Collaborator Should Set Up

Clone:

```powershell
git clone https://github.com/Hussnainoffical/InterviewMate.git
cd InterviewMate
git lfs install
git lfs pull
```

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
```

Then privately copy real `.env` values into `backend/.env`.

If using the private `remaining.zip`, place:

```text
remaining/backend/.env              -> backend/.env
remaining/backend/interviewmate.db  -> backend/interviewmate.db
remaining/backend/models/*          -> backend/models/*
remaining/backend/storage/tts       -> backend/storage/tts
```

Frontend:

```powershell
cd frontend
flutter pub get
flutter run -d chrome
```

Do not normally copy:

```text
frontend/build
frontend/.dart_tool
```

unless debugging an exact local generated state.

## Environment File Guidance

Never commit real `.env`.

Expected backend env values may include:

```env
APP_ENV=development
SECRET_KEY=...
OPENAI_SECRET_KEY=...
OPENAI_REALTIME_MODEL=gpt-realtime-mini
OPENAI_REALTIME_VOICE=marin
INTERVIEWMATE_DISABLE_WHISPER=false
INTERVIEWMATE_DISABLE_T5=false
WHISPER_MODEL_PATH=...
FLAN_T5_MODEL_PATH=...
PIPER_EXE_PATH=...
PIPER_MODEL_PATH=...
D_ID_ENABLED=false
D_ID_API_KEY=...
D_ID_SOURCE_URL=...
```

OpenAI key note:

- OpenAI API keys are project/account API keys.
- They are not the same as ChatGPT Plus subscription access.
- ChatGPT Plus does not automatically include API credits.
- The same OpenAI API key can be used for normal API endpoints and Realtime API if the account/project has access and credits.

## Product Tone And Demo Standard

The target demo should feel:

- Professional.
- Calm.
- Realistic.
- Interview-focused.
- Voice-first.
- Not fake.
- Not button-heavy.
- Not like a quiz form.

The AI interviewer should:

- Stay inside interview scope.
- Repeat the current question when asked.
- Redirect unrelated input.
- Avoid answering for the candidate.
- Ask concise follow-ups.
- Not talk too much.
- Not advance without a meaningful answer unless the state machine decides to skip/end.

The candidate experience should:

- Feel like joining a real video call.
- See clear status: Connecting, Agent Speaking, Listening, Thinking, Evaluating.
- See the current question.
- Hear the AI interviewer.
- Speak naturally.
- End interview manually if needed.

## Things Future Codex Must Not Do

Do not:

- Reintroduce a manual quiz-like flow as the primary live session.
- Evaluate mock Whisper transcripts.
- Evaluate silence as an answer.
- Evaluate "okay", "thanks", "test mic", or random words as valid.
- Show fake/static report scores as real.
- Commit `.env`.
- Commit local DB with user data.
- Commit backend logs.
- Commit generated Flutter build artifacts unless explicitly requested.
- Put OpenAI key in frontend code.
- Make the frontend the only source of truth for interview progression.
- Claim tests/build pass without running them.

## Best Next Task For Codex

If the next Codex session is asked to continue development, start here:

1. Verify fresh clone backend import health.
2. Fix or restore `backend/app/models.py` if missing.
3. Run backend tests.
4. Run Flutter build.
5. Audit `/interview-session` and remove/hide manual controls from live mode.
6. Implement backend interview agent state machine.
7. Make answer completion automatic through realtime transcript events.
8. Upgrade evaluation to LLM rubric with strict invalid-answer guardrails.
9. Verify with browser/manual test using mic permission and backend logs.

## Final North Star

InterviewMate should become a real AI mock interviewer:

- It reads the candidate profile.
- It asks grounded questions.
- It listens continuously.
- It detects when the candidate is done.
- It handles silence and irrelevant input intelligently.
- It evaluates only real answers.
- It produces truthful reports.
- It helps a student practice interviews in a way that feels close to a real interview, not a scripted demo.

