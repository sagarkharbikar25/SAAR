import os
import time
import re
import queue
import threading
import speech_recognition as sr
from core.brain import ask_brain
from voice.tts import speak
from core.os_control import media_key

# --- Configuration ---
WAKE_WORD = "saar"
EXIT_WORDS = ["stop", "quiet", "shut up", "bye", "goodbye", "go idle"]
ENERGY_THRESHOLD = 150 # Lowered for better sensitivity
DYNAMIC_ENERGY = True

# --- Global State ---
is_speaking = False

def run_voice_pipeline(state):
    """Main background loop for voice interaction."""
    global is_speaking
    
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = ENERGY_THRESHOLD
    recognizer.dynamic_energy_threshold = DYNAMIC_ENERGY
    recognizer.pause_threshold = 1.2 # Allow for natural gaps in speech
    
    # Use Microphone as source (Sagar's Smart Discovery)
    print("🎙 Neural Voice Pipeline Online")
    print("📡 Neural Gear Scan: Finding your headset...")
    
    selected_index = None # Default to system default
    found_name = "System Default"
    
    try:
        mics = sr.Microphone.list_microphone_names()
        for i, name in enumerate(mics):
            print(f"  [{i}] {name}")
            # SMART AUTO-SWITCH: Prioritize Portronics or Bluetooth Headsets
            if any(term in name.lower() for term in ["portronics", "twins", "headset", "microphone array", "realtek"]):
                selected_index = i
                found_name = name
                print(f"🌟 [Smart-Sense] Detected preferred gear: {name} at Index {i}")
                break
    except Exception as e:
        print(f"  ⚠️ Hardware scan failed: {e}. Using default settings.")

    try:
        mic = sr.Microphone(device_index=selected_index)
        print(f"📡 Hardware Sync: {found_name} Locked!")
    except Exception as e:
        print(f"⚠️ Selected Index {selected_index} failed: {e}. Falling back to default.")
        mic = sr.Microphone()
        
    last_state = None
    last_heartbeat = time.time()
    conversation_active_until = 0

    while True:
        # Prevent listening to self
        if is_speaking:
            time.sleep(0.5)
            continue
            
        skip_wake_word = state.is_work_mode() or (time.time() < conversation_active_until)

        if not skip_wake_word and last_state != "idle":
            state.set("idle")
            last_state = "idle"
            print("🟡 Adjusting for background noise...")
            try:
                with mic as source:
                    recognizer.adjust_for_ambient_noise(source, duration=1)
            except Exception as e:
                print(f"⚠️ Noise Adjustment failed: {e}")
            print("🟢 SAAR is listening. Say 'SAAR'...")
        
        # Heartbeat to prove we aren't stuck
        if time.time() - last_heartbeat > 10:
            print("💓 [Neural Heartbeat] Monitoring audio stream...")
            last_heartbeat = time.time()

        try:
            with mic as source:
                if not skip_wake_word:
                    # 1. Listen for Wake Word (Added safety timeout)
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=4)
                    try:
                        raw_text = recognizer.recognize_google(audio).lower()
                        print(f"👂 Heard: '{raw_text}'") # DEBUG PRINT
                    except sr.UnknownValueError:
                        continue
                    
                    # Support variations of the wake word
                    if any(w in raw_text for w in ["saar", "sar", "sir", "star", "sagar"]):
                        pass # Wake up!
                    else:
                        continue
                    
                    # 2. Wake Word Detected!
                    print(f"⚡ Wake word detected!")
                    state.set("listening")
                    last_state = "listening"
                    
                    # Vocal Acknowledgment
                    is_speaking = True
                    speak("Yes Sagar?")
                    is_speaking = False
                else:
                    # Work Mode or Active Conversation is ON
                    if last_state != "listening":
                        state.set("listening")
                        last_state = "listening"
                        if state.is_work_mode():
                            print(f"💼 [Work Mode] Continuous Listening Active...")
                        else:
                            print(f"🔄 [Conversation] Actively listening for follow-up...")

                # 3. Listen for Command
                audio = recognizer.listen(source, timeout=10 if skip_wake_word else 5, phrase_time_limit=15)
                command_text = recognizer.recognize_google(audio)
        except sr.WaitTimeoutError:
            continue
        except sr.UnknownValueError:
            continue
        except Exception as e:
            print(f"⚠️ Voice Stream Error: {e}")
            time.sleep(1) # Backoff
            continue

        if not command_text or len(command_text.strip()) < 2:
            print("⚠ Ignoring weak command (too short)")
            continue

        print(f"✅ Final command: {command_text}")
        state.add_chat("User", command_text)

        # ===============================
        # SOFT EXIT → BACK TO IDLE
        # ===============================
        if any(word in command_text.lower() for word in EXIT_WORDS):
            state.set("speaking")
            last_state = "speaking"

            is_speaking = True
            speak("Okay Sagar, going idle.")
            is_speaking = False

            conversation_active_until = 0  # End active conversation
            last_state = None  # force idle reset
            print("↩ SAAR returned to idle")
            continue

        state.set("thinking")
        state.add_chat("SAAR", "📡 Processing Neural Grid...")
        last_state = "thinking"
        
        response, sentiment = ask_brain(command_text, state)
        
        # Update UI with sentiment
        state.set_sentiment(sentiment["polarity"], sentiment["label"])

        if not response or not response.strip():
            response = "I couldn't process that Sagar. Please try again."

        # ===============================
        # SPEAK
        # ===============================
        state.set("speaking")
        last_state = "speaking"

        print(f"🗣 SAAR: {response}")
        state.add_chat("SAAR", response)

        is_speaking = True
        # Split response into sentences for more natural, 'incremental' speech
        # This prevents long pauses on large paragraphs
        sentences = re.split(r'(?<=[.!?]) +|\n+', response)
        for sentence in sentences:
            if sentence.strip():
                speak(sentence.strip())
        
        time.sleep(0.4)
        is_speaking = False

        # Extend active conversation window by 15 seconds after speaking
        conversation_active_until = time.time() + 15

        # Soft reset for visual state evaluation next loop
        last_state = None