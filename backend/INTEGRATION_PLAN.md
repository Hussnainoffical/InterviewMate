# InterviewMate Integration Plan

## Current state found

- Backend: FastAPI app in `Interview`.
- Frontend: Flutter app in `interviewmate_2`.
- FLAN-T5 question model/code: `flant5/question_generator.py` with model files in `flant5/interviewmate_flanT5_final`.
- Whisper model: local model files in `whisper-large-paksouth`.
- Better resume parser: top-level `resume_parser.py`.
- Better GitHub analyzer: top-level `github_analyzer.py`.

## What is wired now

- Resume upload now calls the backend-owned production parser instead of only keyword matching.
- GitHub skill extraction now calls the backend-owned production GitHub analyzer instead of only repo languages.
- Interview start now uses the backend-owned FLAN-T5 hybrid question generator when the model can load, with quality-gated fallback questions.
- Answer submission now reads the uploaded audio and passes it through a direct Whisper model service with chunking.
- Answer submission now evaluates each answer and stores per-question scoring in the session.
- Interview completion now builds the final report from evaluation scores instead of answered-count scoring.
- Backend now has `/api/v1/avatar/talk` and `/api/v1/avatar/talk/{talk_id}` for D-ID avatar video creation and status polling.
- Flutter now passes candidate profile context into interview start, polls D-ID talk status, submits uploaded answer audio, and displays latest question-score feedback in reports.

## Backend-local model assets

- Whisper model: `models/whisper-large-paksouth`
- FLAN-T5 model: `models/interviewmate_flanT5_final`
- Parser/analyzer/question-generator support code now lives under `app/services`.

## Still missing / next work

- D-ID requires `D_ID_API_KEY` in backend environment before real avatar generation works.
- The copied FLAN-T5 model loads, but current generated samples are low quality. Backend quality gates reject bad T5 output and fall back to reliable question-bank questions.
- Flutter still uses answer-audio file upload because the app does not currently include a microphone recording package.
- Flutter should eventually render the D-ID video player directly instead of only showing/polling the returned video URL/status.
- Whisper service currently falls back to a mock transcript if `transformers`, `torch`, audio decoding, or the model path fails.
- Add integration tests for resume upload, GitHub extraction, interview start, answer submit, complete report.

## Recommended next order

1. Set `D_ID_API_KEY` in backend environment.
2. Start backend with `.venv\Scripts\uvicorn.exe main:app --reload`.
3. Test resume upload and verify parsed profile contains field, seniority, skills, experience, and projects.
4. Test interview start and confirm invalid T5 output is replaced by `fallback_bank`.
5. Test answer upload with a short `.wav` and confirm Whisper returns a real transcript.
6. Add real microphone recording and video playback packages to Flutter.
