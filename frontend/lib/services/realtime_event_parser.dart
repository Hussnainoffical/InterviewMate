import 'dart:convert';

enum RealtimeEventKind {
  userSpeaking,
  userSpeechStopped,
  assistantSpeaking,
  assistantTranscriptDelta,
  assistantDone,
  userTranscriptComplete,
  error,
  unknown,
}

class ParsedRealtimeEvent {
  const ParsedRealtimeEvent({
    required this.kind,
    this.text,
    this.error,
  });

  final RealtimeEventKind kind;
  final String? text;
  final String? error;
}

ParsedRealtimeEvent parseRealtimeEvent(String raw) {
  dynamic decoded;
  try {
    decoded = jsonDecode(raw);
  } catch (_) {
    return const ParsedRealtimeEvent(kind: RealtimeEventKind.unknown);
  }
  if (decoded is! Map) {
    return const ParsedRealtimeEvent(kind: RealtimeEventKind.unknown);
  }

  final type = decoded['type']?.toString() ?? '';
  switch (type) {
    case 'input_audio_buffer.speech_started':
      return const ParsedRealtimeEvent(kind: RealtimeEventKind.userSpeaking);
    case 'input_audio_buffer.speech_stopped':
      return const ParsedRealtimeEvent(kind: RealtimeEventKind.userSpeechStopped);
    case 'response.created':
    case 'response.output_item.added':
      return const ParsedRealtimeEvent(kind: RealtimeEventKind.assistantSpeaking);
    case 'response.output_audio_transcript.delta':
    case 'response.output_text.delta':
      return ParsedRealtimeEvent(
        kind: RealtimeEventKind.assistantTranscriptDelta,
        text: decoded['delta']?.toString() ?? '',
      );
    case 'response.done':
      return const ParsedRealtimeEvent(kind: RealtimeEventKind.assistantDone);
    case 'conversation.item.input_audio_transcription.completed':
      return ParsedRealtimeEvent(
        kind: RealtimeEventKind.userTranscriptComplete,
        text: decoded['transcript']?.toString() ?? '',
      );
    case 'error':
      return ParsedRealtimeEvent(
        kind: RealtimeEventKind.error,
        error: decoded['error']?.toString() ?? decoded['message']?.toString() ?? 'Realtime error',
      );
    default:
      return const ParsedRealtimeEvent(kind: RealtimeEventKind.unknown);
  }
}
