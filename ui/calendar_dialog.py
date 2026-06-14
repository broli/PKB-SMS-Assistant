from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QComboBox, QDateTimeEdit, QPushButton,
                               QFormLayout)
from PySide6.QtCore import Qt, QDateTime
import datetime

class CalendarReviewDialog(QDialog):
    def __init__(self, intent_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Review Calendar Action")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self.intent_data = intent_data
        self.timezone = intent_data.get("_timezone", "Local")
        
        self.main_layout = QVBoxLayout(self)
        
        self.form_layout = QFormLayout()
        
        # Summary
        self.summary_input = QLineEdit()
        self.summary_input.setText(intent_data.get("summary", ""))
        self.form_layout.addRow("Summary:", self.summary_input)
        
        # Type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["event", "task"])
        
        initial_type = intent_data.get("type", "event").lower()
        if initial_type == "task":
            self.type_combo.setCurrentText("task")
        else:
            self.type_combo.setCurrentText("event")
            
        self.form_layout.addRow("Type:", self.type_combo)
        
        # Start Time / Due Date
        self.start_date_edit = QDateTimeEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.end_date_edit = QDateTimeEdit()
        self.end_date_edit.setCalendarPopup(True)
        
        self._init_dates(initial_type, intent_data)
        
        self.current_duration = self.start_date_edit.dateTime().secsTo(self.end_date_edit.dateTime())
        self.start_date_edit.dateTimeChanged.connect(self._on_start_date_changed)
        self.end_date_edit.dateTimeChanged.connect(self._on_end_date_changed)
        
        self.start_label = QLabel("Start Time:")
        self.end_label = QLabel("End Time:")
        
        self.form_layout.addRow(self.start_label, self.start_date_edit)
        self.form_layout.addRow(self.end_label, self.end_date_edit)
        
        self.main_layout.addLayout(self.form_layout)
        
        # Display explicit timezone
        tz_label = QLabel(f"<i>Times will be saved using timezone: <b>{self.timezone}</b></i>")
        tz_label.setStyleSheet("color: gray;")
        tz_label.setWordWrap(True)
        self.main_layout.addWidget(tz_label)
        
        # Update visibility based on type
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        self._on_type_changed(self.type_combo.currentText())
        
        # Buttons
        self.btn_layout = QHBoxLayout()
        self.ignore_btn = QPushButton("Ignore")
        self.ignore_btn.clicked.connect(self.reject)
        
        self.add_btn = QPushButton("Add")
        self.add_btn.setStyleSheet("background-color: #2da44e; color: white;")
        self.add_btn.clicked.connect(self.accept)
        
        self.btn_layout.addWidget(self.ignore_btn)
        self.btn_layout.addWidget(self.add_btn)
        
        self.main_layout.addLayout(self.btn_layout)

    def _init_dates(self, type_str, intent_data):
        now = QDateTime.currentDateTime()
        
        if type_str == "event":
            start_str = intent_data.get("start_time")
            if start_str:
                try:
                    dt = datetime.datetime.fromisoformat(start_str.replace('Z', ''))
                    qdt = QDateTime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
                    self.start_date_edit.setDateTime(qdt)
                except ValueError:
                    self.start_date_edit.setDateTime(now)
            else:
                self.start_date_edit.setDateTime(now)
                
            self.end_date_edit.setDateTime(self.start_date_edit.dateTime().addSecs(15 * 60))
        else:
            due_str = intent_data.get("due_date")
            if due_str:
                try:
                    dt = datetime.datetime.fromisoformat(due_str.replace('Z', ''))
                    qdt = QDateTime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
                    self.start_date_edit.setDateTime(qdt)
                except ValueError:
                    self.start_date_edit.setDateTime(now)
            else:
                self.start_date_edit.setDateTime(now)
            
            self.end_date_edit.setDateTime(self.start_date_edit.dateTime().addSecs(15 * 60))

    def _on_type_changed(self, text):
        if text == "event":
            self.start_label.setText("Start Time:")
            self.end_label.show()
            self.end_date_edit.show()
        else:
            self.start_label.setText("Due Date:")
            self.end_label.hide()
            self.end_date_edit.hide()

    def _on_start_date_changed(self, new_dt):
        self.end_date_edit.blockSignals(True)
        self.end_date_edit.setDateTime(new_dt.addSecs(self.current_duration))
        self.end_date_edit.blockSignals(False)

    def _on_end_date_changed(self, new_dt):
        self.current_duration = self.start_date_edit.dateTime().secsTo(new_dt)

    def get_updated_intent(self):
        start_dt = self.start_date_edit.dateTime().toPython()
        end_dt = self.end_date_edit.dateTime().toPython()
        return {
            "intent_level": self.intent_data.get("intent_level", "firm"),
            "type": self.type_combo.currentText(),
            "summary": self.summary_input.text(),
            "start_time": start_dt.isoformat(),  # type: ignore
            "end_time": end_dt.isoformat() if self.type_combo.currentText() == "event" else None,  # type: ignore
            "due_date": start_dt.isoformat() if self.type_combo.currentText() == "task" else None,  # type: ignore
            "_timezone": self.timezone
        }
