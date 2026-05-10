import os
import logging
import tempfile
from cryptography.fernet import Fernet
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressDialog, QMessageBox
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile
from PySide6.QtCore import QUrl, Signal

class MSAuthWindow(QDialog):
    """
    A dialog that embeds a web browser to log the user into Microsoft 365,
    navigates to a SharePoint direct-download link, intercepts the downloaded file,
    and decrypts the API key in memory.
    """
    # Signal emitted when the key is successfully retrieved and decrypted
    key_retrieved = Signal(str)

    def __init__(self, download_url: str, decryption_key: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Company Authentication")
        self.resize(600, 700)
        self.download_url = download_url
        self.decryption_key = decryption_key
        
        layout = QVBoxLayout(self)
        
        self.label = QLabel("Please log in to your Microsoft account to verify your employee status.")
        layout.addWidget(self.label)
        
        # Create a persistent web profile so cookies are saved (user doesn't log in every time)
        self.profile = QWebEngineProfile("MSAuthProfile", self)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)
        
        # Connect to the download requested signal
        self.profile.downloadRequested.connect(self.on_download_requested)
        
        # Set up the web view
        self.browser = QWebEngineView(self)
        self.browser.setPage(self.browser.page())
        # Apply the profile to a new page
        from PySide6.QtWebEngineCore import QWebEnginePage
        page = QWebEnginePage(self.profile, self.browser)
        self.browser.setPage(page)
        
        layout.addWidget(self.browser)
        
        # Navigate to the SharePoint download link
        logging.info("Navigating to auth link...")
        self.browser.setUrl(QUrl(self.download_url))

    def on_download_requested(self, download_item):
        """Intercepts the file download triggered by SharePoint"""
        logging.info("Download requested from SharePoint!")
        
        # We save it to a temporary location
        self.temp_dir = tempfile.gettempdir()
        self.temp_file = os.path.join(self.temp_dir, "encrypted_key.tmp")
        
        download_item.setDownloadDirectory(self.temp_dir)
        download_item.setDownloadFileName("encrypted_key.tmp")
        
        download_item.finished.connect(self.on_download_finished)
        download_item.accept()
        
        self.label.setText("Verifying your access... Please wait.")
        self.browser.hide()

    def on_download_finished(self):
        """Called when the encrypted file finishes downloading to the temp folder"""
        logging.info("Download finished. Decrypting payload...")
        
        if not os.path.exists(self.temp_file):
            QMessageBox.critical(self, "Error", "Failed to retrieve the verification file.")
            self.reject()
            return
            
        try:
            with open(self.temp_file, "rb") as f:
                encrypted_payload = f.read()
                
            # Immediately delete the file from the hard drive so it doesn't linger
            os.remove(self.temp_file)
            
            # Decrypt it
            cipher_suite = Fernet(self.decryption_key)
            api_key = cipher_suite.decrypt(encrypted_payload).decode('utf-8')
            
            logging.info("Successfully decrypted API key in memory.")
            self.key_retrieved.emit(api_key)
            self.accept()
            
        except Exception as e:
            logging.error(f"Failed to decrypt the payload: {e}")
            QMessageBox.critical(self, "Decryption Error", "You do not have access, or the file is invalid.")
            self.reject()
