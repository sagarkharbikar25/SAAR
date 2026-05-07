import whisper
import numpy as np

model = whisper.load_model("medium")

def transcribe(audio):
    if audio is None:
        return ""

    # 🔥 Normalize audio (VERY IMPORTANT)
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val

    # 🔥 Boost signal
    audio = audio * 2.0

    # Clip to safe range
    audio = np.clip(audio, -1.0, 1.0)

    # Debug
    volume = np.mean(np.abs(audio))
    print(f"🔊 STT Volume (normalized): {volume:.6f}")

    try:
        result = model.transcribe(audio, fp16=False, language="en")
        text = result["text"].strip()

        print("🧪 Heard:", text)
        return text

    except Exception as e:
        print("❌ STT Error:", e)
        return ""