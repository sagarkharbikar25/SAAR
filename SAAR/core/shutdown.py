# core/shutdown.py

import shutil
from pathlib import Path
from core.memory import MemoryManager


class ShutdownManager:
    def __init__(self, user_id: int = 1):
        self.memory = MemoryManager(user_id)

        # Temporary data locations
        self.temp_paths = [
            Path("voice"),
            Path("temp"),
        ]

    def cleanup_temp_data(self):
        """
        Delete all temporary voice and face data
        """
        for path in self.temp_paths:
            if path.exists() and path.is_dir():
                try:
                    shutil.rmtree(path)
                    path.mkdir(exist_ok=True)
                except Exception as e:
                    print(f"[WARN] Cleanup failed for {path}: {e}")

    def shutdown(self):
        """
        Main shutdown hook for SAAR
        """
        print("[SAAR] Shutdown started")

        # 1. Clear session memory (DB)
        self.memory.on_shutdown()

        # 2. Delete temporary files (voice / face)
        self.cleanup_temp_data()

        print("[SAAR] Shutdown completed safely")
