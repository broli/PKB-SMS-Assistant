import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QTextEdit, QPushButton, QComboBox,
                               QScrollArea, QFrame, QMessageBox, QCheckBox, QInputDialog, QFileDialog, QDialog)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QIcon

from ui.settings_window import SettingsWindow
from modules import config_manager, rate_limiter, contact_book
from ui.qt_workers import FetchRecentChatsWorker, FetchSMSWorker, GenerateReplyWorker, SendSMSWorker

PRIMARY_BLUE = "#1976D2"

def resource_path(relative_path):
    import sys
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

class MainWindow(QMainWindow):
    def __init__(self, version=""):
        super().__init__()
        title = f"GoTo SMS AI Assistant v{version}" if version else "GoTo SMS AI Assistant"
        self.setWindowTitle(title)
        self.resize(1200, 720)
        self.setMinimumSize(900, 600)

        icon_path = resource_path("app.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._active_phone = ""
        self._contacts = contact_book.load_contacts()
        self._all_conversations = []
        self._active_workers = set()
        self._pending_intents = {}

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self._setup_header()

        self.body_layout = QHBoxLayout()
        self.main_layout.addLayout(self.body_layout, 1)

        self._setup_left_tower()
        self._setup_middle_panel()
        self._setup_right_panel()
        self._setup_status_bar()

        self.cooldown_timer = QTimer(self)
        self.cooldown_timer.timeout.connect(self._update_cooldown_monitor)
        self.cooldown_timer.start(1000)

        QTimer.singleShot(500, self.fetch_recent_chats)

    def _setup_header(self):
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        lbl = QLabel("💬 GoTo SMS AI Assistant")
        lbl.setFont(font)
        header_layout.addWidget(lbl)
        
        header_layout.addStretch()
        
        self.settings_btn = QPushButton("⚙️ Settings")
        self.settings_btn.clicked.connect(self.open_settings)
        header_layout.addWidget(self.settings_btn)
        
        self.main_layout.addWidget(header_frame)

    def _setup_left_tower(self):
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        self.body_layout.addWidget(left_frame, 2)
        
        header_layout = QHBoxLayout()
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        lbl = QLabel("Recent Chats")
        lbl.setFont(font)
        header_layout.addWidget(lbl)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setStyleSheet(f"background-color: {PRIMARY_BLUE}; color: white; font-weight: bold;")
        self.refresh_btn.clicked.connect(self.fetch_recent_chats)
        header_layout.addWidget(self.refresh_btn)
        left_layout.addLayout(header_layout)
        
        search_layout = QHBoxLayout()
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("🔍 Search conversation...")
        self.search_entry.textChanged.connect(self._filter_conversations)
        search_layout.addWidget(self.search_entry)
        
        self.clear_search_btn = QPushButton("✖")
        self.clear_search_btn.setToolTip("Clear search")
        self.clear_search_btn.setFixedWidth(28)
        self.clear_search_btn.clicked.connect(self._on_clear_search_clicked)
        search_layout.addWidget(self.clear_search_btn)
        
        left_layout.addLayout(search_layout)
        
        self.chat_list_area = QScrollArea()
        self.chat_list_area.setWidgetResizable(True)
        self.chat_list_widget = QWidget()
        self.chat_list_layout = QVBoxLayout(self.chat_list_widget)
        self.chat_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_list_area.setWidget(self.chat_list_widget)
        left_layout.addWidget(self.chat_list_area, 1)

    def _on_clear_search_clicked(self):
        if self.search_entry.text():
            self.search_entry.clear()
        else:
            self._filter_conversations()

    def _setup_middle_panel(self):
        mid_frame = QFrame()
        mid_layout = QVBoxLayout(mid_frame)
        self.body_layout.addWidget(mid_frame, 3)
        
        contact_bar = QHBoxLayout()
        self.active_contact_label = QLabel("No contact selected")
        self.active_contact_label.setStyleSheet("color: gray; font-weight: bold;")
        contact_bar.addWidget(self.active_contact_label)
        
        contact_bar.addStretch()
        
        self.receiver_entry = QLineEdit()
        self.receiver_entry.setPlaceholderText("Nickname (optional)")
        self.receiver_entry.setFixedWidth(160)
        contact_bar.addWidget(self.receiver_entry)
        mid_layout.addLayout(contact_bar)
        
        btn_row = QHBoxLayout()
        self.fetch_btn = QPushButton("📨 Load Chat")
        self.fetch_btn.setMinimumHeight(34)
        self.fetch_btn.setStyleSheet(f"background-color: {PRIMARY_BLUE}; color: white; font-weight: bold;")
        self.fetch_btn.clicked.connect(self.fetch_sms)
        btn_row.addWidget(self.fetch_btn)
        
        self.export_btn = QPushButton("📥 Export")
        self.export_btn.setMinimumHeight(34)
        self.export_btn.setStyleSheet(f"background-color: {PRIMARY_BLUE}; color: white; font-weight: bold;")
        self.export_btn.clicked.connect(self.export_history)
        btn_row.addWidget(self.export_btn)
        mid_layout.addLayout(btn_row)
        
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        self.history_text.setPlainText("Select a contact from the left panel to load chat history...")
        mid_layout.addWidget(self.history_text, 1)

    def _setup_right_panel(self):
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        self.body_layout.addWidget(right_frame, 3)
        
        right_layout.addWidget(QLabel("Desired Tone:"))
        
        self.tone_combo = QComboBox()
        self.tone_combo.addItems(["Professional", "Casual", "Empathetic", "Direct", "Apologetic"])
        right_layout.addWidget(self.tone_combo)
        right_layout.addSpacing(10)
        
        right_layout.addWidget(QLabel("What do you want to say?"))
        self.intent_text = QTextEdit()
        right_layout.addWidget(self.intent_text, 1)
        
        gen_btn_layout = QHBoxLayout()
        self.generate_btn = QPushButton("✨ Generate AI Reply")
        self.generate_btn.setStyleSheet(f"background-color: {PRIMARY_BLUE}; color: white; font-weight: bold;")
        self.generate_btn.clicked.connect(self.generate_reply)
        gen_btn_layout.addWidget(self.generate_btn, 1)
        
        self.use_paid_cb = QCheckBox("Use Paid")
        gen_btn_layout.addWidget(self.use_paid_cb)
        right_layout.addLayout(gen_btn_layout)
        
        right_layout.addWidget(QLabel("Draft Reply (Editable):"))
        self.draft_text = QTextEdit()
        right_layout.addWidget(self.draft_text, 2)
        
        action_btn_layout = QHBoxLayout()
        
        self.send_btn = QPushButton("📤 Send SMS")
        self.send_btn.setStyleSheet("background-color: #2da44e; color: white; font-weight: bold;")
        self.send_btn.setMinimumHeight(34)
        self.send_btn.clicked.connect(self.send_sms)
        action_btn_layout.addWidget(self.send_btn, 1)
        
        self.schedule_btn = QPushButton("🔍 Find Commitments")
        self.schedule_btn.setStyleSheet("background-color: #e0e0e0; color: black;")
        self.schedule_btn.setMinimumHeight(34)
        self.schedule_btn.clicked.connect(self._on_schedule_clicked)
        action_btn_layout.addWidget(self.schedule_btn, 1)
        
        right_layout.addLayout(action_btn_layout)

    def _setup_status_bar(self):
        status_frame = QFrame()
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(10, 0, 10, 5)
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: palette(text); font-weight: normal;")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        font = QFont("Consolas", 10)
        self.cooldown_label = QLabel("AI: 0s | GoTo: 0s")
        self.cooldown_label.setFont(font)
        status_layout.addWidget(self.cooldown_label)
        
        self.main_layout.addWidget(status_frame)

    def _set_status(self, text, color="yellow"):
        self.status_label.setText(text)
        if color == "green":
            self.status_label.setStyleSheet("color: #4caf50; font-weight: bold;")
        elif color == "red":
            self.status_label.setStyleSheet("color: #f44336; font-weight: bold;")
        elif color == "yellow":
            self.status_label.setStyleSheet("color: #ffb300; font-weight: bold;")
        else:
            self.status_label.setStyleSheet("color: palette(text); font-weight: normal;")

    def _update_cooldown_monitor(self):
        ai_cd = rate_limiter.get_remaining_cooldown(key="last_ai_call", cooldown_seconds=rate_limiter.AI_COOLDOWN_SECONDS)
        goto_cd = rate_limiter.get_remaining_cooldown(key="last_goto_pull", cooldown_seconds=rate_limiter.GOTO_COOLDOWN_SECONDS)
        self.cooldown_label.setText(f"AI: {ai_cd}s | GoTo: {goto_cd}s")
        if ai_cd > 0 or goto_cd > 0:
            self.cooldown_label.setStyleSheet("color: #d4ac0d;")
        else:
            self.cooldown_label.setStyleSheet("color: gray;")

    def open_settings(self):
        dialog = SettingsWindow(self)
        dialog.exec()

    def reload_contacts(self):
        self._contacts = contact_book.load_contacts()
        self.fetch_recent_chats()

    def fetch_recent_chats(self):
        self.refresh_btn.setEnabled(False)
        self._set_status("Loading recent chats...", "yellow")
        
        worker = FetchRecentChatsWorker()
        worker.data_fetched.connect(self._on_recent_chats_fetched)
        worker.error.connect(self._on_worker_error)
        
        from ui.thread_manager import run_in_thread
        run_in_thread(worker, parent_widget=self)

    def _on_worker_error(self, err_msg):
        self._set_status("An error occurred.", "red")
        self.refresh_btn.setEnabled(True)
        self.fetch_btn.setEnabled(True)
        self.generate_btn.setEnabled(True)
        self.send_btn.setEnabled(True)
        print(err_msg)

    def _on_recent_chats_fetched(self, result):
        self._clear_chat_list()
        
        if "error" in result:
            self._set_status(f"Error: {result['error']}", "red")
            self.refresh_btn.setEnabled(True)
            return

        self._all_conversations = result.get("conversations", [])
        self._filter_conversations()

        if not self._all_conversations:
            self._set_status("No recent conversations found.", "yellow")

        self.refresh_btn.setEnabled(True)

    def _clear_chat_list(self):
        while self.chat_list_layout.count():
            item = self.chat_list_layout.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

    def _filter_conversations(self):
        query = self.search_entry.text().lower().strip()
        self._clear_chat_list()

        filtered = []
        for convo in self._all_conversations:
            phone = convo.get("phone", "Unknown")
            display = contact_book.get_display_name(phone, self._contacts).lower()
            if query in phone.lower() or query in display:
                filtered.append(convo)

        if not filtered:
            msg = "No conversations found." if self._all_conversations else "No recent conversations found."
            if query and self._all_conversations:
                msg = f"No matches for '{query}'"
            lbl = QLabel(msg)
            lbl.setStyleSheet("color: gray;")
            self.chat_list_layout.addWidget(lbl)
        else:
            for convo in filtered:
                self._add_chat_row(convo)

        if query:
            self._set_status(f"Found {len(filtered)} matches.", "green")
        elif self._all_conversations:
            self._set_status(f"Loaded {len(self._all_conversations)} recent conversations.", "green")

    def _add_chat_row(self, convo):
        phone = convo.get("phone", "Unknown")
        unread = convo.get("unread_count", 0)
        display = contact_book.get_display_name(phone, self._contacts)
        badge = f"  🔴 {unread}" if unread > 0 else ""
        label_text = f"{display}{badge}"

        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 2, 0, 2)

        btn = QPushButton(label_text)
        btn.setStyleSheet("text-align: left; padding: 5px;")
        if unread > 0:
            font = btn.font()
            font.setBold(True)
            btn.setFont(font)
        btn.clicked.connect(lambda _, p=phone: self._select_contact(p))
        row_layout.addWidget(btn, 1)

        edit_btn = QPushButton("✏️")
        edit_btn.setFixedSize(28, 28)
        edit_btn.clicked.connect(lambda _, p=phone, rw=row_widget, mb=btn: self._open_nickname_editor(p, rw, mb))
        row_layout.addWidget(edit_btn)

        self.chat_list_layout.addWidget(row_widget)

    def _open_nickname_editor(self, phone, row_widget, main_btn):
        cur = self._contacts.get(phone, {}).get("nickname", "")
        new_nick, ok = QInputDialog.getText(self, "Edit Nickname", "Enter nickname:", QLineEdit.EchoMode.Normal, cur)
        if ok:
            self._contacts = contact_book.set_nickname(phone, new_nick.strip(), self._contacts)
            display = contact_book.get_display_name(phone, self._contacts)
            main_btn.setText(display + (f"  🔴" if "🔴" in main_btn.text() else ""))

    def _select_contact(self, phone):
        if self.search_entry.text():
            self.search_entry.blockSignals(True)
            self.search_entry.clear()
            self.search_entry.blockSignals(False)
            # We don't immediately refresh the list here to avoid deleting the button 
            # that was just clicked, which can cause a crash (Access Violation).
            # The list will be naturally refreshed on next use or manual Refresh.
            
        self._active_phone = phone
        display = contact_book.get_display_name(phone, self._contacts)
        header = display if display != phone else phone
        
        self.active_contact_label.setText(f"📱 {header}")
        self.active_contact_label.setStyleSheet("color: palette(text); font-weight: bold;")
        
        self.receiver_entry.setText(display if display != phone else "")
        self._update_schedule_btn_state(phone)
        self.fetch_sms()

    def fetch_sms(self):
        cooldown = rate_limiter.get_remaining_cooldown(key="last_goto_pull", cooldown_seconds=rate_limiter.GOTO_COOLDOWN_SECONDS)
        if cooldown > 0:
            return

        phone = self._active_phone
        if not phone:
            self._set_status("Select a contact from the left panel first.", "yellow")
            return

        self._set_status("Fetching SMS history...", "yellow")
        self.fetch_btn.setEnabled(False)

        worker = FetchSMSWorker(phone)
        worker.data_fetched.connect(self._on_sms_fetched)
        worker.error.connect(self._on_worker_error)
        
        from ui.thread_manager import run_in_thread
        run_in_thread(worker, parent_widget=self)

    def _on_sms_fetched(self, messages):
        self.history_text.clear()
        
        html = ""
        for msg in messages:
            body = msg.get("body", "")
            is_user = msg.get("is_user", False)

            if body.startswith("Error") or body.startswith("No chat"):
                html += f"<p align='center' style='color: gray;'>{body}</p>"
            elif is_user:
                html += f"<p align='right'><b style='color: #4caf50;'>Me</b><br>{body}</p><br>"
            else:
                name = self.receiver_entry.text().strip() or "Contact"
                html += f"<p align='left'><b style='color: #2196f3;'>{name}</b><br>{body}</p><br>"

        self.history_text.setHtml(html)
        
        scrollbar = self.history_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

        ok = messages and "Error" not in messages[0].get("body", "")
        if ok:
            self._set_status("History loaded.", "green")
        else:
            self._set_status("Error or empty history.", "red")
        self.fetch_btn.setEnabled(True)

    def export_history(self):
        history = self.history_text.toPlainText().strip()
        phone = self._active_phone

        if not history or history.startswith("Select a contact"):
            QMessageBox.warning(self, "Export Warning", "No chat history to export.")
            return
        if "Error" in history:
            QMessageBox.warning(self, "Export Warning", "Cannot export history containing error messages.")
            return

        initial_name = f"SMS_History_{phone.replace('+', '')}.md" if phone else "SMS_History.md"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Chat History", initial_name, "Markdown files (*.md);;Text files (*.txt);;All files (*.*)"
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("# SMS Chat History\n\n")
                    if phone:
                        f.write(f"**Contact:** {phone}\n\n")
                    f.write("---\n\n")
                    f.write(history)
                self._set_status(f"Exported to {file_path}", "green")
                QMessageBox.information(self, "Export Successful", f"History exported to:\n{file_path}")
            except Exception as e:
                self._set_status(f"Export failed: {e}", "red")
                QMessageBox.critical(self, "Export Error", f"Failed to export: {e}")

    def generate_reply(self):
        if rate_limiter.get_remaining_cooldown() > 0:
            return

        history = self.history_text.toPlainText().strip()
        intent = self.intent_text.toPlainText().strip()
        tone = self.tone_combo.currentText()

        if not intent:
            self._set_status("Error: Enter your intent first.", "red")
            return

        use_paid = self.use_paid_cb.isChecked()
        self.use_paid_cb.setChecked(False)

        self._set_status("Drafting reply...", "yellow")
        self.generate_btn.setEnabled(False)
        self.draft_text.clear()

        worker = GenerateReplyWorker(
            history, intent, tone, self.receiver_entry.text().strip() or "Contact", use_paid
        )
        worker.status.connect(lambda m: self._set_status(m, "yellow"))
        worker.waterfall_status.connect(self._on_waterfall_status)
        worker.reply_generated.connect(self._on_reply_generated)
        worker.error.connect(self._on_worker_error)
        
        from ui.thread_manager import run_in_thread
        run_in_thread(worker, parent_widget=self)

    def _on_waterfall_status(self, msg):
        current_text = self.draft_text.toPlainText()
        self.draft_text.setPlainText(current_text + msg)

    def _on_reply_generated(self, reply, source):
        self.draft_text.setPlainText(reply)
        
        if not reply.startswith("Error"):
            rate_limiter.record_ai_call()
            self._set_status(f"Reply generated ({source}).", "green")
        else:
            self._set_status(f"Generation failed: {reply[:60]}...", "red")

        self.generate_btn.setEnabled(True)

    def send_sms(self):
        phone = self._active_phone
        message = self.draft_text.toPlainText().strip()

        if not phone or not message:
            self._set_status("Error: No contact selected or draft is empty.", "red")
            return

        self._set_status(f"Sending SMS to {phone}...", "yellow")
        self.send_btn.setEnabled(False)

        worker = SendSMSWorker(phone, message)
        worker.sms_sent.connect(self._on_sms_sent)
        worker.error.connect(self._on_worker_error)
        
        from ui.thread_manager import run_in_thread
        run_in_thread(worker, parent_widget=self)

        # Spawn the intent analyzer concurrently
        config = config_manager.load_config()
        api_key = config.get("gemini_api_key")
        contact_name = contact_book.get_display_name(phone, self._contacts)
        timezone = config.get("timezone", "Local")
        
        from ui.qt_workers import AnalyzeIntentWorker
        intent_worker = AnalyzeIntentWorker(api_key, message, contact_name, phone, timezone)
        intent_worker.intent_analyzed.connect(self._on_intent_analyzed)
        run_in_thread(intent_worker, parent_widget=self)

    def _update_schedule_btn_state(self, phone):
        intent_data = self._pending_intents.get(phone)
        self.schedule_btn.setEnabled(True)  # Always ensure button is enabled when updating state
        if not intent_data or intent_data.get("intent_level") == "none":
            self.schedule_btn.setText("🔍 Find Commitments")
            self.schedule_btn.setStyleSheet("background-color: #e0e0e0; color: black;")
        else:
            self.schedule_btn.setText("📅 Schedule Event")
            level = intent_data.get("intent_level")
            if level == "firm":
                self.schedule_btn.setStyleSheet("background-color: #4caf50; color: white; font-weight: bold;")
            elif level == "maybe":
                self.schedule_btn.setStyleSheet("background-color: #ffb300; color: black; font-weight: bold;")

    def _on_schedule_clicked(self):
        phone = self._active_phone
        if not phone:
            self._set_status("Select a contact first.", "yellow")
            return
            
        intent_data = self._pending_intents.get(phone)
        if not intent_data or intent_data.get("intent_level") == "none":
            # State A: Trigger Chat History Analysis
            history = self.history_text.toPlainText().strip()
            if not history or history.startswith("Select a contact") or "Error" in history:
                self._set_status("No valid chat history to analyze.", "yellow")
                return
                
            self.schedule_btn.setEnabled(False)
            self.schedule_btn.setText("Scanning...")
            
            config = config_manager.load_config()
            api_key = config.get("gemini_api_key")
            contact_name = contact_book.get_display_name(phone, self._contacts)
            timezone = config.get("timezone", "Local")
            
            from ui.qt_workers import AnalyzeChatHistoryWorker
            from ui.thread_manager import run_in_thread
            worker = AnalyzeChatHistoryWorker(api_key, history, contact_name, phone, timezone)
            worker.intent_analyzed.connect(self._on_intent_analyzed)
            run_in_thread(worker, parent_widget=self)
        else:
            # State B: Open Dialog
            from ui.calendar_dialog import CalendarReviewDialog
            dialog = CalendarReviewDialog(intent_data, parent=self)
            from PySide6.QtWidgets import QDialog
            if dialog.exec() == QDialog.DialogCode.Accepted:
                updated_intent = dialog.get_updated_intent()
                
                from ui.qt_workers import SyncCalendarWorker
                from ui.thread_manager import run_in_thread
                
                self._set_status("Syncing to calendar...", "yellow")
                sync_worker = SyncCalendarWorker(updated_intent)
                sync_worker.sync_complete.connect(self._on_sync_complete)
                run_in_thread(sync_worker, parent_widget=self)
                
                self._pending_intents[phone] = {"intent_level": "none"}
                self._update_schedule_btn_state(phone)
            else:
                self._set_status("Calendar action ignored.", "yellow")
                self._pending_intents[phone] = {"intent_level": "none"}
                self._update_schedule_btn_state(phone)

    def _on_intent_analyzed(self, phone, intent_data):
        level = intent_data.get("intent_level", "none")
        self._pending_intents[phone] = intent_data
        
        if phone == self._active_phone:
            self._update_schedule_btn_state(phone)
            
        if level == "none":
            self._set_status("No actionable commitment found.", "green")
        else:
            self._set_status(f"Found a '{level}' commitment! Click the schedule button to review.", "green")

    def _on_sync_complete(self, success, message):
        if success and "No action" not in message:
            self._set_status(message, "green")
        elif not success:
            self._set_status(f"Calendar Sync Error: {message}", "yellow")

    def _on_sms_sent(self, success):
        if success:
            self._set_status("SMS Sent Successfully!", "green")
            self.draft_text.clear()
            self.intent_text.clear()
        else:
            self._set_status("Failed to send SMS.", "red")
        self.send_btn.setEnabled(True)

