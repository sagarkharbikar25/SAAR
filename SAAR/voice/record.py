# voice/record.py

import sounddevice as sd
import numpy as np

SAMPLE_RATE = 16000
DURATION = 4

BAD_KEYWORDS = ["stereo mix", "speaker", "output"]


def list_mics():
    print("[MIC] Available microphones:")
    devices = sd.query_devices()
    valid = []
    for i, dev in enumerate(devices):
        if dev["max_input_channels"] > 0:
            print(i, dev["name"])
            valid.append(i)
    return valid


def pick_working_mic():
    devices = sd.query_devices()
    for i, dev in enumerate(devices):
        name = dev["name"].lower()

        if dev["max_input_channels"] == 0:
            continue

        if any(bad in name for bad in BAD_KEYWORDS):
            continue

        try:
            sd.check_input_settings(device=i, samplerate=SAMPLE_RATE)
            print(f"[MIC] Using mic: {dev['name']} (index {i})")
            return i
        except Exception:
            continue

    print("[MIC] No valid mic found, using default")
    return sd.default.device[0]


def get_working_mic():
    devices = sd.query_devices()

    for i, dev in enumerate(devices):
        name = dev["name"].lower()

        if dev["max_input_channels"] == 0:
            continue

        if any(bad in name for bad in BAD_KEYWORDS):
            continue

        try:
            sd.check_input_settings(device=i, samplerate=SAMPLE_RATE)
            print(f"[MIC] Auto-selected: {dev['name']} (index {i})")
            return i
        except Exception:
            continue

    print("[MIC] No working mic found, trying default")
    return sd.default.device[0] if sd.default.device[0] >= 0 else None


def record(max_seconds=12, silence_threshold=0.0005, silence_duration=1.5):
    print("[MIC] Listening... speak now.")

    device_index = get_working_mic()

    if device_index is None:
        print("[MIC] ERROR: No mic available")
        return None

    samplerate = SAMPLE_RATE
    silence_limit = int(silence_duration * samplerate)

    audio_buffer = []
    silent_chunks = 0

    def callback(indata, frames, time, status):
        nonlocal silent_chunks

        volume = np.mean(np.abs(indata))

        audio_buffer.append(indata.copy())

        if volume < silence_threshold:
            silent_chunks += frames
        else:
            silent_chunks = 0

    stream = sd.InputStream(
        samplerate=samplerate,
        channels=1,
        callback=callback,
        device=device_index
    )

    with stream:
        for _ in range(int(max_seconds * samplerate / 1024)):
            sd.sleep(50)

            if silent_chunks > silence_limit:
                print("[MIC] Silence detected, stopping.")
                break

    if not audio_buffer:
        return None

    audio = np.concatenate(audio_buffer, axis=0)
    audio = np.squeeze(audio)

    max_amp = np.max(np.abs(audio))
    mean_amp = np.mean(np.abs(audio))

    print(f"[MIC] Max amplitude: {max_amp:.6f} | Mean: {mean_amp:.6f}")

    # Lowered threshold: 0.002 catches quieter microphones too
    if mean_amp < 0.002:
        print("[MIC] Audio too quiet — no speech detected")
        return None

    print("[MIC] Audio captured OK.")
    return audio


# =========================
# TEST MODE
# =========================
if __name__ == "__main__":
    list_mics()
    audio = record(4)

    if audio is not None:
        print("Recorded audio length:", len(audio))
    else:
        print("No valid audio captured")

def reduce_noise(audio):
    import numpy as np

    # simple noise gate
    threshold = 0.01
    audio[np.abs(audio) < threshold] = 0

    return audio