# core/vocal_engine.py
import numpy as np
import librosa

class VocalEmotionAnalyzer:
    def __init__(self):
        self.last_mood = "Neutral"
        self.history = []

    def analyze_audio(self, audio_data, sample_rate=16000):
        """
        Analyzes raw audio data for energy (loudness) and pitch.
        audio_data: numpy array of audio samples
        """
        try:
            # 1. Calculate Energy (RMS)
            rms = librosa.feature.rms(y=audio_data)[0]
            avg_energy = np.mean(rms)
            
            # 2. Estimate Pitch (F0)
            pitches, magnitudes = librosa.piptrack(y=audio_data, sr=sample_rate)
            pitch = self.extract_max_pitch(pitches, magnitudes)
            
            # 3. Simple Heuristic Mapping
            mood = self.map_to_mood(avg_energy, pitch)
            self.last_mood = mood
            return mood
        except Exception as e:
            print(f"⚠ Vocal Analysis Error: {e}")
            return "Neutral"

    def extract_max_pitch(self, pitches, magnitudes):
        """Extract the strongest pitch frequency from the piptrack results."""
        index = magnitudes.argmax()
        pitch = pitches.flatten()[index]
        return pitch

    def map_to_mood(self, energy, pitch):
        # Heuristics for basic tone detection
        # Values can be tuned based on user's mic and voice
        if energy > 0.1: # Speaking loudly
            if pitch > 250:
                return "Excited / Panicked"
            else:
                return "Firm / Angry"
        elif energy < 0.01: # Whispering or quiet
            return "Tired / Sad"
        else:
            if pitch > 200:
                return "Cheerful"
            else:
                return "Calm / Professional"
