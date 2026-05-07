WAKE_WORDS = ["saar", "sar", "sir", "hey saar", "hello saar"]

def extract_command(text: str):
    if not text:
        return False, None

    text = text.lower().strip()

    import re
    # 🔥 Normalize common mistakes with word boundaries
    text = re.sub(r'\b(sar|sir|saa|sarr)\b', 'saar', text)

    # 🔥 Check if wake word is ANYWHERE (not just start)
    for wake in WAKE_WORDS:
        if wake in text:
            command = text.replace(wake, "").strip(" ,.:;")
            return True, command

    return False, None