# core/messaging.py — SAAR Neural Messaging Hub (Jarvis-Level)
# ============================================================
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os
import time
import re

try:
    import pywhatkit
    WHATSAPP_AVAILABLE = True
except Exception:
    WHATSAPP_AVAILABLE = False

# ─────────────────────────────────────────────────────────────
# CONTACTS FILE
# ─────────────────────────────────────────────────────────────
CONTACTS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "contacts.json"
)

# ─────────────────────────────────────────────────────────────
# CONTACT ALIASES  —  spoken word → stored key
# Add as many as you like. All lowercase.
# ─────────────────────────────────────────────────────────────
CONTACT_ALIASES = {
    # Mom variations
    "mom": "mom",
    "mum": "mom",
    "mummy": "mom",
    "mother": "mom",
    "mama": "mom",
    "maa": "mom",
    "ma": "mom",
    # Dad variations
    "dad": "dad",
    "papa": "dad",
    "father": "dad",
    "paa": "dad",
    # Self
    "myself": "sagar",
    "me": "sagar",
    "my number": "sagar",
    # Add more here as needed
}

# ─────────────────────────────────────────────────────────────
# NOISE WORDS — stripped from the START of message content
# ─────────────────────────────────────────────────────────────
MSG_NOISE = {"saying", "say", "that", "to", "and", "tell", "tells"}

# ─────────────────────────────────────────────────────────────
# EMAIL CONFIG FILE
# ─────────────────────────────────────────────────────────────
EMAIL_CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "email_config.json"
)

def _load_email_config():
    if os.path.exists(EMAIL_CONFIG_FILE):
        with open(EMAIL_CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"email": "", "app_password": "", "name": "Sagar"}

def _save_email_config(cfg: dict):
    with open(EMAIL_CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=4)

class MessagingHub:
    def __init__(self):
        self.contacts = self._load_contacts()
        cfg = _load_email_config()
        self.email_address = cfg.get("email", "")
        self.email_password = cfg.get("app_password", "")
        self.email_name    = cfg.get("name", "Sagar")
        self.use_desktop_app = True   # True = native WhatsApp app, False = browser

    def reload_email_config(self):
        cfg = _load_email_config()
        self.email_address = cfg.get("email", "")
        self.email_password = cfg.get("app_password", "")
        self.email_name    = cfg.get("name", "Sagar")

    # ── Contact Management ─────────────────────────────────
    def _load_contacts(self):
        if not os.path.exists(CONTACTS_FILE):
            defaults = {"mom": "+911234567890", "sagar": "+918208389305"}
            with open(CONTACTS_FILE, "w") as f:
                json.dump(defaults, f, indent=4)
            return defaults
        with open(CONTACTS_FILE, "r") as f:
            return json.load(f)

    def _resolve_name(self, raw: str) -> str:
        """Resolve spoken name (with aliases) to a contacts.json key."""
        raw = raw.lower().strip()
        # 1. Direct alias lookup
        if raw in CONTACT_ALIASES:
            return CONTACT_ALIASES[raw]
        # 2. Direct contact key lookup
        if raw in self.contacts:
            return raw
        # 3. Fuzzy: check if any contact key is a substring of raw or vice‑versa
        for key in self.contacts:
            if key in raw or raw in key:
                return key
        return raw   # return as‑is; caller decides what to do

    def get_contact_number(self, name: str):
        resolved = self._resolve_name(name)
        return self.contacts.get(resolved), resolved

    def add_contact(self, name: str, number: str):
        name = name.lower().strip()
        if not number.startswith("+"):
            number = "+91" + number.lstrip("0")
        self.contacts[name] = number
        try:
            with open(CONTACTS_FILE, "w") as f:
                json.dump(self.contacts, f, indent=4)
            return f"✅ {name.capitalize()} saved to Neural Contacts Sagar! Number: {number}"
        except Exception as e:
            return f"Contact save error: {e}"

    def list_contacts(self):
        if not self.contacts:
            return "Your contact list is empty Sagar."
        entries = [f"{n.capitalize()} ({num})" for n, num in self.contacts.items()]
        return "Your Neural Contacts Sagar: " + ", ".join(entries)

    def delete_contact(self, name: str):
        resolved = self._resolve_name(name)
        if resolved in self.contacts:
            del self.contacts[resolved]
            with open(CONTACTS_FILE, "w") as f:
                json.dump(self.contacts, f, indent=4)
            return f"🗑️ {resolved.capitalize()} removed from Neural Contacts Sagar."
        return f"Contact '{name}' not found Sagar."

    # ── WhatsApp Text ──────────────────────────────────────
    def send_whatsapp(self, name: str, message: str):
        number, resolved = self.get_contact_number(name)
        if not number:
            return (f"❌ I couldn't find '{name}' in your Neural Contacts Sagar. "
                    f"Say 'Add contact {name} <number>' to save them!")

        print(f"📱 [WhatsApp] Targeting → {resolved.capitalize()} ({number})")
        print(f"📝 [WhatsApp] Message   → {message}")

        try:
            if self.use_desktop_app:
                return self._send_via_desktop_app(resolved, number, message)
            else:
                return self._send_via_web(number, message, resolved)
        except Exception as e:
            print(f"⚠️  [WhatsApp] Primary path failed: {e}. Trying web fallback...")
            return self._send_via_web(number, message, resolved)

    def _send_via_desktop_app(self, name: str, number: str, message: str):
        """Open WhatsApp Desktop via URI, auto‑fill message, press Enter."""
        import webbrowser
        from urllib.parse import quote

        clean_num = number.replace("+", "").replace(" ", "")
        link = f"whatsapp://send?phone={clean_num}&text={quote(message)}"
        print(f"🚀 [WhatsApp] Launching Desktop App → {link}")
        webbrowser.open(link)

        # Wait for app to open and load the chat
        print("⏳ [WhatsApp] Synchronizing neural link — please keep WhatsApp in focus...")
        time.sleep(7)

        import pyautogui
        # Click the center of the screen to make sure app is focused
        screen_w, screen_h = pyautogui.size()
        pyautogui.click(screen_w // 2, screen_h // 2)
        time.sleep(0.5)

        # Send the message
        pyautogui.press("enter")
        time.sleep(0.3)

        print(f"✅ [WhatsApp] Message sent to {name.capitalize()}!")
        return f"✅ WhatsApp message delivered to {name.capitalize()} Sagar!"

    def _send_via_web(self, number: str, message: str, name: str):
        """Use pywhatkit (browser) as the fallback."""
        from urllib.parse import quote
        import webbrowser

        try:
            if WHATSAPP_AVAILABLE:
                print(f"🌐 [WhatsApp] Using Web route for {name}...")
                pywhatkit.sendwhatmsg_instantly(
                    number, message, wait_time=15, tab_close=True, close_time=3
                )
                return f"✅ WhatsApp Web message sent to {name.capitalize()} Sagar!"
        except Exception as e:
            print(f"⚠️  [WhatsApp] pywhatkit also failed: {e}. Opening wa.me link...")

        # Final fallback — manual click
        clean_num = number.replace("+", "").replace(" ", "")
        link = f"https://wa.me/{clean_num}?text={quote(message)}"
        webbrowser.open(link)
        return (f"🔗 WhatsApp Web opened for {name.capitalize()} Sagar. "
                "Message is pre‑filled — just press Enter to send!")

    # ── WhatsApp Media ──────────────────────────────────────
    def send_whatsapp_media(self, name: str, path: str, caption: str = ""):
        number, resolved = self.get_contact_number(name)
        if not number:
            return f"❌ Contact '{name}' not found Sagar."
        if not os.path.exists(path):
            return f"❌ File not found at path: {path}"

        try:
            print(f"📎 [WhatsApp] Sending media to {resolved} → {path}")
            pywhatkit.sendwhats_image(number, path, caption, wait_time=20, tab_close=True)
            return f"✅ Media sent to {resolved.capitalize()} Sagar!"
        except Exception as e:
            return f"⚠️ Media send error: {e}"

    # ── Email ───────────────────────────────────────────────
    def configure_email(self, email: str, app_password: str):
        """Save email credentials to config file."""
        cfg = {"email": email.strip(), "app_password": app_password.strip(), "name": self.email_name}
        _save_email_config(cfg)
        self.email_address = cfg["email"]
        self.email_password = cfg["app_password"]
        return f"✅ Email configured! SAAR will now send from {email} Sagar."

    def send_email(self, to_email: str, subject: str, body: str):
        """Send an email via Gmail SMTP."""
        self.reload_email_config()
        if not self.email_address:
            return ("❌ Email not configured Sagar. Say: "
                    "'Set my email to yourname@gmail.com password yourapppassword'")
        try:
            msg = MIMEMultipart()
            msg["From"]    = f"{self.email_name} <{self.email_address}>"
            msg["To"]      = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            print(f"📧 [Email] Connecting to Gmail SMTP...")
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(self.email_address, self.email_password)
            server.sendmail(self.email_address, to_email, msg.as_string())
            server.quit()
            print(f"✅ [Email] Sent to {to_email}")
            return f"✅ Email sent to {to_email} successfully Sagar!"
        except smtplib.SMTPAuthenticationError:
            return ("❌ Gmail authentication failed Sagar. "
                    "Make sure you're using a Gmail App Password, not your normal password. "
                    "Go to myaccount.google.com → Security → App Passwords to create one.")
        except Exception as e:
            return f"❌ Email error: {e}"

    def send_email_to_contact(self, name: str, subject: str, body: str):
        """Look up a contact's email and send to them."""
        # contacts.json can optionally store email as value
        # Expected format: {"sneha": "+919209845157"} or {"sneha": {"phone": "..", "email": "..@..."}}
        contact_data = self.contacts.get(self._resolve_name(name))
        if isinstance(contact_data, dict):
            email = contact_data.get("email")
            if email:
                return self.send_email(email, subject, body)
            return f"❌ No email saved for {name} Sagar. Add it with 'Add contact {name} email x@y.com'"
        # Fallback: try parsing as email if stored directly
        if contact_data and "@" in str(contact_data):
            return self.send_email(contact_data, subject, body)
        return f"❌ No email address found for {name} Sagar."

    def read_emails(self, count: int = 3):
        """Read the latest unseen emails using IMAP."""
        import imaplib
        import email
        from email.header import decode_header
        
        self.reload_email_config()
        if not self.email_address:
            return "❌ Email not configured Sagar. Cannot read emails."
            
        try:
            print("📧 [Email] Connecting to IMAP to fetch emails...")
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(self.email_address, self.email_password)
            mail.select("inbox")
            
            status, messages = mail.search(None, "UNSEEN")
            if status != "OK" or not messages[0]:
                return "You have no new unread emails Sagar."
                
            email_ids = messages[0].split()
            latest_ids = email_ids[-count:]
            
            output = []
            for e_id in latest_ids:
                res, msg_data = mail.fetch(e_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8")
                            
                        from_ = msg.get("From")
                        from_name = from_.split('<')[0].strip() if '<' in from_ else from_
                        
                        output.append(f"From {from_name}, subject: {subject}")
            
            mail.close()
            mail.logout()
            
            if not output:
                return "I couldn't fetch the latest emails properly."
                
            return f"You have {len(output)} new emails. " + ". ".join(output)
            
        except Exception as e:
            return f"❌ Failed to read emails: {str(e)}"


# ─────────────────────────────────────────────────────────────
# GLOBAL INSTANCE
# ─────────────────────────────────────────────────────────────
messaging_hub = MessagingHub()


# ─────────────────────────────────────────────────────────────
# JARVIS‑LEVEL VOICE COMMAND PARSER
# ─────────────────────────────────────────────────────────────
def parse_whatsapp_command(text: str) -> str:
    """
    Parses any natural‑language WhatsApp command.

    Supported patterns (all voice‑friendly):
      • "message Sneha saying hello"
      • "send message to mom how are you"
      • "whatsapp Sneha I will be late"
      • "send msg to mum saying I'm coming home"
      • "tell Sneha she is looking good"
      • "send image /path/to/photo.jpg to Sneha"
      • "click send button"
    """
    query = text.lower().strip()
    # Remove special characters except basic punctuation
    query = re.sub(r"[^\w\s'.,!?]", "", query)

    print(f"🧠 [WhatsApp Parser] Processing: '{query}'")

    # ── 0. Manual send click ────────────────────────────────
    if "click" in query and ("send" in query or "button" in query):
        import pyautogui
        pyautogui.press("enter")
        return "✅ Send button activated Sagar!"

    # ── 1. Media detection ─────────────────────────────────
    is_media = any(w in query for w in ["image", "photo", "picture", "file", "document", "pdf"])

    # ── 2. Build a merged name → key lookup map ────────────
    # Includes both aliases AND actual contact names
    name_map = dict(CONTACT_ALIASES)          # alias → stored key
    for key in messaging_hub.contacts:
        name_map[key] = key                   # stored key → itself

    # ── 3. Find the target contact name in the query ───────
    target_key   = None
    target_index = -1
    words        = query.split()

    for i, word in enumerate(words):
        clean_word = re.sub(r"[^\w]", "", word)
        if clean_word in name_map:
            target_key   = name_map[clean_word]
            target_index = i
            print(f"🎯 [WhatsApp Parser] Contact match → '{clean_word}' → '{target_key}'")
            break

    if target_key is None:
        # Build a friendly list of recognized names
        recognized = sorted(set(list(name_map.keys())))
        return (
            f"❌ I couldn't find any of your contacts in that command Sagar. "
            f"Recognized names: {', '.join(recognized)}. "
            f"Or say 'Add contact <name> <number>' to save a new one!"
        )

    # ── 4. Extract message content ─────────────────────────
    if is_media:
        # Pattern: "send image <path> to <name>"
        match = re.search(
            r"(?:image|photo|picture|file|document|pdf)\s+(.+?)\s+(?:to|for|at)\s+\w+",
            query
        )
        if match:
            path = match.group(1).strip()
            caption_match = re.search(r"caption\s+(.+)$", query)
            caption = caption_match.group(1) if caption_match else ""
            return messaging_hub.send_whatsapp_media(target_key, path, caption)

        # Simpler: everything after media keyword until "to <name>" is the path
        return f"❌ Please specify the file path Sagar. Example: 'send image C:/photo.jpg to Sneha'"

    # ── 5. Extract text message (everything AFTER the name) ─
    after_name = words[target_index + 1:]

    # Strip leading noise words
    while after_name and re.sub(r"[^\w]", "", after_name[0]) in MSG_NOISE:
        after_name = after_name[1:]

    final_message = " ".join(after_name).strip()

    if not final_message:
        return (
            f"❌ What should I say to {target_key.capitalize()} Sagar? "
            f"Try: 'message {target_key.capitalize()} hello, I'll be there soon'"
        )

    print(f"📤 [WhatsApp Parser] Sending to {target_key}: '{final_message}'")
    return messaging_hub.send_whatsapp(target_key, final_message)


# ─────────────────────────────────────────────────────────────
# EMAIL PARSER
# ─────────────────────────────────────────────────────────────
def parse_email_command(text: str) -> str:
    text = text.lower()
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    if not email_match:
        return "I need a valid email address boss."

    to_email = email_match.group(0)
    subject  = "SAAR Priority Message"
    body     = "No message body provided."

    if "subject" in text:
        subject = text.split("subject", 1)[1].split("body", 1)[0].strip()
    if "body" in text:
        body = text.split("body", 1)[1].strip()

    return messaging_hub.send_email(to_email, subject, body)