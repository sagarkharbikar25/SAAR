# core/memory.py

from datetime import datetime
from database.db import db


class MemoryManager:
    def __init__(self, user_id: int = 1):
        self.user_id = user_id
        self.pending = None  # 🧠 pending confirmation memory

    # -----------------------------
    # PENDING MEMORY (CONFIRMATION)
    # -----------------------------
    def set_pending(self, mem_type, key, value, importance=5):
        self.pending = {
            "mem_type": mem_type,
            "key": key,
            "value": value,
            "importance": importance,
        }

    def confirm_pending(self, mode: str):
        if not self.pending:
            return False

        if mode == "permanent":
            self.store_memory(
                self.pending["mem_type"],
                self.pending["key"],
                self.pending["value"],
                self.pending["importance"],
            )

        elif mode == "temporary":
            self.store_session(
                f"{self.pending['key']}={self.pending['value']}"
            )

        self.pending = None
        return True

    def clear_pending(self):
        self.pending = None

    # -----------------------------
    # LONG-TERM MEMORY
    # -----------------------------
    def store_memory(
        self,
        mem_type: str,
        key: str,
        value: str,
        importance: int = 5,
        confidence: float = 0.8
    ):
        existing = db.fetchone(
            "SELECT id FROM memory WHERE user_id = ? AND key = ?",
            (self.user_id, key)
        )

        if existing:
            db.execute(
                """
                UPDATE memory
                SET value = ?, importance = ?, confidence = ?, last_updated = ?
                WHERE id = ?
                """,
                (value, importance, confidence, datetime.now(), existing["id"])
            )
        else:
            db.execute(
                """
                INSERT INTO memory (user_id, type, key, value, importance, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (self.user_id, mem_type, key, value, importance, confidence)
            )

    # -----------------------------
    # SESSION MEMORY (TEMPORARY)
    # -----------------------------
    def store_session(self, content: str):
        db.execute(
            "INSERT INTO session_memory (content) VALUES (?)",
            (content,)
        )

    def clear_session(self):
        db.execute("DELETE FROM session_memory")

    # -----------------------------
    # MEMORY RETRIEVAL
    # -----------------------------
    def recall(self, key: str):
        return db.fetchone(
            "SELECT value FROM memory WHERE user_id = ? AND key = ?",
            (self.user_id, key)
        )

    # -----------------------------
    # COMMAND LOGGING
    # -----------------------------
    def log_command(self, command_text: str, intent: str):
        db.execute(
            """
            INSERT INTO commands (user_id, command_text, intent)
            VALUES (?, ?, ?)
            """,
            (self.user_id, command_text, intent)
        )

    # -----------------------------
    # MOOD TRACKING
    # -----------------------------
    def log_mood(self, polarity: float, label: str):
        db.execute(
            """
            INSERT INTO mood_history (user_id, polarity, label)
            VALUES (?, ?, ?)
            """,
            (self.user_id, polarity, label)
        )

    def get_rolling_mood(self) -> str:
        # Get average polarity over the last 5 interactions
        rows = db.fetchall(
            """
            SELECT polarity, label FROM mood_history
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 5
            """,
            (self.user_id,)
        )
        if not rows:
            return "Neutral/Stable"
            
        avg_polarity = sum(r["polarity"] for r in rows) / len(rows)
        
        if avg_polarity <= -0.4: return "Very Stressed or Upset"
        elif avg_polarity < -0.1: return "Negative or Stressed"
        elif avg_polarity > 0.4: return "Very Happy or Excited"
        elif avg_polarity > 0.1: return "Positive or Cheerful"
        else: return "Neutral or Professional"

    # -----------------------------
    # SHUTDOWN
    # -----------------------------
    def on_shutdown(self):
        self.clear_session()
