# core/lifestyle.py
import subprocess
import os

LIFESTYLE_MODEL = "gemma2:9b"

class LifestyleHub:
    def __init__(self):
        pass

    def _run_ollama(self, prompt: str):
        try:
            result = subprocess.run(
                ["ollama", "run", LIFESTYLE_MODEL],
                input=prompt,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=180
            )
            return result.stdout.strip()
        except Exception as e:
            return f"Model error: {e}"

    # ================= WELLNESS =================
    def generate_workout_plan(self, focus: str):
        prompt = f"""You are SAAR, an expert fitness coach. 
Generate a short, concise 3-day workout plan focusing on '{focus}'.
Do not use introductory fillers, just output the plan directly."""
        print(f"\n🏋️ SAAR is building your {focus} workout plan...")
        return self._run_ollama(prompt)

    def generate_diet_plan(self, goal: str):
        prompt = f"""You are SAAR, an expert nutritionist.
Generate a short 1-day sample meal plan (Breakfast, Lunch, Dinner, Snack) for the goal: '{goal}'.
Do not use introductory fillers, just output the plan directly."""
        print(f"\n🥗 SAAR is building your {goal} diet plan...")
        return self._run_ollama(prompt)

    def guide_meditation(self, minutes: int):
        prompt = f"""You are SAAR, a calm meditation guide.
Write a short script for a {minutes}-minute guided meditation. 
Include pauses (e.g., [Pause for 10 seconds]) and focus on deep breathing."""
        print("\n🧘 SAAR is preparing a meditation guide...")
        return self._run_ollama(prompt)

    # ================= HOBBIES & LIFE =================
    def get_recipe(self, dish: str):
        prompt = f"""You are SAAR, a master chef.
Give me a concise recipe for '{dish}'. Include ingredients and steps.
Do not use introductory fillers."""
        print(f"\n🍳 SAAR is finding a recipe for {dish}...")
        return self._run_ollama(prompt)

    def get_pet_plant_care(self, entity: str):
        prompt = f"""You are SAAR, a biology expert.
Give me top 3 essential care tips for: '{entity}'.
Be brief and practical."""
        print(f"\n🌱 SAAR is analyzing care instructions for {entity}...")
        return self._run_ollama(prompt)

    def get_wine_pairing(self, food: str):
        prompt = f"""You are SAAR, a sommelier.
Recommend the best wine pairing for '{food}' and briefly explain why."""
        print(f"\n🍷 SAAR is finding wine pairings for {food}...")
        return self._run_ollama(prompt)

    def get_media_info(self, title: str, media_type: str = "media"):
        prompt = f"""You are SAAR, an entertainment encyclopedia.
Give me a concise summary, release year, and critical reception for the {media_type} titled '{title}'."""
        print(f"\n🎬 SAAR is fetching info for {title}...")
        return self._run_ollama(prompt)

# Global instance
lifestyle_hub = LifestyleHub()
