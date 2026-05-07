# voice/tts.py

import os
import asyncio
import edge_tts
import pygame
import time

# Initialize Pygame Mixer for high-quality audio playback
pygame.mixer.init()

# ⚙️ GLOBAL VOICE CONFIG (Adjustable via UI)
VOICE_RATE = "+8%"
VOICE_PITCH = "+0Hz"

async def _generate_and_play(text: str):
    # ⚡ Restoring the youthful and clear 'Guy' Neural Voice Sagar liked
    voice = "en-US-GuyNeural"
    
    # Create a unique temporary file for each speech snippet to avoid permission errors
    temp_file = f"speech_{int(time.time() * 1000)}.mp3"
    
    # Tuning: Using Sagar's preferred real-time settings
    communicate = edge_tts.Communicate(text, voice, rate=VOICE_RATE, pitch=VOICE_PITCH)
    await communicate.save(temp_file)

    # Play the generated audio
    pygame.mixer.music.load(temp_file)
    pygame.mixer.music.play()
    
    # Wait for audio to finish playing
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
    
    # Clean up immediately after playback finishes
    try:
        # Give it a tiny moment to release the file handle
        pygame.mixer.music.unload()
        if os.path.exists(temp_file):
            os.remove(temp_file)
            # print(f"🗑️ Cleaned up {temp_file}")
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")

def speak(text: str) -> float:
    if not text.strip():
        return 0.0

    print(f"🔊 SAAR Speaking: {text[:40]}...")
    
    start = time.time()
    
    try:
        # Run the async generation and playback in a new event loop
        asyncio.run(_generate_and_play(text))
    except Exception as e:
        print(f"⚠️ TTS Error: {e}. Falling back to system voice.")
        # Fallback to simple PowerShell TTS if Edge-TTS fails
        safe_text = text.replace('"', '').replace('\n', ' ')
        command = f'Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("{safe_text}")'
        import subprocess
        subprocess.run(["powershell", "-Command", command], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    end = time.time()
    return end - start
