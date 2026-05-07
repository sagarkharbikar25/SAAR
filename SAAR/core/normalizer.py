# core/normalizer.py

def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower().strip()

    # Common speech mistakes → correct words
    replacements = {
        "sir": "saar",
        "sar": "saar",
        "saar ji": "saar",
        "saarjee": "saar",
        "sa": "saar",
        "hey sir": "hey saar",
        "hello sir": "hello saar",
        "assistant": "saar"
    }

    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)

    return text
