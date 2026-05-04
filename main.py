import sys
import os
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

APP_VERSION = "3.0"

if __name__ == "__main__":
    # Globally scale the Qt UI for better readability
    os.environ["QT_SCALE_FACTOR"] = "1.2"
    
    app = QApplication(sys.argv)
    
    # Modern Qt styling or OS-native style is used by default
    app.setStyle("Fusion") # Optional: Gives a consistent clean look across OSes

    
    window = MainWindow(version=APP_VERSION)
    window.show()
    
    sys.exit(app.exec())

