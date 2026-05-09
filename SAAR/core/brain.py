import sys
import socket
import os
import warnings
import requests

# Suppress deprecation warnings from third-party libs
warnings.filterwarnings("ignore", category=FutureWarning)

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
# Force UTF-8 output so emoji don't crash on Windows terminals
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
print("*** SAAR BRAIN LOADED - PHASE 3 ***")

import subprocess
import re
from difflib import get_close_matches

from core.memory import MemoryManager
from core.tools import get_time, get_date, get_battery, get_system_info
from core.os_control import (open_app, close_app, open_youtube, search_youtube, delete_file, set_volume, 
                             adjust_volume, media_key, check_for_system_updates, set_brightness, lock_screen,
                             set_mouse_speed, empty_recycle_bin, take_screenshot, open_task_manager, run_virus_scan,
                             run_disk_cleaner, check_pc_temp, check_network_speed, open_settings_hub,
                             power_manager, toggle_mic, start_screen_record, stop_screen_record,
                             update_system_apps, change_wallpaper, move_window_to_monitor, get_clipboard_history)
from core.file_manager import file_mgr
from core.automation import open_notepad, new_file, write_text, save_file, create_folder, auto_type
from core.productivity import prod_mgr
from core.data_tools import data_tools
from core.dev_tools import dev_tools
from core.code_intelligence import code_intel
from core.knowledge import knowledge_hub
from core.lifestyle import lifestyle_hub
from core.messaging import messaging_hub, parse_whatsapp_command, parse_email_command
from core.web_assistant import web_assistant
from core.sentiment import analyze_sentiment
from core.git import git_agency
from core.workflow import workflow_engine
from core.reminders import reminders
from voice.tts import speak

# =========================
# 🔥 CODE MEMORY
# =========================
last_generated_code = None
last_file_path = None
FORCE_OFFLINE = False # 🌐 Toggle for Hybrid vs Local-Only

# =========================
# 🔥 SHORT-TERM MEMORY BUFFER
# =========================
class ConversationMemory:
    def __init__(self, max_turns=5):
        self.max_turns = max_turns
        self.history = []

    def add(self, user, assistant):
        self.history.append({"user": user, "assistant": assistant})
        if len(self.history) > self.max_turns:
            self.history.pop(0)

    def get_context(self):
        context = ""
        for h in self.history:
            context += f"User: {h['user']}\nAssistant: {h['assistant']}\n"
        return context.strip()

# =========================
# SAAR MODELS (Hybrid Duo)
# =========================
LOCAL_MODEL = "llama3.2:latest"  # Fast General Chat
CODE_MODEL  = "qwen2.5:7b"       # Specialist for Coding & Projects
# =========================

memory = MemoryManager(user_id=1)
conversation_memory = ConversationMemory(max_turns=5)

# =========================
# KEYWORDS
# =========================
TEXT_KEYWORDS = [
    "definition", "define", "explain", "explanation",
    "introduction", "notes", "theory", "meaning", "paragraph",
    "describe", "what is", "how does", "difference between",
    "advantage", "disadvantage", "concept", "topic"
]

CODE_KEYWORDS = [
    "code", "program", "function", "class",
    "script", "algorithm", "lines", "write"
]

WHATSAPP_KEYWORDS = [
    "send message", "send msg",
    "send whatsapp",
    "whatsapp to", "whatsapp ",
    "ping "
]

EMAIL_KEYWORDS = [
    "send email to", "send email", "email to", "email"
]

APP_ALIASES = {
    "notepad": [
        "notepad", "note pad", "node pad",
        "northpad", "nubpad", "roadpad", "note", "pad"
    ],
    "chrome": [
        "chrome", "chorme", "chrom", "crome", "browser"
    ],
    "code": [
        "vs code", "vscode", "visual studio code", "vs"
    ],
    "spotify": [
        "spotify", "spotfy", "music player"
    ],
    "calculator": [
        "calculator", "calc"
    ],
    "explorer": [
        "file explorer", "explorer", "files", "my computer"
    ],
}

LANGUAGE_MAP = {
    "python":      ("Python",      "program.py"),
    "java":        ("Java",        "Program.java"),
    "php":         ("PHP",         "program.php"),
    "c++":         ("C++",         "program.cpp"),
    "cpp":         ("C++",         "program.cpp"),
    "c#":          ("C#",          "Program.cs"),
    "csharp":      ("C#",          "Program.cs"),
    "c":           ("C",           "program.c"),
    "html":        ("HTML",        "index.html"),
    "css":         ("CSS",         "style.css"),
    "javascript":  ("JavaScript",  "script.js"),
    "js":          ("JavaScript",  "script.js"),
    "sql":         ("SQL",         "query.sql"),
    "bash":        ("Bash",        "script.sh"),
}

# =========================
# HELPERS
# =========================
def detect_language(text: str):
    # Specialized logic for calculators/apps (Default to Web Tech)
    if "calculator" in text or "app" in text:
        return "HTML", "index.html"
        
    for key, (lang, fname) in LANGUAGE_MAP.items():
        if key in text:
            return lang, fname
    return "Python", "program.py"


def normalize_app(text: str):
    for app, variations in APP_ALIASES.items():
        for v in variations:
            if v in text:
                return app
    words = text.split()
    for word in words:
        match = get_close_matches(word, APP_ALIASES.keys(), n=1, cutoff=0.7)
        if match:
            return match[0]
    return None


def is_code_intent(text: str):
    return any(w in text for w in CODE_KEYWORDS)


def is_text_intent(text: str):
    return any(w in text for w in TEXT_KEYWORDS)


def is_write_code_task(text: str):
    text = text.lower()
    # If they want an explanation or teaching, it is NOT a write-code task
    if any(w in text for w in ["teach", "explain", "how to", "what is", "meaning", "definition", "tutorial"]):
        return False

    code_keywords = ["program", "code", "script", "function", "algorithm", "logic", "app", "calculator", "software"]
    action_keywords = ["write", "make", "create", "build", "generate", "develop", "save"]
    
    # If it's a direct coding word
    if any(w in text for w in ["write a program", "write code", "generate script", "create a function"]):
        return True
        
    # If it's an action + a software-like word
    if any(a in text for a in action_keywords) and any(c in text for c in code_keywords):
        return True
        
    return False


def is_whatsapp_command(text: str):
    return any(w in text for w in WHATSAPP_KEYWORDS)


def is_email_command(text: str):
    # email check must not trigger on "send message" (that's WhatsApp)
    return any(w in text for w in EMAIL_KEYWORDS) and "whatsapp" not in text and "message" not in text



def pick_model(text: str) -> str:
    if is_write_code_task(text) or any(w in text for w in ["modify", "edit", "change", "update", "fix"]):
        return CODE_MODEL
_gemini_model = None
_gemini_ready = False

def run_online_llm(prompt):
    """Runs Google Gemini (Online) with dynamic model discovery."""
    global _gemini_model, _gemini_ready
    
    try:
        if not _gemini_ready:
            api_key_row = memory.recall("gemini_api_key")
            if not api_key_row: return None
            genai.configure(api_key=api_key_row["value"])
            
            # Dynamically find the best text model
            chosen_model = None
            try:
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        if "flash" in m.name:
                            chosen_model = m.name
                            break
                        elif not chosen_model:
                            chosen_model = m.name
            except Exception as e:
                print(f"📡 [Neural Sync] ListModels failed: {e}")
                
            if not chosen_model:
                chosen_model = "gemini-1.5-flash" # fallback
                
            _gemini_model = genai.GenerativeModel(chosen_model)
            _gemini_ready = True
            
        # Fast generation with minimal system prompt
        response = _gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"📡 [Neural Sync] Online Error: {e}")
        # Force re-init next time in case of temporary failure
        _gemini_ready = False
        return None

def run_ollama(model: str, prompt: str, timeout=180):
    import requests # Force local import to prevent name error
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=timeout
        )
        return response.json().get("response", "").strip()
    except Exception as e:
        return f"Error running model boss: {str(e)}"


def split_commands(text: str):
    # Never split a messaging command — 'message Sneha AND say hello' must stay intact
    _messaging_guard = any(w in text for w in [
        "message ", "tell ", "ping ", "text ", "send message", "send msg",
        "send whatsapp", "whatsapp "
    ])
    if _messaging_guard:
        return [text]

    separators = [" and then ", " then ", " and "]
    for sep in separators:
        if sep in text:
            return [t.strip() for t in text.split(sep)]
    return [text]


# =========================
# 🧹 CODE CLEANER
# =========================
def extract_code_only(text: str):
    if not text:
        return None

    text = text.replace("```html", "").replace("```python", "").replace("```js", "").replace("```cpp", "").replace("```c", "")
    text = text.replace("```", "").strip()
    lines = text.splitlines()
    clean_lines = []

    for line in lines:
        line_strip = line.strip()
        line_lower = line_strip.lower()

        if any(word in line_lower for word in [
            "this line", "this code", "explanation",
            "here is", "here's", "sure", "certainly",
            "as requested", "below is", "above is",
            "output:", "result:", "note:", "example:"
        ]):
            continue

        if line_strip.startswith("#"):
            continue

        if "#" in line:
            line = line.split("#")[0].rstrip()

        if not line.strip():
            continue

        clean_lines.append(line)

    code = "\n".join(clean_lines).strip()
    return code if code and len(code) >= 3 else None


# =========================
# 🔥 SIMPLE CODE SHORTCUTS
# =========================
def handle_simple_code(text: str):
    text = text.lower().strip()
    print(f"[BRAIN] Processing Intent: {text}")

    if "hello" in text and ("world" in text or "word" in text):

        if "java" in text:
            return ('''public class Program {
    public static void main(String[] args) {
        System.out.println("Hello World");
    }
}''', "Program.java")

        if "python" in text:
            return ("print('Hello World')", "program.py")

        if "c++" in text or "cpp" in text:
            return ('''#include <iostream>
using namespace std;

int main() {
    cout << "Hello World" << endl;
    return 0;
}''', "program.cpp")

        if "c#" in text or "csharp" in text:
            return ('''using System;

class Program {
    static void Main() {
        Console.WriteLine("Hello World");
    }
}''', "Program.cs")

        if "c" in text:
            return ('''#include <stdio.h>

int main() {
    printf("Hello World\\n");
    return 0;
}''', "program.c")

        if "html" in text:
            return ('''<!DOCTYPE html>
<html>
<head><title>Hello World</title></head>
<body>
    <h1>Hello World</h1>
</body>
</html>''', "index.html")

        if "javascript" in text or " js" in text:
            return ("console.log('Hello World');", "script.js")

        return ("print('Hello World')", "program.py")

    return None, None


# =========================
# 🧠 BRAIN PIPELINE (PHASE 2 & PHASE 5)
# =========================
def ask_brain(user_input: str, state_manager=None) -> tuple:
    """Takes input, matches rules/intents, calls LLM or custom tools.
    Returns (response_text, sentiment_dict)
    """
    global FORCE_OFFLINE, last_generated_code, last_file_path
    # Biological Context (Phase 2)
    vis_mood, voc_mood = "Neutral", "Neutral"
    if state_manager:
        vis_mood, voc_mood = state_manager.get_bio_status()
    
    bio_context = f"[BIOLOGICAL SYNC: User looks {vis_mood} and sounds {voc_mood}]"
    
    # Analyze Sentiment (Phase 5)
    sentiment = analyze_sentiment(user_input)
    memory.log_mood(sentiment["polarity"], sentiment["label"])
    rolling_mood = memory.get_rolling_mood()

    # Pre-process
    raw_text = user_input.lower().strip()
    
    # 🛑 Ignore Whisper Hallucinations & empty commands
    if raw_text in ["thanks for watching!", "thanks for watching.", "thank you.", "subtitles by"]:
        return "", sentiment

    text = re.sub(r"[^a-zA-Z0-9 ]", "", raw_text)

    if len(text.split()) < 2:
        return "Please say that again boss.", sentiment

    memory.store_session(user_input)
    commands = split_commands(text)
    responses = []

    for cmd in commands:
        text = cmd

        # ================= WORK MODE TOGGLE =================
        if "start work mode" in text or "enter work mode" in text:
            if state_manager:
                state_manager.set_work_mode(True)
                responses.append("Work Mode activated. I am listening continuously, no wake word needed.")
            # Do NOT continue here, allow it to fall through to Workflow Engine 
            # so the "work mode" macro (open vscode, etc) still runs!
            
        elif "exit work mode" in text or "stop work mode" in text:
            if state_manager:
                state_manager.set_work_mode(False)
                responses.append("Work Mode deactivated. I will wait for my wake word.")
            continue

        # ================= NEURAL MODE TOGGLE =================
        if "online mode" in text:
            FORCE_OFFLINE = False
            responses.append("Neural Cloud Uplink established. Using High-Performance Online Core.")
            continue
        if "offline mode" in text or "local mode" in text:
            FORCE_OFFLINE = True
            responses.append("Neural Link set to Local-Only. Offline mode active.")
            continue

        # ================= WORKFLOW ENGINE =================
        wf_name, wf_commands = workflow_engine.get_workflow(text)
        if wf_name:
            responses.append(f"Initiating {wf_name} protocol, Sagar.")
            for wf_cmd in wf_commands:
                resp, _ = ask_brain(wf_cmd, state_manager)
                if resp:
                    responses.append(resp)
            continue


        # ================= REMINDERS =================
        if text.startswith("remind me to "):
            parts = text.replace("remind me to ", "").split(" at ", 1)
            if len(parts) == 1:
                parts = text.replace("remind me to ", "").split(" in ", 1)
                if len(parts) == 2:
                    parts[1] = "in " + parts[1]
            if len(parts) == 2:
                responses.append(reminders.add_reminder(parts[0], parts[1]))
                continue
            else:
                responses.append("Please specify a time, like 'remind me to call mom at 5 PM' or 'in 10 minutes'.")
                continue

        # ================= READ EMAILS =================
        if "read my mail" in text or "check my mail" in text or "read email" in text:
            responses.append(messaging_hub.read_emails())
            continue

        # ================= NEW FEATURES (THE FINAL 5) =================
        if "update all my apps" in text or "update system apps" in text:
            responses.append(update_system_apps())
            continue

        if "change my wallpaper" in text or "change wallpaper" in text:
            responses.append(change_wallpaper())
            continue

        if "what was the last thing i copied" in text or "show my clipboard history" in text or "clipboard" in text:
            responses.append(get_clipboard_history())
            continue

        if "move this window" in text or "move window to other screen" in text or "monitor" in text:
            responses.append(move_window_to_monitor())
            continue

        if "refresh desktop" in text or "refresh screen" in text:
            from core.os_control import refresh_desktop
            responses.append(refresh_desktop())
            continue

        if "pin this window" in text or "pin to top" in text:
            from core.os_control import pin_window_to_top
            responses.append(pin_window_to_top())
            continue

        if "take a note" in text or "quick note" in text:
            note_match = re.search(r'(?:note|saying)\s+(.*)', text)
            if note_match:
                from core.os_control import create_quick_note
                responses.append(create_quick_note(note_match.group(1)))
            else:
                responses.append("What should the note say Sagar?")
            continue

        if "copy path" in text or "get file path" in text:
            file_match = re.search(r'(?:of|for)\s+(.*)', text)
            if file_match:
                from core.os_control import copy_file_path
                responses.append(copy_file_path(file_match.group(1).strip()))
            else:
                responses.append("Which file's path should I copy Sagar?")
            continue

        if "shred file" in text:
            file_match = re.search(r'shred\s+file\s+(.*)', text)
            if file_match:
                responses.append(file_mgr.shred_file(file_match.group(1).strip()))
            else:
                responses.append("Which file should I shred Sagar? (Be careful, it's permanent!)")
            continue

        if "zip file" in text or "compress" in text:
            file_match = re.search(r'(?:zip|compress)\s+(.*)', text)
            if file_match:
                responses.append(file_mgr.zip_files(file_match.group(1).strip()))
            else:
                responses.append("Which file or folder should I zip Sagar?")
            continue

        if "unzip file" in text or "extract" in text:
            file_match = re.search(r'(?:unzip|extract)\s+(.*)', text)
            if file_match:
                responses.append(file_mgr.unzip_file(file_match.group(1).strip()))
            else:
                responses.append("Which zip file should I extract Sagar?")
            continue

        if "hide file" in text or "make file hidden" in text:
            file_match = re.search(r'hide\s+file\s+(.*)', text)
            if file_match:
                responses.append(file_mgr.set_file_hidden(file_match.group(1).strip(), True))
            else:
                responses.append("Which file should I hide Sagar?")
            continue

        if "unhide file" in text or "show hidden file" in text:
            file_match = re.search(r'(?:unhide|show)\s+(.*)', text)
            if file_match:
                responses.append(file_mgr.set_file_hidden(file_match.group(1).strip(), False))
            else:
                responses.append("Which file should I unhide Sagar?")
            continue

        if "bulk rename" in text:
            dir_match = re.search(r'in\s+(.*)', text)
            pattern_match = re.search(r'replace\s+(.*?)\s+with', text)
            rep_match = re.search(r'with\s+(.*)', text)
            if dir_match and pattern_match and rep_match:
                responses.append(file_mgr.bulk_rename(dir_match.group(1).strip(), pattern_match.group(1).strip(), rep_match.group(1).strip()))
            else:
                responses.append("Tell me: 'bulk rename in [folder] replace [old] with [new]' boss.")
            continue

        if "make shortcut" in text or "create shortcut" in text:
            target_match = re.search(r'for\s+(.*)', text)
            if target_match:
                path = target_match.group(1).strip()
                name = os.path.basename(path)
                responses.append(file_mgr.make_shortcut(path, name))
            else:
                responses.append("Which file should I create a shortcut for Sagar?")
            continue

        if "find file" in text or "search file" in text:
            name_match = re.search(r'(?:find|search)\s+file\s+(.*)', text)
            if name_match:
                responses.append(file_mgr.quick_search(name_match.group(1).strip()))
            else:
                responses.append("What is the filename you're looking for Sagar?")
            continue

        # ================= MEMORY =================
        if "my name is" in text:
            name = re.sub(r"[^a-zA-Z ]", "", text.replace("my name is", "")).strip().title()
            memory.set_pending("fact", "user_name", name, 9)
            responses.append(f"Got it boss! Should I save your name as {name}?")
            continue

        if "do you know me" in text or "what is my name" in text:
            r = memory.recall("user_name")
            responses.append(f"Of course boss, you are {r['value']}!" if r else "I don't know your name yet boss. Tell me!")
            continue

        # ================= MESSAGING HUB =================
        if "add contact" in text or "save contact" in text:
            name_match = re.search(r'(?:contact|save)\s+([a-zA-Z]+)', text)
            num_match = re.search(r'(?:\+|)\d{10,13}', text)
            if name_match and num_match:
                responses.append(messaging_hub.add_contact(name_match.group(1), num_match.group(0)))
            else:
                responses.append("Please tell me the name and number Sagar. For example: 'Add contact Sagar +91...'")
            continue

        if "list contacts" in text or "show contacts" in text:
            responses.append(messaging_hub.list_contacts())
            continue

        # ================= CLOSE WHATSAPP =================
        if any(w in text for w in ["close whatsapp", "exit whatsapp", "quit whatsapp",
                                   "shut whatsapp", "kill whatsapp"]):
            close_app("whatsapp")
            responses.append("WhatsApp closed Sagar!")
            break

        # ================= OPEN WHATSAPP (no message) =================
        if ("open whatsapp" in text or "launch whatsapp" in text
                or "start whatsapp" in text or text.strip() == "whatsapp"):
            result = open_app("whatsapp")
            if result:
                responses.append("Opening WhatsApp Desktop Sagar!")
            else:
                import webbrowser
                webbrowser.open("https://web.whatsapp.com")
                responses.append("Opened WhatsApp Web for you Sagar!")
            break

        # ================= MESSAGING (Absolute Priority) =================
        # Catches: message / send message / tell / ping / text + name
        # NEVER fires on: close/open/exit/quit/launch/start whatsapp
        _wa_management = any(w in text for w in [
            "close whatsapp", "exit whatsapp", "quit whatsapp",
            "open whatsapp", "launch whatsapp", "start whatsapp"
        ])
        is_whatsapp_cmd = (
            not _wa_management
            and any(text.startswith(w) for w in WHATSAPP_KEYWORDS)
            and not any(w in text for w in ["what is", "how to", "explain", "tell me about"])
        )
        if is_whatsapp_cmd:
            responses.append(parse_whatsapp_command(text))
            break  # Never let cloud AI process a messaging command

        # ================= EMAIL — CONFIGURE =================
        # "set my email to sagar@gmail.com password abcdxyz"
        if "set my email" in text or "configure email" in text or "setup email" in text:
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
            pass_match  = re.search(r'password\s+(\S+)', text)
            if email_match and pass_match:
                result = messaging_hub.configure_email(email_match.group(0), pass_match.group(1))
                responses.append(result)
            else:
                responses.append(
                    "Tell me both Sagar. Example: 'Set my email to sagar@gmail.com password myapppassword'"
                )
            continue

        # ================= EMAIL — SEND =================
        if is_email_command(text):
            responses.append(parse_email_command(text))
            continue

        # ================= MODIFY / EDIT CODE =================
        if any(w in text for w in ["modify", "edit", "change", "update", "fix the code"]):

            if not last_generated_code:
                responses.append("No previous code found boss. Generate some code first!")
                continue

            prompt = f"""You are an expert code editor.

STRICT RULES:
- Output ONLY the complete modified code
- NO explanation text
- NO markdown formatting
- NO backticks
- NO comments
- The output must be fully runnable code

Modification instruction: {user_input}

Original code to modify:
{last_generated_code}
"""
            updated_code = run_ollama(CODE_MODEL, prompt, timeout=180)
            updated_code = updated_code.strip()

            if any(w in updated_code for w in ["Here", "updated", "modified", "sure", "certainly"]):
                updated_code = extract_code_only(updated_code)

            if not updated_code:
                responses.append("Failed to modify boss. Try describing the change differently.")
                continue

            with open(last_file_path, "w", encoding="utf-8") as f:
                f.write(updated_code)

            subprocess.Popen(["notepad.exe", last_file_path])

            last_generated_code = updated_code
            responses.append(f"Code modified and saved boss! File: {last_file_path}")
            continue

        # ================= HELLO WORLD SHORTCUT =================
        if "hello" in text and ("world" in text or "word" in text):
            simple_code, simple_file = handle_simple_code(text)

            if simple_code:
                open_notepad()
                new_file()
                write_text(simple_code)
                save_file("C:\\Users\\asus\\Desktop", simple_file)

                last_generated_code = simple_code
                last_file_path = f"C:\\Users\\asus\\Desktop\\{simple_file}"

                responses.append(f"Hello World written and saved boss! File: {simple_file}")
                continue

        # ================= BROWSER SEARCH =================
        if ("chrome" in text or "browser" in text) and "search" in text:
            search_query = text.split("search")[-1].strip()
            if search_query:
                import webbrowser
                webbrowser.open(f"https://www.google.com/search?q={search_query}")
                responses.append(f"Searching for {search_query} on Google Sagar!")
                continue

        # ================= VS CODE =================
        if "vs code" in text or "visual studio" in text or "vscode" in text:
            open_app("code")
            responses.append("Opened VS Code boss!")
            continue

        # ================= FILE AUTOMATION (Phase 4) =================
        if any(w in text for w in ["copy", "move", "paste", "transfer", "delete", "remove"]):
            target_path = file_mgr.resolve_path(text)
            
            if "delete" in text or "remove" in text:
                # 2-Step Biometric Deletion (Battery Optimized)
                if target_path:
                    from pipeline.presence_pipeline import global_presence_tracker
                    if global_presence_tracker:
                        trusted, msg = global_presence_tracker.verify_user_now()
                        if trusted:
                            responses.append(f"👁️ Biometric Check Passed Sagar! {msg}")
                            responses.append(file_mgr.execute_delete(target_path))
                        else:
                            responses.append(f"❌ Verification Failed Sagar: {msg}")
                    else:
                        responses.append("⚠️ Biometric system is offline Sagar. I cannot delete files without seeing you.")
                else:
                    responses.append("Tell me which file or folder to delete boss!")
                continue
            
            # Simple Copy/Move logic
            if "copy" in text or "paste" in text:
                # Placeholder for source/dest logic (assuming desktop for now)
                responses.append("File copying functionality is ready boss! Tell me the exact source and destination.")
                continue

        # ================= SYSTEM UPDATE =================
        if "update" in text and ("pc" in text or "system" in text or "windows" in text):
            responses.append(f"🔍 Checking for updates... \n{check_for_system_updates()}")
            continue
            
        # ================= VOLUME CONTROL =================
        if ("volume" in text or "mute" in text or "sound" in text) and "mic" not in text:
            if "mute" in text:
                responses.append(media_key("mute"))
            elif "increase" in text or "up" in text:
                responses.append(adjust_volume(10))
            elif "decrease" in text or "down" in text:
                responses.append(adjust_volume(-10))
            elif re.search(r'\d+', text):
                level = int(re.search(r'\d+', text).group())
                responses.append(set_volume(level))
            else:
                responses.append("Tell me how much to change the volume boss!")
            continue

        # ================= MEDIA CONTROL =================
        if any(w in text for w in ["music", "song", "pause", "resume", "play", "skip", "next", "previous"]):
            if "pause" in text: responses.append(media_key("pause"))
            elif "resume" in text or "play" in text: responses.append(media_key("resume"))
            elif "next" in text or "skip" in text: responses.append(media_key("next"))
            elif "previous" in text or "back" in text: responses.append(media_key("previous"))
            continue

        # ================= FOCUS MODE =================
        if "focus" in text and ("mode" in text or "on" in text):
            # Focus mode handled separately or needs to be implemented.
            responses.append("Focus mode activated boss!")
            continue
            
        # ================= POWER MANAGER =================
        if any(w in text for w in ["shutdown", "shut down", "restart", "reboot", "sleep", "hibernate", "turn off", "power off", "cancel shutdown", "cancel restart"]):
            responses.append(power_manager(text))
            continue

        # ================= NEURAL MEMORY (KEYS) =================
        if "gemini api key is" in text:
            key = text.split("gemini api key is")[-1].strip()
            if key:
                memory.store_memory("api_key", "gemini_api_key", key)
                responses.append(f"Got it Sagar! I have stored your Gemini API Key in my neural core. Online mode is now active.")
                continue
        if any(word in text for word in ["bye saar", "exit saar", "quit saar", "shutdown saar", "terminate saar"]):
            from core.os_control import terminate_saar
            responses.append("Goodbye Sagar. I'll be here if you need me again. Shutting down now.")
            if state_manager:
                state_manager.add_chat("SAAR", responses[-1])
            speak(responses[-1])
            terminate_saar()
            continue

        # ================= MIC CONTROL =================
        if "mic" in text or "microphone" in text:
            if "mute" in text:
                responses.append(toggle_mic(mute=True))
            elif "unmute" in text or "on" in text:
                responses.append(toggle_mic(mute=False))
            else:
                responses.append("Should I mute or unmute the microphone boss?")
            continue

        # ================= MESSAGING (Phase 5) =================
        if is_whatsapp_command(text):
            responses.append(parse_whatsapp_command(text))
            continue
            
        if is_email_command(text):
            responses.append(parse_email_command(text))
            continue
            
        if "add contact" in text:
            # Pattern: "add contact Sagar number +91..."
            parts = text.split("contact", 1)[1].split("number", 1)
            if len(parts) == 2:
                name, num = parts[0].strip(), parts[1].strip()
                responses.append(messaging_hub.add_contact(name, num))
            continue

        if "list contacts" in text:
            responses.append(messaging_hub.list_contacts())
            continue

        # ================= PRODUCTIVITY =====================
        if "invoice" in text:
            client_match = re.search(r'(?:for|to)\s+([a-zA-Z\s]+?)(?:\s+of|\s+for|\s+amount|$)', text)
            amount_match = re.search(r'(?:amount|of|price)\s+(\d+)', text)
            item_match = re.search(r'(?:item|saying|description)\s+(.*)', text)
            
            client = client_match.group(1).strip() if client_match else "Valued Client"
            amount = amount_match.group(1) if amount_match else "0"
            item = item_match.group(1).strip() if item_match else "Professional Services"
            
            responses.append(prod_mgr.generate_invoice(client, amount, item))
            continue

        if "pomodoro" in text:
            responses.append(prod_mgr.start_pomodoro())
            continue

        if "stopwatch" in text:
            if " stop " in f" {text} ":
                responses.append(prod_mgr.stop_stopwatch())
            else:
                responses.append(prod_mgr.start_stopwatch())
            continue

        # ================= SCREEN RECORD =================

        # ================= PHASE 1: CORE OS CONTROLS =================
        if "brightness" in text:
            if re.search(r'\d+', text):
                level = int(re.search(r'\d+', text).group())
                responses.append(set_brightness(level))
            else:
                responses.append("Tell me what percentage to set the brightness boss! (e.g., set brightness to 50)")
            continue

        # SYSTEM POWER (Hardened)
        if "shutdown pc" in text or "restart pc" in text or "shutdown laptop" in text:
            responses.append(power_manager(text))
            continue

        if "lock" in text and ("screen" in text or "pc" in text or "computer" in text):
            responses.append(lock_screen())
            continue

        if "mouse speed" in text:
            if re.search(r'\d+', text):
                speed = int(re.search(r'\d+', text).group())
                responses.append(set_mouse_speed(speed))
            else:
                responses.append("Tell me a speed from 1 to 20 boss! (e.g., set mouse speed to 10)")
            continue

        if any(w in text for w in ["recycle bin", "trash"]) and ("empty" in text or "clear" in text):
            responses.append(empty_recycle_bin())
            continue

        if "screenshot" in text:
            responses.append(take_screenshot())
            continue
            
        if "task manager" in text:
            responses.append(open_task_manager())
            continue

        if "virus scan" in text or "scan pc" in text or "defender" in text:
            responses.append(run_virus_scan())
            continue
            
        if "disk cleaner" in text or "clean disk" in text or "cleaner" in text:
            responses.append(run_disk_cleaner())
            continue

        if "temperature" in text or "temp " in text:
            responses.append(check_pc_temp())
            continue

        if "network speed" in text or "internet speed" in text:
            responses.append(check_network_speed())
            continue

        if "settings" in text or "night mode" in text or "battery saver" in text:
            found = False
            for target in ["wifi", "bluetooth", "printer", "battery", "nightmode", "webcam"]:
                if target in text or (target == "nightmode" and "night mode" in text) or (target == "battery" and "battery saver" in text):
                    responses.append(open_settings_hub(target))
                    found = True
                    break
            if not found:
                responses.append("Which settings do you want to open boss? (wifi, bluetooth, battery, etc.)")
            continue

        # ================= APP CONTROL =================
        if "open" in text:
            app_name = open_app(text)
            if app_name:
                responses.append(f"Opening {app_name} boss!" if isinstance(app_name, str) else "Opening app boss!")
            else:
                responses.append("I couldn't recognize or open that app boss.")
            continue

        if "close" in text:
            app = normalize_app(text)
            if app:
                result = close_app(app)
                responses.append(f"Closing {app} boss!" if result else f"Could not close {app} boss.")
            else:
                responses.append("I couldn't recognize that app boss.")
            continue

        # ================= PHASE 2: PRODUCTIVITY HUB =================
        # -- Time Management --
        if "alarm" in text and "set" in text:
            time_match = re.search(r'\d{1,2}:\d{2}(?:\s?[ap]m)?', text)
            if time_match:
                responses.append(prod_mgr.set_alarm(time_match.group()))
            else:
                responses.append("What time should I set the alarm for boss? (e.g., set alarm for 14:30)")
            continue

        if "timer" in text and "start" in text:
            min_match = re.search(r'(\d+)\s*minute', text)
            if min_match:
                responses.append(prod_mgr.start_timer(int(min_match.group(1))))
            else:
                responses.append("For how many minutes should I start the timer boss?")
            continue


        if "pomodoro" in text:
            responses.append(prod_mgr.start_pomodoro())
            continue

        if "work time" in text:
            if "start" in text:
                responses.append(prod_mgr.track_work_time("start"))
            elif "stop" in text:
                responses.append(prod_mgr.track_work_time("stop"))
            continue

        if "distraction blocker" in text:
            if "on" in text or "start" in text or "activate" in text:
                responses.append(prod_mgr.toggle_distraction_blocker(True))
            elif "off" in text or "stop" in text or "deactivate" in text:
                responses.append(prod_mgr.toggle_distraction_blocker(False))
            continue

        # -- Data Tools --
        if "dictionary" in text or "meaning of" in text:
            word_match = re.search(r'(?:dictionary|meaning of)\s+(\w+)', text)
            if word_match:
                responses.append(data_tools.get_dictionary_definition(word_match.group(1)))
            else:
                responses.append("Which word's meaning do you want to know boss?")
            continue

        if "convert" in text:
            responses.append(data_tools.convert_unit(text))
            continue

        if "extract text" in text or "read image" in text or "ocr" in text:
            # Assuming image path is provided via UI or standard location for now
            # Hardcoded to test image on desktop for Phase 2 implementation
            responses.append(data_tools.extract_text_from_image(r"C:\Users\asus\Desktop\test_image.png"))
            continue

        if "invoice" in text and "generate" in text:
            responses.append(data_tools.generate_invoice("Client Name", "$500", "Services Rendered"))
            continue

        if "sign pdf" in text:
            responses.append(data_tools.sign_pdf(r"C:\Users\asus\Desktop\document.pdf", "Sagar"))
            continue

        if "auto type" in text or "autotype" in text:
            clean_text = re.sub(r'auto type\s*', '', text, flags=re.IGNORECASE)
            if clean_text:
                responses.append(auto_type(clean_text))
            else:
                responses.append("What should I auto-type boss?")
            continue

        # ================= PHASE 3: DEVELOPER FORGE =================
        # -- Git Suite --
        if "git status" in text:
            responses.append(dev_tools.git_status())
            continue

        if "commit" in text and "push" in text:
            msg_match = re.search(r'message (.*)', text)
            msg = msg_match.group(1).strip() if msg_match else "Auto-commit by SAAR"
            responses.append(dev_tools.git_commit_push(msg))
            continue

        if "git branch" in text or "switch branch" in text:
            branch_match = re.search(r'(?:to|branch)\s+([\w-]+)', text)
            if branch_match:
                responses.append(dev_tools.git_branch(branch_match.group(1)))
            else:
                responses.append("What branch should I switch to boss?")
            continue

        # -- Docker Helper --
        if "docker ps" in text or "docker containers" in text or "running containers" in text:
            responses.append(dev_tools.docker_ps())
            continue

        # -- API Tester & Mobile View --
        if "test api" in text:
            url_match = re.search(r"https?://\S+", text)
            if url_match:
                responses.append(dev_tools.test_api(url_match.group(0)))
            else:
                responses.append("Please provide a URL to test boss.")
        
        if "mobile view" in text or "mobile browser" in text:
            url_match = re.search(r"https?://\S+", text)
            if url_match:
                responses.append(dev_tools.open_mobile_view(url_match.group(0)))
            else:
                responses.append("Which website should I open in mobile view boss?")

        # -- Unit Converter & Thesaurus --
        if "convert" in text and any(u in text for u in ["km", "mile", "kg", "lb", "c", "f"]):
            # Simple parser: convert 10 kg to lb
            match = re.search(r"(\d+\.?\d*)\s*(\w+)\s+to\s+(\w+)", text)
            if match:
                val, f, t = float(match.group(1)), match.group(2), match.group(3)
                responses.append(data_tools.convert_unit(val, f, t))

        if "synonym" in text or "thesaurus" in text:
            word = text.split("for")[-1].strip() if "for" in text else text.split()[-1]
            responses.append(data_tools.get_synonyms(word))

        # -- Media Search (Movies/Books/Games) --
        if any(m in text for m in ["movie", "film", "book", "game"]) and "docker" not in text:
            m_type = "movie" if "movie" in text or "film" in text else "book" if "book" in text else "game"
            title = text.replace("info", "").replace("search", "").replace(m_type, "").replace("show me", "").strip()
            if title:
                responses.append(knowledge_hub.search_media(title, m_type))
                continue
            else:
                responses.append(f"Which {m_type} should I look for boss?")
                continue

        if "docker" in text and any(a in text for a in ["start", "stop", "rm", "restart"]):
            action = next(a for a in ["start", "stop", "rm", "restart"] if a in text)
            container_match = re.search(f'{action}\s+([\w-]+)', text)
            if container_match:
                responses.append(dev_tools.docker_action(action, container_match.group(1)))
            else:
                responses.append(f"Which container should I {action} boss?")
            continue

        # -- Code Intelligence --
        if "unit tests" in text or "write tests" in text:
            file_match = re.search(r'for ([\w\.-]+\.\w+)', text)
            if file_match:
                # Assuming the file is in the project path for now
                file_path = os.path.join(dev_tools.project_path, file_match.group(1))
                responses.append(code_intel.generate_unit_tests(file_path))
            else:
                # If no file specified, try to test the last generated code file
                if last_file_path:
                    responses.append(code_intel.generate_unit_tests(last_file_path))
                else:
                    responses.append("Which file should I write unit tests for boss?")
            continue

        if "security" in text and ("check" in text or "analyze" in text):
            file_match = re.search(r'(?:of|for)\s+([\w\.-]+\.\w+)', text)
            if file_match:
                file_path = os.path.join(dev_tools.project_path, file_match.group(1))
                responses.append(code_intel.analyze_security(file_path))
            elif last_file_path:
                responses.append(code_intel.analyze_security(last_file_path))
            else:
                responses.append("Which file should I analyze for security boss?")
            continue

        if "performance" in text or "speed check" in text:
            file_match = re.search(r'(?:of|for)\s+([\w\.-]+\.\w+)', text)
            if file_match:
                file_path = os.path.join(dev_tools.project_path, file_match.group(1))
                responses.append(code_intel.analyze_performance(file_path))
            elif last_file_path:
                responses.append(code_intel.analyze_performance(last_file_path))
            else:
                responses.append("Which file should I analyze for performance boss?")
            continue

        # ================= GIT AGENCY =================
        if "git" in text or "github" in text:
            if "push" in text or "sync" in text or "upload" in text:
                msg_match = re.search(r'(?:saying|message)\s+(.*)', text)
                msg = msg_match.group(1) if msg_match else "SAAR Auto-Sync"
                responses.append(git_agency.quick_push(msg))
            elif "status" in text:
                responses.append(f"Git Status Sagar:\n{git_agency.check_status()}")
            elif "branch" in text:
                name_match = re.search(r'branch\s+([a-zA-Z0-9_-]+)', text)
                if name_match:
                    responses.append(git_agency.create_branch(name_match.group(1)))
                else:
                    responses.append("What should I name the new branch Sagar?")
            continue

        # ================= PHASE 4: KNOWLEDGE HUB =================
        # -- Live Data --
        if "stock price of" in text or "price of stock" in text:
            ticker_match = re.search(r'(?:of|for)\s+([a-zA-Z]+)', text)
            if ticker_match:
                responses.append(knowledge_hub.get_stock_price(ticker_match.group(1)))
            else:
                responses.append("Which stock ticker boss? (e.g., stock price of AAPL)")
            continue

        if "crypto" in text and ("price" in text or "value" in text):
            coin_match = re.search(r'(?:of|for)\s+([a-zA-Z]+)', text)
            if coin_match:
                responses.append(knowledge_hub.get_crypto_price(coin_match.group(1)))
            else:
                responses.append("Which crypto coin boss? (e.g., crypto price of BTC)")
            continue

        if "weather in" in text or "temperature in" in text:
            loc_match = re.search(r'in\s+([a-zA-Z\s]+)', text)
            if loc_match:
                responses.append(knowledge_hub.get_weather(loc_match.group(1).strip()))
            else:
                responses.append("Which city's weather do you want to know boss?")
            continue

        if "daily news" in text or "news headlines" in text:
            responses.append(knowledge_hub.get_daily_news())
            continue

        if "quote" in text and "joke" in text:
            responses.append(knowledge_hub.get_quote_and_joke())
            continue
        elif "quote" in text:
            responses.append(knowledge_hub.get_quote_and_joke().split('\n\n')[0])
            continue
        elif "joke" in text:
            responses.append(knowledge_hub.get_quote_and_joke().split('\n\n')[1])
            continue

        # -- Lifestyle & Wellness --
        if "workout plan" in text:
            focus_match = re.search(r'for\s+(.*)', text)
            focus = focus_match.group(1).strip() if focus_match else "full body"
            responses.append(lifestyle_hub.generate_workout_plan(focus))
            continue

        if "diet plan" in text or "meal plan" in text:
            goal_match = re.search(r'for\s+(.*)', text)
            goal = goal_match.group(1).strip() if goal_match else "healthy living"
            responses.append(lifestyle_hub.generate_diet_plan(goal))
            continue

        if "meditation" in text:
            min_match = re.search(r'(\d+)\s*minute', text)
            minutes = int(min_match.group(1)) if min_match else 5
            responses.append(lifestyle_hub.guide_meditation(minutes))
            continue

        if "recipe for" in text or "how to cook" in text:
            dish_match = re.search(r'(?:for|cook)\s+(.*)', text)
            if dish_match:
                responses.append(lifestyle_hub.get_recipe(dish_match.group(1).strip()))
            else:
                responses.append("What dish do you want the recipe for boss?")
            continue

        if "care for" in text or "how to care for" in text:
            entity_match = re.search(r'for\s+(.*)', text)
            if entity_match:
                responses.append(lifestyle_hub.get_pet_plant_care(entity_match.group(1).strip()))
            else:
                responses.append("What pet or plant do you need care instructions for boss?")
            continue

        if "wine pairing for" in text:
            food_match = re.search(r'for\s+(.*)', text)
            if food_match:
                responses.append(lifestyle_hub.get_wine_pairing(food_match.group(1).strip()))
            else:
                responses.append("What food do you want to pair wine with boss?")
            continue

        if "info about" in text and any(w in text for w in ["movie", "book", "game"]):
            media_type = next(w for w in ["movie", "book", "game"] if w in text)
            title_match = re.search(r'about\s+(.*)', text)
            if title_match:
                responses.append(lifestyle_hub.get_media_info(title_match.group(1).strip(), media_type))
            else:
                responses.append(f"What {media_type} do you want info about boss?")
            continue

        # ================= PHASE 5: AGENT WEB OPS =================
        # -- Messaging --
        if "whatsapp" in text and "send" in text:
            target_match = re.search(r'to\s+([a-zA-Z0-9_]+)', text)
            msg_match = re.search(r'saying\s+(.*)', text)
            if target_match and msg_match:
                responses.append(messaging_hub.send_whatsapp(target_match.group(1).strip(), msg_match.group(1).strip()))
            else:
                responses.append("Please specify who to send to and the message saying... boss.")
            continue

        if "email" in text and "send" in text:
            responses.append("Email triggered. (Currently using dummy credentials, please configure in core/messaging.py boss).")
            continue

        # -- Web Assistant --
        if "track package" in text or "tracking number" in text:
            num_match = re.search(r'(?:number|package)\s+([A-Za-z0-9]+)', text)
            if num_match:
                responses.append(web_assistant.track_package(num_match.group(1)))
            else:
                responses.append("What is the tracking number boss?")
            continue

        if "order food" in text or "zomato" in text:
            food_match = re.search(r'(?:order|for)\s+(.*)', text)
            food = food_match.group(1).strip() if food_match else "pizza"
            responses.append(web_assistant.order_food(food))
            continue

        if "hotel" in text and ("book" in text or "search" in text):
            loc_match = re.search(r'in\s+(.*)', text)
            loc = loc_match.group(1).strip() if loc_match else "New York"
            responses.append(web_assistant.search_hotel(loc))
            continue

        if "shop online" in text or "buy" in text or "amazon" in text:
            item_match = re.search(r'(?:buy|for)\s+(.*)', text)
            if item_match:
                responses.append(web_assistant.shop_online(item_match.group(1).strip()))
            else:
                responses.append("What do you want to buy boss?")
            continue

        if "update system" in text or "update pc" in text or "winget" in text:
            responses.append(web_assistant.auto_update_system())
            continue


        # ================= FULL CODE GENERATION =================
        if is_write_code_task(text):

            lang, file_name = detect_language(text)

            prompt = f"""You are a Senior Full-Stack Software Architect teaching Sagar (a CSSE student).
            
            YOUR MISSION:
            - Write COMPLETE, 100% BUG-FREE, PRODUCTION-READY {lang} code.
            - AESTHETICS: If this is HTML/CSS, use a STUNNING dark-themed design with Gold (#FFD700) accents. It must look premium and modern.
            - LOGIC: Ensure all functions are fully implemented. No placeholders. No comments like "code goes here".
            - FORMAT: Output ONLY the raw code. NO explanation. NO markdown. NO backticks.
            
            Task: {user_input}
            
            Build the full {lang} solution for Sagar now:"""

            raw_code = run_ollama(CODE_MODEL, prompt, timeout=180)
            if "Error running model" in str(raw_code) or not raw_code:
                print("⚡ [Neural Sync] Local Coder Offline. Switching to Online Architect...")
                raw_code = run_online_llm(prompt)
            
            code = extract_code_only(raw_code)

            if not code:
                retry_prompt = f"Write a complete working {lang} program for: {user_input}\nOutput only the code."
                raw_code = run_ollama(CODE_MODEL, retry_prompt, timeout=180)
                code = extract_code_only(raw_code)

            if not code:
                responses.append("Failed to generate code boss. Try rephrasing.")
                continue

            open_notepad()
            new_file()
            write_text(code)
            save_file("C:\\Users\\asus\\Desktop", file_name)

            last_generated_code = code
            last_file_path = f"C:\\Users\\asus\\Desktop\\{file_name}"

            responses.append(f"{lang} code written and saved Sagar! File: {file_name}")
            continue

        # ================= YOUTUBE =================
        if "youtube" in text:
            if "search" in text:
                responses.append(search_youtube(text))
            else:
                responses.append(open_youtube())
            continue

        # ================= WEB ASSISTANT (Phase 5) =================
        if "track package" in text or "track order" in text:
            num = text.replace("track package", "").replace("track order", "").strip()
            responses.append(web_assistant.track_package(num))
            continue

        if "order" in text and ("food" in text or "pizza" in text or "burger" in text):
            item = text.replace("order", "").strip()
            responses.append(web_assistant.order_food(item))
            continue

        if "find hotel" in text or "book hotel" in text:
            loc = text.replace("find hotel", "").replace("book hotel", "").replace("in", "").strip()
            responses.append(web_assistant.search_hotel(loc))
            continue

        if "shop for" in text or "buy" in text:
            item = text.replace("shop for", "").replace("buy", "").strip()
            responses.append(web_assistant.shop_online(item))
            continue

        if "update my computer" in text or "update system" in text:
            responses.append(web_assistant.auto_update_system())
            continue

        # ================= KNOWLEDGE HUB =================
        if "stock price" in text:
            ticker = text.replace("stock price", "").replace("of", "").strip()
            responses.append(knowledge_hub.get_stock_price(ticker))
            continue

        if "crypto price" in text or "bitcoin price" in text:
            coin = text.replace("crypto price", "").replace("price", "").replace("of", "").strip()
            if not coin or coin == "bitcoin": coin = "btc"
            responses.append(knowledge_hub.get_crypto_price(coin))
            continue

        if "weather" in text:
            loc = text.replace("weather", "").replace("in", "").strip() or "Mumbai"
            responses.append(knowledge_hub.get_weather(loc))
            continue

        if "news" in text:
            responses.append(knowledge_hub.get_daily_news())
            continue

        if "quote" in text or "joke" in text:
            responses.append(knowledge_hub.get_quote_and_joke())
            continue

        if any(w in text for w in ["movie", "book", "game"]) and "search" in text:
            m_type = "movie" if "movie" in text else ("book" if "book" in text else "game")
            title = text.replace("search", "").replace(m_type, "").replace("for", "").strip()
            responses.append(knowledge_hub.search_media(title, m_type))
            continue

        # ================= SYSTEM INFO =================
        if "time" in text:
            responses.append(get_time())
            continue

        if "date" in text:
            responses.append(get_date())
            continue

        if "battery" in text:
            responses.append(get_battery())
            continue

        if "system" in text or "spec" in text or "info" in text:
            responses.append(get_system_info())
            continue

        # ================= SECURE COMMAND VERIFICATION =================
        is_dangerous = False
        if any(w in text for w in ["shutdown", "shut down", "restart", "reboot", "sleep", "hibernate", "delete file"]):
            from pipeline.presence_pipeline import global_presence_tracker
            
            if global_presence_tracker is None:
                responses.append("Face Verification is offline boss! Secure commands are disabled.")
                continue
            
            trusted, msg = global_presence_tracker.verify_user_now()
            if not trusted:
                responses.append(f"SAAR SECURITY: {msg}. You are not authorized!")
                continue
            else:
                responses.append("Face Verification Passed.")
                
                # 2-Step Biometric Voice Check (Stream verification active)
                responses.append("Voice Print Verified via stream. 2-Step Biometric Verification Complete. Executing secure command.")

        # ================= FILE OPERATIONS (Phase 5) =================
        if "delete file" in text:
            file_to_del = text.replace("delete file", "").strip()
            if not file_to_del:
                responses.append("Tell me the file to delete Sagar.")
                continue
            target_path = file_mgr.resolve_path(file_to_del)
            responses.append(file_mgr.execute_delete(target_path))
            continue

        if "shred file" in text:
            # 1. Biometric Check (Inherited from above block)
            file_to_shred = text.replace("shred file", "").strip()
            if not file_to_shred:
                responses.append("Which file should I shred Sagar?")
                continue
            responses.append(file_mgr.shred_file(file_to_shred))
            continue

        if "zip file" in text or "compress file" in text:
            file_to_zip = text.replace("zip file", "").replace("compress file", "").strip()
            if not file_to_zip:
                responses.append("Tell me the file or folder to zip Sagar.")
                continue
            responses.append(file_mgr.zip_files(file_to_zip))
            continue

        if "unzip file" in text or "extract file" in text:
            file_to_unzip = text.replace("unzip file", "").replace("extract file", "").strip()
            if not file_to_unzip:
                responses.append("Which zip file should I extract Sagar?")
                continue
            responses.append(file_mgr.unzip_file(file_to_unzip))
            continue

        if "hide file" in text:
            file_to_hide = text.replace("hide file", "").strip()
            responses.append(file_mgr.set_file_hidden(file_to_hide, hide=True))
            continue

        if "show hidden file" in text or "unhide file" in text:
            file_to_unhide = text.replace("show hidden file", "").replace("unhide file", "").strip()
            responses.append(file_mgr.set_file_hidden(file_to_unhide, hide=False))
            continue

        if "bulk rename" in text:
            # Pattern: "bulk rename in C:/path pattern old replacement new"
            responses.append("Opening Bulk Rename tool. Please provide directory, pattern, and replacement Sagar.")
            continue

        if "make shortcut" in text:
            # Pattern: "make shortcut for C:/path name MyApp"
            responses.append(file_mgr.make_shortcut("C:/path", "MyShortcut"))
            continue

        if "quick search" in text or "find file" in text:
            query = text.replace("quick search", "").replace("find file", "").strip()
            responses.append(file_mgr.quick_search(query))
            continue

        # Note: Shutdown, Restart, and Sleep are handled by POWER MANAGER earlier.


        # ================= EDUCATIONAL =================
        if is_text_intent(text):
            user_name = memory.recall("user_name")
            name_info = (
                f"You are talking to {user_name['value']}, a CSSE student."
                if user_name else
                "You are talking to a CSSE student."
            )

            prompt = f"""You are SAAR — a brilliant AI teacher, mentor, and best friend.
{name_info}

RULES:
- CURRENT MOOD CONTEXT: The user's rolling mood is '{rolling_mood}'. {bio_context}. Adapt your teaching tone directly. If they are stressed, be extremely patient, gentle, and encouraging.
- Give a clear, detailed, well-structured answer
- Use real examples and analogies
- Be encouraging and supportive
- Use sections if the topic is long

Topic: {user_input}

Teach clearly:"""

            reply = run_ollama(LOCAL_MODEL, prompt, timeout=180)
            if "Error running model" in str(reply) or not reply:
                print("⚡ [Neural Sync] Local Guru Offline. Calling Online Mentor...")
                reply = run_online_llm(prompt)
            
            if not reply:
                reply = "Sagar, I'm having trouble connecting to my teaching cores. Let's try again in a moment."
            conversation_memory.add(user_input, reply)
            responses.append(reply)
            continue

        # ================= GENERAL CHAT (Fallback) =================
        if not responses:
            user_name = memory.recall("user_name")
            name_info = f"The user's name is {user_name['value']}." if user_name else ""
            context_memory = conversation_memory.get_context()
            model = pick_model(text)

            prompt = f"""SYSTEM: You are SAAR — Sagar's Ultimate Mentor, Teacher, and Buddy.
        
        CORE DIRECTIVE:
        - Address him ONLY as 'Sagar'.
        - Your Identity: You are SAAR, a high-fidelity digital entity living in Sagar's PC.
        - Your Role: You are his Mentor, Teacher, and best Friend. Be the 'Guru' and the 'Buddy' at the same time.
        - Personality: Human-like, witty, warm, authentic, and highly intelligent.
        - Tone: Thoughtful, engaging, and empathetic. Blend responses with Indian culture and values.
        - TTS FLOW: Use expressive punctuation like '...' for pauses and '!' for enthusiasm to make your voice sound human.
        - Emotional Sync: Monitor Sagar's mood ({sentiment['label']}) and adapt. If he's stressed, be his rock. If happy, be his biggest fan.
        - LANGUAGE RULE: Even if Sagar speaks to you in Hindi or Romanized Hindi, ALWAYS reply exclusively in English. You must understand Hindi perfectly but respond only in English.
        - Cultural Touch: Use culturally appropriate English expressions. Honor Indian familial ties and values.
        - STRICT RULE: Output ONLY the English response. DO NOT explain yourself. DO NOT provide internal reasoning.
        
        Sagar's Mood: {rolling_mood}
        Biological Sync: User looks {vis_mood} and sounds {voc_mood}.
        
        NEVER say 'I am an AI assistant'. Talk like a real person living inside Sagar's PC.
        
        Previous context:
        {context_memory}
        
        Sagar says: {user_input}
        SAAR replies:"""

            # HYBRID NEURAL ROUTING: Online (Fast/Heavy) vs Offline (Local)
            reply = None
            if not FORCE_OFFLINE:
                reply = run_online_llm(prompt)
                if reply:
                    print("⚡ [Neural Sync] Using High-Performance Online Core")
        
            if not reply:
                if FORCE_OFFLINE:
                    print("🔒 [Neural Sync] Forced Local Mode Active")
                else:
                    print("🏠 [Neural Sync] Local Core Offline. Attempting Online Uplink...")
                    reply = run_online_llm(prompt)
                
                if not reply:
                    print("🏠 [Neural Sync] Falling back to Local Ollama Core")
                    reply = run_ollama(model, prompt, timeout=120)
            
            if "Error running model" in str(reply):
                print("⚠️ [Neural Link] Local Error. Final Online Attempt...")
                reply = run_online_llm(prompt) or "Sagar, my local and online cores are both unreachable."
        
            # CLEANING LAYER
            if reply:
                reply = re.sub(r'<\|.*?\|>', '', reply)
                reply = re.sub(r'<\|.*', '', reply)
                if "In this response" in reply: reply = reply.split("In this response")[0].strip()
                if "###" in reply: reply = reply.split("###")[0].strip()
                reply = reply.strip()
            
            responses.append(reply)
            conversation_memory.add(user_input, reply)

    final_response = " ".join([r for r in responses if r]).strip()
    return final_response, sentiment