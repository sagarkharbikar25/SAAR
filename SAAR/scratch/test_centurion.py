import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add SAAR to path
sys.path.append(os.path.abspath("."))

from core.brain import ask_brain

# Mock speak to prevent actual audio playback during tests
import voice.tts
voice.tts.speak = MagicMock()

class TestCenturionFeatures(unittest.TestCase):
    
    def test_01_core_os_intents(self):
        """Phase 1: Test basic OS intents in brain.py"""
        # Test Volume
        resp, _ = ask_brain("set volume to 50")
        self.assertIn("Volume set to 50", resp)
        
        # Test Brightness
        resp, _ = ask_brain("set brightness to 70")
        self.assertIn("brightness set to 70%", resp.lower())
        
        # Test Lock Screen
        resp, _ = ask_brain("lock my screen")
        self.assertIn("Screen locked", resp)

    def test_02_productivity_intents(self):
        """Phase 2: Test Productivity Hub intents"""
        # Test Stopwatch
        resp, _ = ask_brain("start stopwatch")
        self.assertIn("Stopwatch started", resp)
        
        # Test Pomodoro
        resp, _ = ask_brain("start pomodoro")
        self.assertIn("Pomodoro session started", resp)

    def test_03_developer_intents(self):
        """Phase 3: Test Developer Forge intents"""
        # Test Git Status
        with patch('core.dev_tools.dev_tools.git_status', return_value="On branch main"):
            resp, _ = ask_brain("git status")
            self.assertIn("On branch main", resp)

    def test_04_knowledge_intents(self):
        """Phase 4: Test Knowledge Hub intents"""
        # Test Weather (Mocked)
        with patch('core.knowledge.knowledge_hub.get_weather', return_value="Sunny in Mumbai"):
            resp, _ = ask_brain("weather in Mumbai")
            self.assertIn("Sunny in Mumbai", resp)

    def test_05_final_five_intents(self):
        """Phase 5: Test the Final 5 completion features"""
        # Test Clipboard
        resp, _ = ask_brain("show my clipboard history")
        self.assertIn("recent", resp.lower())
        
        # Test Wallpaper
        with patch('ctypes.windll.user32.SystemParametersInfoW', return_value=1):
             with patch('glob.glob', return_value=["C:\\test.jpg"]):
                resp, _ = ask_brain("change my wallpaper")
                self.assertIn("Wallpaper changed", resp)

if __name__ == "__main__":
    unittest.main()
