import unittest
import asyncio
import inspect
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import crud
from app.db_models import Base
from app.models import StartInterviewRequest
from app.routers import github, interview, resume
from app.services import evaluation, realtime, transcription


async def maybe_await(value):
    if inspect.isawaitable(value):
        return await value
    return value


class FakeUpload:
    filename = "answer.wav"
    content_type = "audio/wav"

    async def read(self):
        return b"RIFF....WAVE"


class FakeResumeUpload:
    filename = "resume.pdf"
    content_type = "application/pdf"

    async def read(self):
        return b"%PDF-empty"


def fake_questions(skills, candidate_profile=None, count=5):
    return [
        {
            "questionId": f"q{i}",
            "questionText": f"Explain {skills[0]} concept {i}",
            "skillTag": skills[0],
            "category": "Technical",
            "source": "test",
        }
        for i in range(count)
    ]


class InterviewPipelineTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.db = self.SessionLocal()
        crud.create_user(
            self.db,
            "user_001",
            {
                "uid": "user_001",
                "fullName": "Test User",
                "email": "user@example.com",
                "password": "pass",
                "role": "user",
            },
        )

    def tearDown(self):
        self.db.close()

    async def start_session(self, question_count=3):
        with patch.object(interview, "generate_interview_questions", side_effect=fake_questions):
            return await maybe_await(interview.start_interview(
                StartInterviewRequest(skills=["FastAPI"], questionCount=question_count),
                uid="user_001",
                db=self.db,
            ))

    async def submit_real_answer(self, session_id, question_id="q0"):
        with patch.object(
            interview,
            "transcribe_audio",
            return_value={
                "transcript": "I built FastAPI endpoints with Pydantic validation, dependency injection, tests, and clear error handling.",
                "transcriptionSource": "whisper",
                "transcriptionError": None,
            },
        ):
            return await interview.submit_answer(
                sessionId=session_id,
                questionId=question_id,
                uid="user_001",
                audio=FakeUpload(),
                db=self.db,
            )

    async def test_start_interview_allows_fifteen_questions(self):
        response = await self.start_session(question_count=15)

        self.assertEqual(15, len(response.questions))

    async def test_mock_transcription_is_rejected_before_evaluation(self):
        session = await self.start_session()

        with patch.object(
            interview,
            "transcribe_audio",
            return_value={
                "transcript": "I have hands-on experience with this topic.",
                "transcriptionSource": "mock",
                "transcriptionError": "Whisper disabled by environment.",
            },
        ):
            with self.assertRaises(HTTPException) as raised:
                await interview.submit_answer(
                    sessionId=session.sessionId,
                    questionId="q0",
                    uid="user_001",
                    audio=FakeUpload(),
                    db=self.db,
                )

        self.assertEqual(422, raised.exception.status_code)
        stored = crud.get_session(self.db, session.sessionId)
        self.assertEqual({}, stored.answers)

    async def test_meaningless_transcript_is_rejected_before_evaluation(self):
        session = await self.start_session()

        with patch.object(
            interview,
            "transcribe_audio",
            return_value={
                "transcript": "Thank you.",
                "transcriptionSource": "whisper",
                "transcriptionError": None,
            },
        ):
            with self.assertRaises(HTTPException) as raised:
                await interview.submit_answer(
                    sessionId=session.sessionId,
                    questionId="q0",
                    uid="user_001",
                    audio=FakeUpload(),
                    db=self.db,
                )

        self.assertEqual(422, raised.exception.status_code)
        self.assertIn("meaningful answer", raised.exception.detail)
        stored = crud.get_session(self.db, session.sessionId)
        self.assertEqual({}, stored.answers)

    async def test_complete_requires_at_least_one_answer(self):
        session = await self.start_session()

        with self.assertRaises(HTTPException) as raised:
            await maybe_await(interview.complete_interview({"sessionId": session.sessionId, "uid": "user_001"}, db=self.db))

        self.assertEqual(400, raised.exception.status_code)
        stored = crud.get_session(self.db, session.sessionId)
        self.assertEqual("active", stored.status)

    async def test_completed_session_cannot_be_completed_or_answered_again(self):
        session = await self.start_session()
        for question in session.questions:
            await self.submit_real_answer(session.sessionId, question_id=question.questionId)
        first = await maybe_await(interview.complete_interview({"sessionId": session.sessionId, "uid": "user_001"}, db=self.db))

        with self.assertRaises(HTTPException) as duplicate:
            await maybe_await(interview.complete_interview({"sessionId": session.sessionId, "uid": "user_001"}, db=self.db))

        with self.assertRaises(HTTPException) as late_answer:
            await self.submit_real_answer(session.sessionId, question_id="q1")

        self.assertEqual(409, duplicate.exception.status_code)
        self.assertEqual(409, late_answer.exception.status_code)
        self.assertEqual(1, crud.count_reports(self.db))
        self.assertTrue(first["reportId"])

    async def test_resubmitting_answer_replaces_question_evaluation(self):
        session = await self.start_session(question_count=1)

        transcripts = [
            {
                "transcript": "I used FastAPI to build endpoints with basic validation and tests.",
                "transcriptionSource": "whisper",
                "transcriptionError": None,
            },
            {
                "transcript": (
                    "I built FastAPI endpoints with Pydantic validation, dependency injection, "
                    "structured error handling, and tests for the API behavior."
                ),
                "transcriptionSource": "whisper",
                "transcriptionError": None,
            },
        ]

        with patch.object(interview, "transcribe_audio", side_effect=transcripts):
            first = await interview.submit_answer(
                sessionId=session.sessionId,
                questionId="q0",
                uid="user_001",
                audio=FakeUpload(),
                db=self.db,
            )
            second = await interview.submit_answer(
                sessionId=session.sessionId,
                questionId="q0",
                uid="user_001",
                audio=FakeUpload(),
                db=self.db,
            )

        stored = crud.get_session(self.db, session.sessionId)
        answer = stored.answers["q0"]

        self.assertEqual(2, answer["attemptNumber"])
        self.assertEqual(second.evaluation["overallScore"], answer["evaluation"]["overallScore"])
        self.assertGreater(second.evaluation["overallScore"], first.evaluation["overallScore"])

    async def test_realtime_session_returns_answer_sdp_for_active_owner(self):
        session = await self.start_session(question_count=1)

        with patch.object(interview, "create_realtime_answer_sdp", return_value="v=0\r\nanswer") as created:
            response = await interview.create_realtime_session(
                {
                    "sessionId": session.sessionId,
                    "uid": "user_001",
                    "questionIndex": 0,
                    "offerSdp": "v=0\r\noffer",
                },
                db=self.db,
            )

        self.assertEqual("v=0\r\nanswer", response["answerSdp"])
        self.assertEqual("gpt-realtime-mini", response["model"])
        created.assert_awaited_once()

    async def test_realtime_session_rejects_completed_session(self):
        session = await self.start_session(question_count=1)
        await self.submit_real_answer(session.sessionId, question_id="q0")
        await maybe_await(interview.complete_interview({"sessionId": session.sessionId, "uid": "user_001"}, db=self.db))

        with self.assertRaises(HTTPException) as raised:
            await interview.create_realtime_session(
                {
                    "sessionId": session.sessionId,
                    "uid": "user_001",
                    "questionIndex": 0,
                    "offerSdp": "v=0\r\noffer",
                },
                db=self.db,
            )

        self.assertEqual(409, raised.exception.status_code)

    async def test_realtime_session_rejects_non_numeric_question_index(self):
        session = await self.start_session(question_count=1)

        with self.assertRaises(HTTPException) as raised:
            await interview.create_realtime_session(
                {
                    "sessionId": session.sessionId,
                    "uid": "user_001",
                    "questionIndex": "first",
                    "offerSdp": "v=0\r\noffer",
                },
                db=self.db,
            )

        self.assertEqual(400, raised.exception.status_code)
        self.assertIn("Question index", raised.exception.detail)

    async def test_submit_transcript_answer_saves_live_realtime_answer(self):
        session = await self.start_session(question_count=1)

        response = await maybe_await(interview.submit_transcript_answer(
            {
                "sessionId": session.sessionId,
                "questionId": "q0",
                "uid": "user_001",
                "transcript": "I handled FastAPI offline sync by queueing writes, resolving conflicts, and testing retries.",
                "source": "realtime",
            },
            db=self.db,
        ))

        stored = crud.get_session(self.db, session.sessionId)
        self.assertEqual("realtime", stored.answers["q0"]["transcriptionSource"])
        self.assertEqual(response["evaluation"]["overallScore"], stored.answers["q0"]["evaluation"]["overallScore"])

    async def test_submit_transcript_answer_rejects_noise(self):
        session = await self.start_session(question_count=1)

        with self.assertRaises(HTTPException) as raised:
            await maybe_await(interview.submit_transcript_answer(
                {
                    "sessionId": session.sessionId,
                    "questionId": "q0",
                    "uid": "user_001",
                    "transcript": "okay thanks",
                    "source": "realtime",
                },
                db=self.db,
            ))

        self.assertEqual(422, raised.exception.status_code)

    async def test_resume_upload_does_not_invent_default_skills(self):
        with patch.object(
            resume,
            "parse_resume_file",
            return_value={
                "field": "General",
                "seniority": "Beginner",
                "skills": [],
                "projects": [],
            },
        ):
            response = await resume.upload_resume(
                uid="user_001",
                file=FakeResumeUpload(),
                db=self.db,
            )

        self.assertEqual([], response.extractedSkills)
        user = crud.get_user(self.db, "user_001")
        self.assertEqual([], user.skills or [])

    async def test_github_analysis_error_is_not_replaced_with_fake_skills(self):
        with patch.object(
            github,
            "analyze_github_profile",
            return_value={"username": "broken", "error": "network unavailable"},
        ):
            with self.assertRaises(HTTPException) as raised:
                await github.extract_github_skills(
                    github.GitHubSkillsRequest(githubUsername="broken"),
                    uid="user_001",
                    db=self.db,
                )

        self.assertEqual(502, raised.exception.status_code)

class WhisperConfigTests(unittest.TestCase):
    def test_local_env_false_overrides_stale_process_true(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env"
            env_file.write_text("INTERVIEWMATE_DISABLE_WHISPER=false\n", encoding="utf-8")

            with patch.object(transcription, "LOCAL_ENV_FILES", [env_file]):
                with patch.dict(os.environ, {"INTERVIEWMATE_DISABLE_WHISPER": "true"}):
                    self.assertFalse(transcription._is_whisper_disabled())


class AnswerQualityTests(unittest.TestCase):
    def test_rejects_short_polite_noise_as_not_meaningful(self):
        valid, reason = evaluation.validate_answer_transcript("Thank you.")

        self.assertFalse(valid)
        self.assertIn("meaningful", reason)

    def test_accepts_short_but_real_interview_answer(self):
        valid, reason = evaluation.validate_answer_transcript(
            "I used FastAPI to build REST endpoints with validation and tests."
        )

        self.assertTrue(valid, reason)

    def test_rejects_near_silent_audio(self):
        self.assertIsNotNone(transcription._audio_quality_error([0.0] * 16000))

    def test_rejects_too_short_audio(self):
        self.assertIsNotNone(transcription._audio_quality_error([0.5] * 8000))


class RealtimeSessionTests(unittest.TestCase):
    def test_realtime_session_payload_uses_server_vad_and_budget_model(self):
        config = realtime.build_realtime_session_config(
            questions=[{
                "questionId": "q1",
                "questionText": "Explain how you handled offline data sync.",
            }],
            current_index=0,
            user_id="user_001",
            candidate_profile={"field": "Software Engineer", "seniority": "Junior"},
        )

        payload = realtime.build_openai_session_payload(config)

        self.assertIn('"model": "gpt-realtime-mini"', payload)
        self.assertIn('"type": "semantic_vad"', payload)
        self.assertIn('"create_response": true', payload)
        self.assertIn('"interrupt_response": true', payload)
        self.assertIn('"transcription": {"model": "gpt-realtime-whisper"', payload)
        self.assertIn("offline data sync", payload)
        self.assertIn("repeat the current question verbatim", payload)
        self.assertIn("interview-only", payload)
        self.assertNotIn("user_001", config.safety_identifier)

    def test_realtime_sdp_requires_api_key(self):
        config = realtime.build_realtime_session_config(
            questions=[],
            current_index=0,
            user_id="user_001",
        )

        with patch.object(realtime, "LOCAL_ENV_FILES", []):
            with patch.dict(os.environ, {"OPENAI_API_KEY": "", "OPENAI_SECRET_KEY": ""}, clear=True):
                with self.assertRaises(realtime.RealtimeConfigurationError):
                    asyncio.run(
                        realtime.create_realtime_answer_sdp(
                            offer_sdp="v=0\r\n",
                            config=config,
                        )
                    )

    def test_realtime_api_key_can_come_from_local_secret_key_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env"
            env_file.write_text(
                "OPENAI_SECRET_KEY = sk-test-local\n"
                "OPENAI_REALTIME_MODEL=gpt-realtime-mini\n",
                encoding="utf-8",
            )

            with patch.object(realtime, "LOCAL_ENV_FILES", [env_file]):
                with patch.dict(os.environ, {}, clear=True):
                    self.assertEqual("sk-test-local", realtime.resolve_openai_api_key())


if __name__ == "__main__":
    unittest.main()
