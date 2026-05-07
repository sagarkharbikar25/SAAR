import customtkinter as ctk
from threading import Thread
import time

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class AssistantUI(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Personal AI Assistant")
        self.geometry("520x620")
        self.resizable(False, False)

        # Header
        self.header = ctk.CTkLabel(
            self,
            text="Personal AI Assistant",
            font=("Segoe UI", 22, "bold")
        )
        self.header.pack(pady=20)

        # Status
        self.status = ctk.CTkLabel(
            self,
            text="● Idle",
            text_color="gray",
            font=("Segoe UI", 14)
        )
        self.status.pack(pady=5)

        # Chat box
        self.chat_box = ctk.CTkTextbox(
            self,
            width=460,
            height=350,
            corner_radius=15
        )
        self.chat_box.pack(pady=20)
        self.chat_box.insert("end", "🤖 Assistant ready...\n")
        self.chat_box.configure(state="disabled")

        # Buttons frame
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(pady=10)

        self.start_btn = ctk.CTkButton(
            self.btn_frame,
            text="Start",
            width=140,
            command=self.start_assistant
        )
        self.start_btn.grid(row=0, column=0, padx=15)

        self.stop_btn = ctk.CTkButton(
            self.btn_frame,
            text="Stop",
            width=140,
            fg_color="red",
            hover_color="#aa0000",
            command=self.stop_assistant
        )
        self.stop_btn.grid(row=0, column=1, padx=15)

    def start_assistant(self):
        self.status.configure(text="● Listening", text_color="green")
        self.append_text("🎤 Listening...\n")
        Thread(target=self.fake_response).start()

    def stop_assistant(self):
        self.status.configure(text="● Stopped", text_color="red")
        self.append_text("⛔ Assistant stopped\n")

    def append_text(self, text):
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", text)
        self.chat_box.see("end")
        self.chat_box.configure(state="disabled")

    def fake_response(self):
        time.sleep(2)
        self.append_text("🤖 Thinking...\n")
        time.sleep(2)
        self.append_text("🤖 Hello! I am ready to assist you.\n")
        self.status.configure(text="● Idle", text_color="gray")

if __name__ == "__main__":
    app = AssistantUI()
    app.mainloop()
