# Model Assets

This repository includes the Piper TTS runtime under `models/piper/`.

The following large local models are intentionally not committed:

- `models/whisper-large-paksouth/`
- `models/interviewmate_flanT5_final/`

They are too large for normal GitHub Git history. Share them separately through a model host, cloud drive, or Git LFS after confirming quota.

The backend supports custom paths through environment variables:

```env
WHISPER_MODEL_PATH=C:\path\to\whisper-large-paksouth
FLAN_T5_MODEL_PATH=C:\path\to\interviewmate_flanT5_final
PIPER_EXE_PATH=C:\path\to\piper.exe
PIPER_MODEL_PATH=C:\path\to\en_US-amy-medium.onnx
```
