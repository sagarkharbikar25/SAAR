# core/state.py
import queue

class AssistantState:
    def __init__(self):
        self._state = "idle"
        self._sentiment = 0.0 # -1.0 to 1.0 (Text)
        self._mood_label = "Neutral"
        self._visual_mood = "Neutral"
        self._vocal_mood = "Neutral"
        self._work_mode = False
        self.chat_queue = queue.Queue()

    def set_work_mode(self, mode: bool):
        self._work_mode = mode
        print(f"💼 Work Mode → {'ON (Continuous Listening)' if mode else 'OFF (Wake Word Required)'}")

    def is_work_mode(self):
        return self._work_mode

    def add_chat(self, sender: str, message: str):
        self.chat_queue.put((sender, message))


    def set(self, state: str):
        self._state = state
        print(f"🔄 State → {state}")

    def set_sentiment(self, polarity: float, label: str):
        self._sentiment = polarity
        self._mood_label = label

    def set_visual_mood(self, mood: str):
        self._visual_mood = mood

    def set_vocal_mood(self, mood: str):
        self._vocal_mood = mood

    def get(self):
        return self._state
        
    def get_sentiment(self):
        return self._sentiment, self._mood_label

    def get_bio_status(self):
        return self._visual_mood, self._vocal_mood
