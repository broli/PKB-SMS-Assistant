import sys
import os
import customtkinter as ctk
from ui.main_window import MainWindow

APP_VERSION = "2.3"

if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    
    # Linux (especially KDE/Wayland) often has rendering bugs with forced scaling in Tkinter
    # We keep it at 1.0 for Linux, and use 1.2 for Windows/macOS
    if sys.platform.startswith("linux"):
        ctk.set_widget_scaling(1.0)
        ctk.set_window_scaling(1.0)
    else:
        ctk.set_widget_scaling(1.2)
        ctk.set_window_scaling(1.2)
    
    app = MainWindow(version=APP_VERSION)
    app.mainloop()
