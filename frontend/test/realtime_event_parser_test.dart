import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:interviewmate/services/realtime_event_parser.dart';

void main() {
  test('marks candidate speech started from input audio event', () {
    final event = parseRealtimeEvent(jsonEncode({
      'type': 'input_audio_buffer.speech_started',
    }));

    expect(event.kind, RealtimeEventKind.userSpeaking);
  });

  test('extracts assistant transcript delta', () {
    final event = parseRealtimeEvent(jsonEncode({
      'type': 'response.output_audio_transcript.delta',
      'delta': 'Tell me more',
    }));

    expect(event.kind, RealtimeEventKind.assistantTranscriptDelta);
    expect(event.text, 'Tell me more');
  });

  test('extracts completed user transcript from nested content', () {
    final event = parseRealtimeEvent(jsonEncode({
      'type': 'conversation.item.input_audio_transcription.completed',
      'transcript': 'I used FastAPI and tests for the backend.',
    }));

    expect(event.kind, RealtimeEventKind.userTranscriptComplete);
    expect(event.text, contains('FastAPI'));
  });

  test('unknown events stay harmless', () {
    final event = parseRealtimeEvent(jsonEncode({
      'type': 'session.created',
    }));

    expect(event.kind, RealtimeEventKind.unknown);
  });
}
