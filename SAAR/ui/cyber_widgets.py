import customtkinter as ctk
import tkinter as tk
import math
import time

class CyberFrame(ctk.CTkFrame):
    """A frame with L-bracket corners and a subtle top gradient line, drawn via Canvas."""
    def __init__(self, master, border_color="#00331A", bg_color="#010A14", **kwargs):
        super().__init__(master, fg_color=bg_color, corner_radius=0, **kwargs)
        self.border_color = border_color
        
        self.canvas = tk.Canvas(self, bg=bg_color, highlightthickness=0)
        self.canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        self.bind("<Configure>", self._draw_brackets)
        
        # We need an inner frame for actual content so it sits on top of the canvas
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(fill=ctk.BOTH, expand=True, padx=4, pady=4)
        
    def _draw_brackets(self, event=None):
        self.canvas.delete("bracket")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 10 or h < 10: return
        
        c = self.border_color
        lw = 2 # line width
        ll = 15 # line length
        
        # Top-left
        self.canvas.create_line(0, 0, ll, 0, fill=c, width=lw, tags="bracket")
        self.canvas.create_line(0, 0, 0, ll, fill=c, width=lw, tags="bracket")
        # Top-right
        self.canvas.create_line(w, 0, w-ll, 0, fill=c, width=lw, tags="bracket")
        self.canvas.create_line(w, 0, w, ll, fill=c, width=lw, tags="bracket")
        # Bottom-left
        self.canvas.create_line(0, h, ll, h, fill=c, width=lw, tags="bracket")
        self.canvas.create_line(0, h, 0, h-ll, fill=c, width=lw, tags="bracket")
        # Bottom-right
        self.canvas.create_line(w, h, w-ll, h, fill=c, width=lw, tags="bracket")
        self.canvas.create_line(w, h, w, h-ll, fill=c, width=lw, tags="bracket")

        # Top edge gradient line (simulated by a solid cyan line for now since Tkinter doesn't do linear gradients easily)
        self.canvas.create_line(ll, 0, w-ll, 0, fill="#00E5FF", width=1, stipple="gray50", tags="bracket")

class SegmentedProgressBar(ctk.CTkFrame):
    """A progress bar split into 20 glowing segments."""
    def __init__(self, master, segments=20, active_color="#00FF88", inactive_color="#002211", **kwargs):
        super().__init__(master, fg_color="transparent", height=15, **kwargs)
        self.segments = segments
        self.active_color = active_color
        self.inactive_color = inactive_color
        self.value = 0.0 # 0.0 to 1.0
        
        self.canvas = tk.Canvas(self, bg="#010A14", highlightthickness=0, height=15)
        self.canvas.pack(fill=ctk.BOTH, expand=True)
        self.bind("<Configure>", self._draw_segments)
        
        # Pulse animation
        self.pulse_state = True
        self._pulse()
        
    def set(self, value):
        self.value = max(0.0, min(1.0, value))
        self._draw_segments()
        
    def _draw_segments(self, event=None):
        self.canvas.delete("seg")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 10: return
        
        seg_w = (w - (self.segments - 1) * 2) / self.segments
        active_count = int(self.value * self.segments)
        
        for i in range(self.segments):
            x0 = i * (seg_w + 2)
            x1 = x0 + seg_w
            
            color = self.inactive_color
            if i < active_count:
                color = self.active_color
                
            # Pulsing tip
            if i == active_count - 1 and self.pulse_state:
                color = "#FFFFFF" # bright white flash
                
            self.canvas.create_rectangle(x0, 2, x1, h-2, fill=color, outline="", tags="seg")
            
    def _pulse(self):
        self.pulse_state = not self.pulse_state
        self._draw_segments()
        self.after(500, self._pulse)

class HeartbeatCanvas(tk.Canvas):
    """A sine wave animation simulating a biometric heartbeat."""
    def __init__(self, master, color="#00FF88", **kwargs):
        super().__init__(master, bg="#010A14", highlightthickness=0, **kwargs)
        self.color = color
        self.offset = 0
        self.amplitude = 10
        self.frequency = 0.1
        self._animate()
        
    def _animate(self):
        self.delete("wave")
        w = self.winfo_width()
        h = self.winfo_height()
        if w > 10:
            cy = h / 2
            points = []
            for x in range(0, w, 2):
                # Simple moving sine wave
                y = cy + math.sin((x + self.offset) * self.frequency) * self.amplitude
                
                # Add a sharp "heartbeat" spike in the middle
                if w/2 - 10 < (x + self.offset) % w < w/2 + 10:
                    y -= 20 * math.sin((x + self.offset) * 0.5)
                
                points.append(x)
                points.append(y)
            
            if points:
                self.create_line(points, fill=self.color, width=2, tags="wave", smooth=True)
                
        self.offset += 5
        self.after(50, self._animate)

class WaveformBar(tk.Canvas):
    """An animated waveform that activates when the mic is on."""
    def __init__(self, master, color="#00E5FF", bg_color="#000B0C", **kwargs):
        super().__init__(master, bg=bg_color, highlightthickness=0, **kwargs)
        self.color = color
        self.active = False
        self.offset = 0
        self._animate()

    def set_active(self, active):
        self.active = active

    def _animate(self):
        self.delete("wave")
        w = self.winfo_width()
        h = self.winfo_height()
        if w > 10:
            cy = h / 2
            points = []
            
            # Dynamic amplitude and color based on active state
            if self.active:
                target_amp = 20
                color = "#00E5FF" # Cyan active
                freq = 0.2
            else:
                target_amp = 5
                color = "#00FF88" # Green standby
                freq = 0.1
                
            for x in range(0, w, 4):
                # Sine wave with gentle pulse
                y = cy + math.sin((x + self.offset) * freq) * target_amp
                points.append(x)
                points.append(y)
            if points:
                self.create_line(points, fill=color, width=2, tags="wave", smooth=True)
                
        self.offset += 5
        self.after(30, self._animate)

class DotGridCanvas(tk.Canvas):
    """A subtle dot-grid pattern renderer."""
    def __init__(self, master, dot_color="rgba(0, 255, 136, 0.05)", spacing=20, **kwargs):
        super().__init__(master, highlightthickness=0, **kwargs)
        self.dot_color = "#001108" # Hardcoded subtle green for Tkinter
        self.spacing = spacing
        self.bind("<Configure>", self._draw_grid)

    def _draw_grid(self, event=None):
        self.delete("grid")
        w = self.winfo_width()
        h = self.winfo_height()
        for x in range(0, w, self.spacing):
            for y in range(0, h, self.spacing):
                self.create_oval(x, y, x+1, y+1, fill=self.dot_color, outline="", tags="grid")

class OrbitalBackground(tk.Canvas):
    """A radial gradient simulator for the central orb area."""
    def __init__(self, master, center_color="#000408", edge_color="#000B0C", **kwargs):
        super().__init__(master, bg=center_color, highlightthickness=0, **kwargs)
        self.center_color = center_color
        self.edge_color = edge_color
        self.bind("<Configure>", self._draw_gradient)

    def _draw_gradient(self, event=None):
        self.delete("grad")
        w = self.winfo_width()
        h = self.winfo_height()
        cx, cy = w/2, h/2
        max_r = math.sqrt(cx**2 + cy**2)
        
        # Draw concentric circles to simulate radial gradient
        steps = 10
        for i in range(steps, 0, -1):
            r = (i / steps) * max_r * 0.8
            # Dimmer as we go out
            alpha = int(255 * (1 - i/steps))
            # Simulated color mixing with black
            # Since we can't do real alpha on Canvas, we just use darker shades
            self.create_oval(cx-r, cy-r, cx+r, cy+r, fill=self.edge_color, outline="", tags="grad")

class HUDModuleChip(ctk.CTkFrame):
    """A small styled chip for HUD modules."""
    def __init__(self, master, text, is_active=False, **kwargs):
        self.is_active = is_active
        color = "#00E5FF" if is_active else "#555"
        bg = "#001A1D" if is_active else "transparent"
        super().__init__(master, fg_color=bg, border_color=color, border_width=1, corner_radius=2, **kwargs)
        
        self.label = ctk.CTkLabel(self, text=text, font=("Share Tech Mono", 9), text_color=color)
        self.label.pack(expand=True, fill=ctk.BOTH, padx=4, pady=1)

    def set_active(self, active):
        self.is_active = active
        color = "#00E5FF" if active else "#555"
        bg = "#001A1D" if active else "transparent"
        self.configure(fg_color=bg, border_color=color)
        self.label.configure(text_color=color)
