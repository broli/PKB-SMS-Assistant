import sys

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    from ui.auth_window import MSAuthWindow
    try:
        from corporate_secrets import AUTH_DOWNLOAD_URL, DECRYPTION_KEY
    except ImportError:
        AUTH_DOWNLOAD_URL = None
        DECRYPTION_KEY = None

    app = QApplication(sys.argv)
    win = MSAuthWindow(AUTH_DOWNLOAD_URL, DECRYPTION_KEY)
    win.show()
    sys.exit(app.exec())


