import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QTextEdit, QPushButton, QScrollArea, 
                               QWidget, QFileDialog, QMessageBox, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from modules import config_manager, contact_book
from modules.gemini_ai import DEFAULT_PROMPT
from ui.import_preview import ImportPreviewWindow
from ui.qt_workers import OAuthLoginWorker

class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings - API Keys & Prompts")
        self.resize(600, 750)
        self.setModal(True)
        
        self.config = config_manager.load_config()
        self.worker = None # keep reference to thread

        # Main Layout
        self.main_layout = QVBoxLayout(self)
        
        # Scroll Area
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.main_layout.addWidget(self.scroll_area)

        # Title
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title_label = QLabel("Configure Assistant Settings")
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.scroll_layout.addWidget(self.title_label)
        self.scroll_layout.addSpacing(15)

        # GoTo OAuth Login
        self.login_frame = QFrame()
        self.login_layout = QHBoxLayout(self.login_frame)
        self.login_layout.setContentsMargins(0, 0, 0, 0)
        
        has_token = bool(self.config.get("access_token"))
        status_text = "Status: Logged In" if has_token else "Status: Not Logged In"
        self.login_status = QLabel(status_text)
        if has_token:
            self.login_status.setStyleSheet("color: green;")
        else:
            self.login_status.setStyleSheet("color: red;")
            
        self.login_layout.addWidget(self.login_status)
        self.login_layout.addStretch()
        
        self.login_button = QPushButton("Login with GoTo")
        self.login_button.clicked.connect(self.do_login)
        self.login_layout.addWidget(self.login_button)
        
        self.scroll_layout.addWidget(self.login_frame)
        self.scroll_layout.addSpacing(10)

        # GoTo Phone Number
        self.scroll_layout.addWidget(QLabel("GoTo Account Phone Number (From):"))
        self.phone_entry = QLineEdit()
        self.phone_entry.setPlaceholderText("+1234567890")
        self.phone_entry.setText(self.config.get("goto_phone", ""))
        self.scroll_layout.addWidget(self.phone_entry)
        self.scroll_layout.addSpacing(10)

        # Gemini Free API Key
        self.scroll_layout.addWidget(QLabel("Free Gemini API Key:"))
        self.gemini_free_entry = QLineEdit()
        self.gemini_free_entry.setEchoMode(QLineEdit.Password)
        self.gemini_free_entry.setText(self.config.get("gemini_api_key", ""))
        self.scroll_layout.addWidget(self.gemini_free_entry)
        self.scroll_layout.addSpacing(10)

        # Gemini Paid API Key
        self.scroll_layout.addWidget(QLabel("Paid Gemini API Key:"))
        self.gemini_paid_entry = QLineEdit()
        self.gemini_paid_entry.setEchoMode(QLineEdit.Password)
        self.gemini_paid_entry.setText(self.config.get("gemini_api_key_paid", ""))
        self.scroll_layout.addWidget(self.gemini_paid_entry)
        self.scroll_layout.addSpacing(15)

        # AI Custom Prompt
        self.scroll_layout.addWidget(QLabel("Custom AI System Prompt:"))
        self.prompt_text = QTextEdit()
        self.prompt_text.setMinimumHeight(200)
        current_prompt = self.config.get("custom_prompt") or DEFAULT_PROMPT
        self.prompt_text.setPlainText(current_prompt)
        self.scroll_layout.addWidget(self.prompt_text)

        self.reset_button = QPushButton("Reset to Default Prompt")
        self.reset_button.clicked.connect(self.reset_prompt)
        self.scroll_layout.addWidget(self.reset_button)
        self.scroll_layout.addSpacing(20)

        # Contact Book Section
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        self.scroll_layout.addWidget(sep)

        contacts_font = QFont()
        contacts_font.setPointSize(12)
        contacts_font.setBold(True)
        self.contacts_label = QLabel("Contact Book")
        self.contacts_label.setFont(contacts_font)
        self.scroll_layout.addWidget(self.contacts_label)

        self.contacts_desc = QLabel("Sync names from a GoTo copy-paste TXT file.")
        self.contacts_desc.setStyleSheet("color: gray;")
        self.scroll_layout.addWidget(self.contacts_desc)

        self.import_btn = QPushButton("📂 Import from GoTo (.txt)")
        self.import_btn.clicked.connect(self.open_import_file)
        self.scroll_layout.addWidget(self.import_btn)

        self.scroll_layout.addStretch()

        # Save Button (Bottom)
        self.save_button = QPushButton("Save Settings")
        self.save_button.setMinimumHeight(40)
        self.save_button.clicked.connect(self.save_settings)
        self.main_layout.addWidget(self.save_button)

    def reset_prompt(self):
        self.prompt_text.setPlainText(DEFAULT_PROMPT)

    def do_login(self):
        self.login_button.setEnabled(False)
        self.login_button.setText("Waiting in browser...")
        
        self.worker = OAuthLoginWorker()
        self.worker.finished.connect(self.on_login_complete)
        self.worker.start()

    def on_login_complete(self, success):
        self.login_button.setEnabled(True)
        self.login_button.setText("Login with GoTo")
        if success:
            self.login_status.setText("Status: Logged In")
            self.login_status.setStyleSheet("color: green;")
            self.config = config_manager.load_config()
        else:
            self.login_status.setText("Status: Login Failed")
            self.login_status.setStyleSheet("color: red;")

    def open_import_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Raw GoTo Contacts Text File", "", "Text files (*.txt);;All files (*.*)"
        )
        if not path:
            return
            
        plan = contact_book.analyze_raw_text(path)
        
        total_changes = len(plan["new"]) + len(plan["update"])
        if total_changes == 0 and plan["total_scanned"] > 0:
            QMessageBox.information(self, "Import Information", "No new contacts or updates found. Your list is already up to date!")
            return
        elif plan["total_scanned"] == 0:
            QMessageBox.warning(self, "Import Warning", "The file appears to be empty or invalid.")
            return

        self.preview_window = ImportPreviewWindow(plan, parent=self)
        self.preview_window.import_confirmed.connect(self._on_import_confirmed)
        self.preview_window.exec()

    def _on_import_confirmed(self, success):
        if success:
            QMessageBox.information(self, "Import Successful", "Contacts merged successfully!")
            # The parent main window will need a way to refresh contacts
            if hasattr(self.parent(), "reload_contacts"):
                self.parent().reload_contacts()
        else:
            QMessageBox.critical(self, "Import Error", "Failed to save contacts. Check console for details.")

    def save_settings(self):
        new_config = {
            "access_token": self.config.get("access_token", ""),
            "refresh_token": self.config.get("refresh_token", ""),
            "goto_phone": self.phone_entry.text(),
            "gemini_api_key": self.gemini_free_entry.text(),
            "gemini_api_key_paid": self.gemini_paid_entry.text(),
            "custom_prompt": self.prompt_text.toPlainText().strip()
        }

        config_manager.save_config(new_config)
        self.accept()
