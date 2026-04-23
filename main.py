import customtkinter as ctk
from ui.main_window import MainWindow

APP_VERSION = "2.1"

if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    
    app = MainWindow(version=APP_VERSION)
    app.mainloop()
