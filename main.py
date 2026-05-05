import sys
import os
import logging
import traceback
from PySide6.QtWidgets import QApplication, QMessageBox
from ui.main_window import MainWindow

APP_VERSION = "3.0"

def setup_logging():
    """Sets up logging. If --debug is in sys.argv, logs to app.log."""
    log_level = logging.INFO
    log_file = None
    
    if "--debug" in sys.argv:
        log_file = "app.log"
        log_level = logging.DEBUG
        print("Debug mode enabled. Logging to app.log")

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file) if log_file else logging.NullHandler(),
            logging.StreamHandler(sys.stdout)
        ]
    )

def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler to log crashes even if debug mode is off."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logging.critical("Uncaught exception:\n%s", error_msg)
    
    # Always write fatal crashes to a separate file for easy discovery
    with open("crash.log", "a") as f:
        import datetime
        f.write(f"\n--- CRASH AT {datetime.datetime.now()} ---\n")
        f.write(error_msg)
        f.write("-" * 30 + "\n")

    # Show a message box to the user since it's a GUI app
    try:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("The application has crashed.")
        msg.setInformativeText("An error log has been saved to 'crash.log'. Please share this file with the developer.")
        msg.setWindowTitle("Fatal Error")
        msg.setDetailedText(error_msg)
        msg.exec()
    except:
        pass # If Qt isn't initialized yet, this will fail

if __name__ == "__main__":
    setup_logging()
    sys.excepthook = handle_exception
    
    try:
        # Globally scale the Qt UI for better readability
        os.environ["QT_SCALE_FACTOR"] = "1.2"
        
        app = QApplication(sys.argv)
        app.setStyle("Fusion") 

        window = MainWindow(version=APP_VERSION)
        window.show()
        
        sys.exit(app.exec())
    except Exception:
        # This catches errors during initialization before sys.excepthook takes over
        handle_exception(*sys.exc_info())

