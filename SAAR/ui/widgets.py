# ui/widgets.py

import tkinter as tk
import math

class Orb(tk.Canvas):
    def __init__(self, parent, state_manager, size=120):
        super().__init__(parent, width=size, height=size, bg="#0d0d0d", highlightthickness=0)
        self.state_manager = state_manager
        self.size = size
        self.radius = size // 2 - 10
        self.center = size // 2
        self.angle = 0

        self.circle = self.create_oval(
            self.center - self.radius,
            self.center - self.radius,
            self.center + self.radius,
            self.center + self.radius,
            fill="#4da6ff",
            outline=""
        )

        self.animate()

    def animate(self):
        state = self.state_manager.get()

        if state == "speaking":
            # pulse animation
            pulse = 5 * math.sin(self.angle)
            r = self.radius + pulse
            self.coords(
                self.circle,
                self.center - r,
                self.center - r,
                self.center + r,
                self.center + r
            )
            self.angle += 0.3

        elif state == "listening":
            self.itemconfig(self.circle, fill="#00ff99")

        else:  # idle
            self.itemconfig(self.circle, fill="#4da6ff")
            self.coords(
                self.circle,
                self.center - self.radius,
                self.center - self.radius,
                self.center + self.radius,
                self.center + self.radius
            )

        self.after(50, self.animate)
