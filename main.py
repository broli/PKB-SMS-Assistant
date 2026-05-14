import sys
import os
import logging
import traceback
import faulthandler
from PySide6.QtWidgets import QApplication, QMessageBox
from ui.main_window import MainWindow
# Enable faulthandler to catch native segmentation faults (0xc0000005)
# This will write the C-level traceback to crash.log even if Python crashes silently.
try:
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    crash_log_path = os.path.join(base_dir, "crash.log")
    crash_log_file = open(crash_log_path, "a")
    import datetime
    crash_log_file.write(f"\n--- APP SESSION STARTED AT {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
    crash_log_file.flush()
    faulthandler.enable(file=crash_log_file)
except Exception:
    pass

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
    try:
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        crash_log_path = os.path.join(base_dir, "crash.log")
        
        with open(crash_log_path, "a") as f:
            import datetime
            f.write(f"\n--- CRASH AT {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            f.write(error_msg)
            f.write("-" * 30 + "\n")
    except Exception as e:
        logging.error(f"Failed to write crash log: {e}")

    # Show a message box to the user since it's a GUI app
    try:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
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

