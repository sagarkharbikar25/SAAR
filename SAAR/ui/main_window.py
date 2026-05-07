# pyrefly: ignore [missing-import]
import customtkinter as ctk
import tkinter as tk
import threading
import sys
import os
import queue
import time
import math
import pickle
import psutil
import socket
from core.state import AssistantState
from ui.theme import THEME
from ui.cyber_widgets import CyberFrame, SegmentedProgressBar, HeartbeatCanvas, WaveformBar, DotGridCanvas, OrbitalBackground, HUDModuleChip
from core.brain import ask_brain
from voice.tts import speak

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

AVATAR_DIR = get_resource_path("avatar")
STABLE_FACE = get_resource_path("avatar/face view.jpeg")

class SaarVisualizer(ctk.CTkFrame):
    def __init__(self, master, state_manager):
        super().__init__(master, fg_color="transparent")
        self.state_manager = state_manager
        
        from ui.theme import THEME
        self.colors = THEME
        
        # We match the canvas background to the panel color to make the orb "float"
        self.canvas = ctk.CTkCanvas(self, width=500, height=450, bg=self.colors["frame_bg"], highlightthickness=0)
        self.canvas.pack()
        
        # Removed static oval to allow orb to float on the panel background
        
        self.arcs = []
        self.create_singularity()
        self.after(50, self.update_visualizer)

    def create_singularity(self):
        # Create a Cosmic Singularity (Vortex)
        cx, cy = 250, 225
        for i in range(12):
            r = 30 + i*15
            extent = 60 + i*10
            start = i*30
            arc_id = self.canvas.create_arc(cx-r, cy-r, cx+r, cy+r, start=start, extent=extent, outline=self.colors["orb_idle"], style="arc", width=2)
            self.arcs.append({"id": arc_id, "radius": r, "start": start, "speed": 2 + i*0.5})
            
        self.center_glow = self.canvas.create_oval(240, 215, 260, 235, fill=self.colors["orb_idle"], outline="")

    def update_visualizer(self):
        state = self.state_manager.get()
        color = self.colors["orb_idle"]
        if state == "listening": color = self.colors["orb_listening"]
        elif state == "thinking": color = self.colors["orb_thinking"]
        elif state == "speaking": color = self.colors["orb_speaking"]

        cx, cy = 250, 225
        t = time.time()
        
        for i, arc in enumerate(self.arcs):
            # Rotate arcs at different speeds
            new_start = (arc["start"] + t * arc["speed"] * (20 if state=="speaking" else 5)) % 360
            pulse = math.sin(t * 3 + i) * (5 if state=="idle" else 15)
            r = arc["radius"] + pulse
            
            self.canvas.itemconfig(arc["id"], start=new_start, outline=color)
            self.canvas.coords(arc["id"], cx-r, cy-r, cx+r, cy+r)
            
        glow_r = 10 + math.sin(t * 5) * (2 if state=="idle" else 8)
        self.canvas.coords(self.center_glow, cx-glow_r, cy-glow_r, cx+glow_r, cy+glow_r)
        self.canvas.itemconfig(self.center_glow, fill=color)

        self.after(50, self.update_visualizer)

class AsyncRedirector:
    def __init__(self, textbox, queue):
        self.textbox = textbox
        self.queue = queue

    def write(self, string):
        self.queue.put(string)

    def flush(self):
        pass

class SAAR_UI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("SAAR – Elite Neural Interface")
        self.state_manager = AssistantState()
        self.colors = THEME
        self.log_queue = queue.Queue()
        self.start_time = time.time()
        
        self.title("SAAR - Neural Dashboard")
        self.geometry("1100x700")
        self.configure(fg_color=self.colors["bg"])
        
        # 1. Global Dot Grid Background
        self.bg_grid = DotGridCanvas(self, bg=self.colors["bg"])
        self.bg_grid.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # ==========================================
        # TOP HEADER
        # ==========================================
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill=ctk.X, pady=(15, 5), padx=30)
        
        # Header Bottom Border (Cyan Gradient transparent->cyan->transparent)
        self.header_border = tk.Canvas(self, height=1, bg=self.colors["bg"], highlightthickness=0)
        self.header_border.place(relx=0.1, rely=0.08, relwidth=0.8)
        self.header_border.create_line(0, 0, 1000, 0, fill=self.colors["secondary"], width=1, stipple="gray50")

        self.logo_label = ctk.CTkLabel(self.header_frame, text="SAAR", font=("Orbitron", 32, "bold"), text_color=self.colors["title"])
        self.logo_label.pack(side="left")
        
        self.sub_logo = ctk.CTkLabel(self.header_frame, text="| NEURAL DASHBOARD", font=("Orbitron", 14), text_color=self.colors["subtitle"])
        self.sub_logo.pack(side="left", padx=15, pady=(5, 0))

        self.top_right_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.top_right_frame.pack(side="right")
        
        self.time_label = ctk.CTkLabel(self.top_right_frame, text="00:00:00", font=("Consolas", 14, "bold"), text_color=self.colors["primary"])
        self.time_label.pack(side="right", padx=10)
        
        # Blinking Green Dot
        self.status_dot = ctk.CTkLabel(self.top_right_frame, text="●", font=("Consolas", 14), text_color=self.colors["primary"])
        self.status_dot.pack(side="right", padx=(5, 0))
        
        self.sys_status_top = ctk.CTkLabel(self.top_right_frame, text="[ ONLINE ]", font=("Exo 2 Light", 14), text_color=self.colors["primary"])
        self.sys_status_top.pack(side="right", padx=(5, 10))

        # ==========================================
        # MAIN CONTAINER (3 COLUMNS)
        # ==========================================
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill=ctk.BOTH, expand=True, padx=20, pady=5)

        self.main_container.grid_columnconfigure(0, weight=0, minsize=240)  
        self.main_container.grid_columnconfigure(1, weight=1)               
        self.main_container.grid_columnconfigure(2, weight=0, minsize=380)  
        self.main_container.grid_rowconfigure(0, weight=1)

        # ------------------------------------------
        # 1. LEFT SIDEBAR (SYSTEM & QUICK ACTIONS)
        # ------------------------------------------
        self.sidebar_left = CyberFrame(self.main_container, border_color=self.colors["border_normal"], bg_color=self.colors["frame_bg"])
        self.sidebar_left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.sidebar_left.grid_propagate(False)
        self.init_system_metrics()

        # ------------------------------------------
        # 2. CENTER HERO SECTION (ORB + COMMANDS)
        # ------------------------------------------
        self.center_panel = CyberFrame(self.main_container, border_color=self.colors["border_normal"], bg_color=self.colors["glass_bg"])
        self.center_panel.grid(row=0, column=1, sticky="nsew", padx=10)
        
        # 2. Orbital Background (Radial Gradient)
        self.center_bg = OrbitalBackground(self.center_panel.content, center_color=self.colors["bg"], edge_color="#000F14")
        self.center_bg.place(relx=0, rely=0, relwidth=1, relheight=1)

        # 3. Dot Grid for Center (24px spacing)
        self.center_grid = DotGridCanvas(self.center_panel.content, bg=self.colors["glass_bg"], spacing=24)
        self.center_grid.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Scanline Canvas Overlay (Created after background to sit on top)
        self.scanline_canvas = tk.Canvas(self.center_panel.content, bg=self.colors["glass_bg"], highlightthickness=0, height=2)
        self.scanline_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.visualizer = SaarVisualizer(self.center_panel.content, self.state_manager)
        self.visualizer.pack(pady=(20, 0))
        
        self.status_label = ctk.CTkLabel(self.center_panel.content, text="[ SAAR READY : STANDBY ]", font=("Share Tech Mono", 16, "bold"), text_color=self.colors["secondary"])
        self.status_label.pack(pady=(0, 10))

        # MODE Tabs
        self.tabs_frame = ctk.CTkFrame(self.center_panel.content, fg_color="transparent")
        self.tabs_frame.pack(pady=(0, 0))
        modes = ["COMMAND", "AUTOMATION", "VISION", "ANALYTICS"]
        for i, mode in enumerate(modes):
            is_active = (i == 0) # Command is default
            fg = self.colors["primary"] if is_active else "transparent"
            txt = "#000" if is_active else self.colors["primary"]
            
            m_btn = ctk.CTkButton(self.tabs_frame, text=mode, width=90, height=26, corner_radius=0,
                                  fg_color=fg, text_color=txt,
                                  border_color=self.colors["primary"], border_width=1,
                                  font=("Share Tech Mono", 10, "bold" if is_active else "normal"))
            m_btn.pack(side="left", padx=5)

        # Waveform Bar (Mic Feedback) - 40px height, NO gap below tabs
        self.waveform = WaveformBar(self.center_panel.content, color=self.colors["secondary"], bg_color=self.colors["frame_bg"], height=40)
        self.waveform.pack(fill=ctk.X, padx=150, pady=(0, 10))
        
        # Command Area Container - Pack bottom to stay flush with vitals
        self.cmd_area = ctk.CTkFrame(self.center_panel.content, fg_color="transparent")
        self.cmd_area.pack(side="bottom", fill=ctk.X, pady=(0, 0), padx=20)
        
        self.chips_frame = ctk.CTkFrame(self.cmd_area, fg_color="transparent")
        self.chips_frame.pack(fill=ctk.X, pady=(0, 10))
        
        chips = ["Open Chrome", "Check Weather", "Play Music", "Open VS Code"]
        for chip in chips:
            c_btn = ctk.CTkButton(self.chips_frame, text=f"[{chip}]", width=10, height=24, corner_radius=12, 
                                  fg_color="transparent", text_color=self.colors["primary"], 
                                  border_color=self.colors["border_active"], border_width=1,
                                  hover_color=self.colors["border_normal"], font=("Consolas", 11),
                                  command=lambda t=chip: self.send_text_command(t))
            c_btn.pack(side="left", padx=5)
        
        self.cmd_bar = ctk.CTkFrame(self.cmd_area, fg_color="transparent")
        self.cmd_bar.pack(fill=ctk.X, pady=(0, 0))
        
        self.query_entry = ctk.CTkEntry(self.cmd_bar, placeholder_text="Enter command or speak...", height=50, font=("Share Tech Mono", 16), corner_radius=0, border_width=1, fg_color="#000", border_color=self.colors["secondary"])
        self.query_entry.pack(side="left", fill=ctk.X, expand=True, padx=(0, 10))
        self.query_entry.bind("<Return>", lambda e: self.send_text_command())
        
        self.mic_btn = ctk.CTkButton(self.cmd_bar, text="🎤", width=50, height=50, corner_radius=25, fg_color="#111", text_color=self.colors["secondary"], border_color=self.colors["secondary"], border_width=1, font=("Segoe UI Emoji", 20), command=self.toggle_mic_gui)
        self.mic_btn.pack(side="left", padx=(0, 10))
        
        self.send_btn = ctk.CTkButton(self.cmd_bar, text="▶ EXECUTE", width=120, height=50, corner_radius=0, fg_color="transparent", text_color=self.colors["primary"], border_color=self.colors["primary"], border_width=1, hover_color=self.colors["border_normal"], font=("Orbitron", 14, "bold"), command=self.send_text_command)
        self.send_btn.pack(side="right")
        
        # SYSTEM VITALS MINI BAR (Center Bottom, Flush)
        self.v_wrap = ctk.CTkFrame(self.center_panel.content, fg_color="transparent")
        self.v_wrap.pack(side="bottom", fill=ctk.X)
        
        # Thin top border
        ctk.CTkFrame(self.v_wrap, height=1, fg_color="#00FF88").pack(fill=ctk.X)
        
        self.vitals_bar = ctk.CTkLabel(self.v_wrap, text="CPU: 0% | RAM: 0% | NET: 12ms | DISK: 0.0MB/s", 
                                        font=("Consolas", 10), text_color="#00FF88")
        self.vitals_bar.pack(pady=6)

        # ------------------------------------------
        # 3. RIGHT SIDEBAR (NEURAL FEED & WIDGETS)
        # ------------------------------------------
        self.sidebar_right = CyberFrame(self.main_container, border_color=self.colors["border_normal"], bg_color=self.colors["frame_bg"])
        self.sidebar_right.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
        self.sidebar_right.grid_propagate(False)
        
        ctk.CTkLabel(self.sidebar_right.content, text="NEURAL FEED_LOG", font=("Orbitron", 16, "bold"), text_color=self.colors["primary"]).pack(pady=(10, 5))
        
        self.chat_container = ctk.CTkTextbox(self.sidebar_right.content, fg_color="transparent", font=("Share Tech Mono", 12), border_width=0, text_color=self.colors["text"])
        self.chat_container.pack(fill=ctk.BOTH, expand=True, padx=5, pady=(0, 5))
        self.chat_container.configure(state="disabled")
        
        # Feed Tags
        self.chat_container.tag_config("sys", foreground=self.colors["primary"])
        self.chat_container.tag_config("saar", foreground=self.colors["secondary"])
        self.chat_container.tag_config("warn", foreground=self.colors["accent_amber"])
        self.chat_container.tag_config("err", foreground=self.colors["critical"])
        self.chat_container.tag_config("user", foreground="#FFFFFF")
        
        self.init_right_widgets()

        # ==========================================
        # FOOTER BAR
        # ==========================================
        self.footer = ctk.CTkFrame(self, height=28, fg_color=self.colors["frame_bg"], corner_radius=0)
        self.footer.pack(fill=ctk.X, side="bottom")
        
        self.cpu_temp = ctk.CTkLabel(self.footer, text="TEMP: 45°C", font=("Exo 2 Light", 10), text_color=self.colors["secondary"])
        self.cpu_temp.pack(side="left", padx=15)
        
        self.battery_lbl = ctk.CTkLabel(self.footer, text="PWR: AC", font=("Exo 2 Light", 10), text_color=self.colors["secondary"])
        self.battery_lbl.pack(side="left", padx=15)
        
        self.mod_lbl = ctk.CTkLabel(self.footer, text="108 MODULES ACTIVE", font=("Exo 2 Light", 10, "bold"), text_color=self.colors["accent_amber"])
        self.mod_lbl.pack(expand=True)
        
        self.conn_dot = ctk.CTkLabel(self.footer, text="●", font=("Consolas", 14), text_color=self.colors["primary"])
        self.conn_dot.pack(side="right", padx=(5, 15))
        
        self.date_lbl = ctk.CTkLabel(self.footer, text="DD-MM-YYYY", font=("Exo 2 Light", 10), text_color=self.colors["secondary"])
        self.date_lbl.pack(side="right", padx=15)

        # Initial Boot Sequence
        self._typing_insert(">>> INITIALIZING NEURAL CORE...\n", "sys")
        self._typing_insert(">>> BIOMETRIC SENSORS ONLINE...\n", "sys")
        self._typing_insert(">>> AWAITING ROOT COMMAND...\n\n", "sys")
        
        # START ANIMATIONS & SYSTEMS
        self.scan_y = 0
        self.scan_dir = 1
        self.bracket_anim_state = 0
        self.after(50, self.animate_scanline)
        self.after(100, self.animate_brackets)
        self.after(1000, self.start_services)
        self.update_clock()
        self.process_logs()
        self.update_metrics_loop()
        self.update_status_loop()
        self._add_dummy_logs()

    def init_system_metrics(self):
        c = self.sidebar_left.content
        
        # 1. Presence Toggle (Neural Eye)
        from pipeline.presence_pipeline import PRESENCE_ENABLED
        eye_frame = ctk.CTkFrame(c, fg_color="transparent")
        eye_frame.pack(fill=ctk.X, pady=(5, 15))
        
        self.eye_toggle = ctk.CTkSwitch(eye_frame, text="NEURAL EYE", command=self.toggle_eye, 
                                        progress_color=self.colors["primary"], font=("Share Tech Mono", 12))
        if PRESENCE_ENABLED: self.eye_toggle.select()
        else: self.eye_toggle.deselect()
        self.eye_toggle.pack(side="left", padx=10)

        # 2. System Metrics (Segmented)
        ctk.CTkLabel(c, text="⚙ SYS_PROC_UNIT", font=("Share Tech Mono", 12), text_color=self.colors["secondary"]).pack(anchor="w", padx=10)
        self.cpu_bar = SegmentedProgressBar(c, active_color=self.colors["primary"], inactive_color=self.colors["border_normal"])
        self.cpu_bar.pack(fill=ctk.X, padx=10, pady=(2, 10))
        
        self.ram_bar = SegmentedProgressBar(c, active_color=self.colors["secondary"], inactive_color=self.colors["border_normal"])
        self.ram_bar.pack(fill=ctk.X, padx=10, pady=(2, 10))
        
        # Biometric Heartbeat
        self.bio_canvas = HeartbeatCanvas(c, color=self.colors["primary"], height=40)
        self.bio_canvas.pack(fill=ctk.X, padx=10, pady=(2, 10))
        
        # 3. Voice Tuning Sliders (Green Polish)
        s_style = {"progress_color": self.colors["slider_fill"], "button_color": self.colors["slider_fill"], "fg_color": self.colors["slider_empty"]}
        
        self.pitch_lbl = ctk.CTkLabel(c, text="PITCH: 0Hz", font=("Share Tech Mono", 10), text_color=self.colors["secondary"])
        self.pitch_lbl.pack(anchor="w", padx=10)
        self.pitch_slider = ctk.CTkSlider(c, from_=-10, to=10, height=15, command=self.update_pitch, **s_style)
        self.pitch_slider.set(0)
        self.pitch_slider.pack(fill=ctk.X, padx=15, pady=(0, 10))

        self.speed_lbl = ctk.CTkLabel(c, text="SPEED: +8%", font=("Share Tech Mono", 10), text_color=self.colors["secondary"])
        self.speed_lbl.pack(anchor="w", padx=10)
        self.speed_slider = ctk.CTkSlider(c, from_=0, to=20, height=15, command=self.update_speed, **s_style)
        self.speed_slider.set(8)
        self.speed_slider.pack(fill=ctk.X, padx=15, pady=(0, 15))

        # 4. HUD MODULE CHIPS (3x4 Grid)
        ctk.CTkLabel(c, text="HUD MODULES", font=("Orbitron", 12), text_color=self.colors["secondary"]).pack(pady=5)
        mod_grid = ctk.CTkFrame(c, fg_color="transparent")
        mod_grid.pack(fill=ctk.X, padx=5)
        
        modules = ["VOICE", "VISION", "AUTO", "MEDIA", "SYS", "NET", "WEATHER", "CHROME", "VSCODE", "TASKS", "AI", "BIO"]
        for i, mod in enumerate(modules):
            row, col = divmod(i, 3)
            is_active = mod in ["VOICE", "SYS", "AI", "BIO"]
            chip = HUDModuleChip(mod_grid, text=mod, is_active=is_active)
            chip.grid(row=row, column=col, padx=2, pady=2, sticky="ew")

        # 5. SYSTEM STATUS MINI SECTION
        ss_frame = ctk.CTkFrame(c, fg_color="transparent", border_color=self.colors["border_normal"], border_width=1)
        ss_frame.pack(fill=ctk.X, padx=10, pady=10, ipady=5)
        ctk.CTkLabel(ss_frame, text="NET_LATENCY: 12ms", font=("Consolas", 9), text_color=self.colors["secondary"]).pack(anchor="w", padx=10)
        ctk.CTkLabel(ss_frame, text="DISK_IO: 3.2 MB/s", font=("Consolas", 9), text_color=self.colors["secondary"]).pack(anchor="w", padx=10)

        # 6. Quick Actions (Bottom)
        qa_frame = ctk.CTkFrame(c, fg_color="transparent")
        qa_frame.pack(side="bottom", fill=ctk.X, pady=10)
        
        ctk.CTkLabel(qa_frame, text="QUICK UPLINK", font=("Orbitron", 12), text_color=self.colors["secondary"]).pack(pady=5)
        
        qa_grid = ctk.CTkFrame(qa_frame, fg_color="transparent")
        qa_grid.pack(fill=ctk.BOTH, expand=True)
        qa_grid.grid_columnconfigure(0, weight=1)
        qa_grid.grid_columnconfigure(1, weight=1)
        
        # Updated Button Style with Cyan Glow
        btn_style = {"height": 32, "corner_radius": 0, "font": ("Share Tech Mono", 11), 
                     "fg_color": "transparent", "text_color": self.colors["secondary"], 
                     "border_color": self.colors["secondary"], "border_width": 1, 
                     "hover_color": "#001A1D"}
        
        ctk.CTkButton(qa_grid, text="SHUTDOWN", command=lambda: self._process_text_query("shutdown system"), **btn_style).grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        ctk.CTkButton(qa_grid, text="RESTART", command=lambda: self._process_text_query("restart system"), **btn_style).grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        ctk.CTkButton(qa_grid, text="LOCK SYS", command=lambda: self._process_text_query("lock screen"), **btn_style).grid(row=1, column=0, padx=2, pady=2, sticky="ew")
        ctk.CTkButton(qa_grid, text="BROWSER", command=lambda: self._process_text_query("open chrome"), **btn_style).grid(row=1, column=1, padx=2, pady=2, sticky="ew")

    def init_right_widgets(self):
        c = self.sidebar_right.content
        
        # Neural Link Signal Strength
        sig_frame = ctk.CTkFrame(c, fg_color="transparent")
        sig_frame.pack(fill=ctk.X, pady=(5, 10), padx=10)
        
        ctk.CTkLabel(sig_frame, text="NEURAL LINK: STRONG", font=("Share Tech Mono", 9), text_color=self.colors["primary"]).pack(side="left")
        
        bar_f = ctk.CTkFrame(sig_frame, fg_color="transparent")
        bar_f.pack(side="right")
        for i in range(4):
            h = 4 + i*3
            ctk.CTkFrame(bar_f, width=3, height=h, fg_color=self.colors["primary"]).pack(side="left", padx=1, anchor="s")

        # Thin separator line
        ctk.CTkFrame(c, height=1, fg_color=self.colors["border_normal"]).pack(fill=ctk.X, padx=10, pady=5)

        # Active Automations
        ctk.CTkLabel(c, text="ACTIVE AUTOMATIONS", font=("Orbitron", 12), text_color=self.colors["secondary"]).pack(pady=(5, 5))
        auto_frame = ctk.CTkFrame(c, fg_color="transparent")
        auto_frame.pack(fill=ctk.X, padx=10)
        
        autos = [("System Monitor", self.colors["primary"]), 
                 ("Background Sync", self.colors["accent_amber"]),
                 ("Neural Uplink", self.colors["primary"]),
                 ("Crypto Watch", self.colors["secondary"])]
        
        for name, dot_color in autos:
            a = ctk.CTkFrame(auto_frame, fg_color="transparent")
            a.pack(fill=ctk.X, pady=2)
            ctk.CTkLabel(a, text=name, font=("Exo 2 Light", 10), text_color=self.colors["text"]).pack(side="left")
            ctk.CTkLabel(a, text="●", font=("Consolas", 10), text_color=dot_color).pack(side="right")

        # Weather Widget (Polished)
        w_frame = ctk.CTkFrame(c, fg_color="transparent")
        w_frame.pack(side="bottom", fill=ctk.X, pady=10, padx=10)
        
        # Thin top border separator
        sep = ctk.CTkFrame(w_frame, height=1, fg_color=self.colors["border_normal"])
        sep.pack(fill=ctk.X, pady=(0, 10))
        
        weather_top = ctk.CTkFrame(w_frame, fg_color="transparent")
        weather_top.pack(fill=ctk.X)
        
        self.temp_lbl = ctk.CTkLabel(weather_top, text="29°C", font=("Share Tech Mono", 16, "bold"), text_color=self.colors["primary"])
        self.temp_lbl.pack(side="left")
        
        self.cond_lbl = ctk.CTkLabel(weather_top, text="CLOUDY", font=("Share Tech Mono", 10), text_color=self.colors["secondary"])
        self.cond_lbl.pack(side="left", padx=10)

        self.city_lbl = ctk.CTkLabel(w_frame, text="NEW DELHI | INDIA", font=("Share Tech Mono", 9), text_color=self.colors["secondary"])
        self.city_lbl.pack(anchor="w")

        self.uptime_lbl = ctk.CTkLabel(w_frame, text="UP: 00:00:00", font=("Share Tech Mono", 10), text_color=self.colors["secondary"])
        self.uptime_lbl.pack(anchor="e", pady=(5, 0))

    def animate_scanline(self):
        self.scanline_canvas.delete("scan")
        w = self.scanline_canvas.winfo_width()
        h = self.scanline_canvas.winfo_height()
        if h > 10:
            self.scan_y += 2
            if self.scan_y > h:
                self.scan_y = 0
            
            # Draw faded line
            self.scanline_canvas.create_line(0, self.scan_y, w, self.scan_y, fill=self.colors["border_active"], width=2, stipple="gray50", tags="scan")
        
        self.after(50, self.animate_scanline)

    def animate_brackets(self):
        self.bracket_anim_state += 0.05
        # Oscillate color between primary and secondary for a "breathing" effect
        # We calculate a mix color roughly
        osc = (math.sin(self.bracket_anim_state) + 1) / 2 # 0 to 1
        
        # Slow glow oscillation
        color = self.colors["primary"] if osc > 0.5 else self.colors["secondary"]
        
        self.sidebar_left.border_color = color
        self.center_panel.border_color = color
        self.sidebar_right.border_color = color
        
        self.sidebar_left._draw_brackets()
        self.center_panel._draw_brackets()
        self.sidebar_right._draw_brackets()
        
        self.after(100, self.animate_brackets)

    def update_clock(self):
        now = time.strftime("%H:%M:%S")
        self.time_label.configure(text=now)
        self.date_lbl.configure(text=time.strftime("%d-%m-%Y"))
        
        up_secs = int(time.time() - self.start_time)
        up_str = f"UP: {up_secs//3600:02d}:{(up_secs%3600)//60:02d}:{up_secs%60:02d}"
        self.uptime_lbl.configure(text=up_str)
        
        # Blinking conn dot & Status Dot
        blink = up_secs % 2 == 0
        self.conn_dot.configure(text_color=self.colors["primary"] if blink else self.colors["bg"])
        self.status_dot.configure(text_color=self.colors["primary"] if blink else "#002211")
        
        self.after(1000, self.update_clock)

    def update_metrics_loop(self):
        # Run every 2 seconds instead of 1 to reduce overhead
        cpu = psutil.cpu_percent(interval=None) 
        ram = psutil.virtual_memory().percent
        
        self.cpu_bar.set(cpu / 100)
        self.ram_bar.set(ram / 100)
        
        # Update System Vitals
        io = psutil.disk_io_counters()
        io_total = (io.read_bytes + io.write_bytes) / (1024 * 1024) # MB
        self.vitals_bar.configure(text=f"CPU: {int(cpu)}% | RAM: {int(ram)}% | NET: 12ms | DISK: {io_total:.1f}MB/s")
        
        vis_mood, voc_mood = self.state_manager.get_bio_status()
        self.bio_canvas.amplitude = 10 if vis_mood == "Neutral" else 25
        
        self.after(2000, self.update_metrics_loop)

    def process_logs(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self._typing_insert(msg, "sys")
        except queue.Empty:
            pass

        try:
            while True:
                sender, message = self.state_manager.chat_queue.get_nowait()
                # Dynamic Color Coding
                tag = "saar"
                if message.startswith(">>>>>"): tag = "sys_dim"
                elif "[SAAR]" in message or "[Neural" in message: tag = "saar"
                elif "WARNING" in message.upper() or "WARN" in message.upper(): tag = "warn"
                elif "ERROR" in message.upper(): tag = "error"
                elif sender == "User": tag = "user"
                else: tag = "sys" # Default green

                self.add_to_chat(sender, message, tag)
        except queue.Empty:
            pass

        self.after(50, self.process_logs)

    def _add_dummy_logs(self):
        dummies = [
            ("SYS", ">>>>> Calibrating Neural Arrays..."),
            ("SAAR", "[SAAR]: Voice engine loaded successfully."),
            ("SAAR", "[SAAR]: Biometric uplink established."),
            ("SYS", "[SYS]: All 108 modules reporting green."),
            ("SAAR", "Dashboard initialized. Ready for command.")
        ]
        for s, m in dummies:
            self.state_manager.add_chat(s, m)

    def toggle_eye(self):
        import pipeline.presence_pipeline as pp
        pp.PRESENCE_ENABLED = self.eye_toggle.get() == 1
        status = "ENABLED" if pp.PRESENCE_ENABLED else "DISABLED"
        self.state_manager.add_chat("SAAR", f"Neural Eye is now {status} Sagar.")
        
        if pp.PRESENCE_ENABLED and hasattr(pp, 'global_presence_tracker') and pp.global_presence_tracker:
            pp.global_presence_tracker.start(self.state_manager)
        elif not pp.PRESENCE_ENABLED and hasattr(pp, 'global_presence_tracker') and pp.global_presence_tracker:
            pp.global_presence_tracker.stop()

    def update_pitch(self, val):
        import voice.tts as tts
        val = int(val)
        sign = "+" if val >= 0 else "-"
        tts.VOICE_PITCH = f"{sign}{abs(val)}Hz"
        self.pitch_lbl.configure(text=f"PITCH: {val}Hz")

    def update_speed(self, val):
        import voice.tts as tts
        val = int(val)
        tts.VOICE_RATE = f"+{val}%"
        self.speed_lbl.configure(text=f"SPEED: +{val}%")

    def add_to_chat(self, sender, message, tag="user"):
        self.chat_container.configure(state="normal", font=("Share Tech Mono", 9))
        
        # Color definitions for tags
        self.chat_container.tag_config("sys_dim", foreground="#1e2a1e")
        self.chat_container.tag_config("saar", foreground="#00E5FF")
        self.chat_container.tag_config("warn", foreground="#FFAA00")
        self.chat_container.tag_config("error", foreground="#FF3366")
        self.chat_container.tag_config("user", foreground="#FFFFFF")
        self.chat_container.tag_config("sys", foreground="#00FF88")
        
        # Line spacing
        self.chat_container.configure(spacing1=2, spacing3=2) # Simulated 4px gap (2 top + 2 bottom)

        if sender == "SAAR" and message != "📡 Processing Neural Grid...":
            pos = self.chat_container.search("📡 Processing Neural Grid...", "1.0", ctk.END)
            if pos:
                self.chat_container.delete(f"{pos} linestart", ctk.END)

        # Fix duplicate prefix bug
        display_msg = message
        prefix = f"[{sender}]:"
        if display_msg.startswith(prefix):
            display_msg = display_msg[len(prefix):].strip()

        self.chat_container.insert(ctk.END, f"\n[{sender}]: ", tag)
        self.chat_container.insert(ctk.END, display_msg + "\n", tag)
        self.chat_container.see(ctk.END)
        self.chat_container.configure(state="disabled")

    def _typing_insert(self, text, tag="sys", index=0):
        if index == 0:
            self.chat_container.configure(state="normal")
            
        if index < len(text):
            self.chat_container.insert(ctk.END, text[index], tag)
            self.chat_container.see(ctk.END)
            self.after(15, lambda: self._typing_insert(text, tag, index+1))
        else:
            self.chat_container.configure(state="disabled")

    def toggle_mic_gui(self):
        if self.state_manager.is_work_mode():
            self.state_manager.set_work_mode(False)
            self.mic_btn.configure(fg_color="#111", text_color=self.colors["secondary"])
            self.waveform.set_active(False)
            self.state_manager.add_chat("SAAR", "Neural Voice Link Terminated. Wake word required.")
        else:
            self.state_manager.set_work_mode(True)
            self.mic_btn.configure(fg_color=self.colors["critical"], text_color="#FFF")
            self.waveform.set_active(True)
            self.state_manager.add_chat("SAAR", "Continuous Neural Voice Link Established. I am listening...")

    def send_text_command(self, query=None):
        if query is None:
            query = self.query_entry.get().strip()
        if not query: return
            
        self.query_entry.delete(0, ctk.END)
        self.state_manager.add_chat("User", query)
        threading.Thread(target=self._process_text_query, args=(query,), daemon=True).start()

    def _process_text_query(self, query):
        self.state_manager.set("thinking")
        self.state_manager.add_chat("SAAR", "📡 Processing Neural Grid...")
        
        response, sentiment = ask_brain(query, self.state_manager)
        self.state_manager.set_sentiment(sentiment["polarity"], sentiment["label"])
        self.state_manager.add_chat("SAAR", response)
        
        self.state_manager.set("speaking")
        speak(response)
        self.state_manager.set("idle")

    def update_status_loop(self):
        current = self.state_manager.get()
        
        if current == "idle":
            self.status_label.configure(text="[ SAAR READY : STANDBY ]")
        elif current == "listening":
            self.status_label.configure(text="[ SAAR : LISTENING... ]")
            self.mic_btn.configure(border_color=self.colors["critical"])
        elif current == "thinking":
            self.status_label.configure(text="[ SAAR : PROCESSING ]")
        elif current == "speaking":
            self.status_label.configure(text="[ SAAR : COMMUNICATING ]")
            
        self.after(500, self.update_status_loop)

    def start_services(self):
        def _delayed_start():
            from pipeline.voice_pipeline import run_voice_pipeline
            from pipeline.presence_pipeline import PresencePipeline
            
            self._typing_insert("🚀 [Neural Core] Initializing sensors in background...\n", "sys")
            try:
                # Initialize in thread to prevent UI hang
                self.presence_tracker = PresencePipeline()
                self.presence_tracker.start(self.state_manager)
            except Exception as e:
                print(f"[UI ERROR] Sensor failure: {e}")
                self.presence_tracker = None
            
            threading.Thread(target=run_voice_pipeline, args=(self.state_manager,), daemon=True).start()

        # Small delay to let UI stabilize first
        self.after(1500, _delayed_start)

def run_app():
    app = SAAR_UI()
    app.mainloop()
