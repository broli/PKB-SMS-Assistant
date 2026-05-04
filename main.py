import customtkinter as ctk
from ui.main_window import MainWindow

APP_VERSION = "2.0"

if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    
    # Increase UI scaling for better readability (1.2 = 120%)
    ctk.set_widget_scaling(1.2)
    ctk.set_window_scaling(1.2)
    
    app = MainWindow(version=APP_VERSION)
    app.mainloop()
