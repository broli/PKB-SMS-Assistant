from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QScrollArea, QWidget)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from modules import contact_book

class ImportPreviewWindow(QDialog):
    import_confirmed = Signal(bool)

    def __init__(self, plan, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Preview & Confirmation")
        self.resize(500, 600)
        self.setModal(True)
        
        self.plan = plan
        
        self.main_layout = QVBoxLayout(self)

        # Header
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        self.header = QLabel("📋 Contact Import Summary")
        self.header.setFont(header_font)
        self.header.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.header)
        self.main_layout.addSpacing(20)

        # Stats
        new_count = len(plan.get("new", {}))
        upd_count = len(plan.get("update", {}))
        pre_count = len(plan.get("preserve", {}))
        total     = plan.get("total_scanned", 0)

        total_font = QFont()
        total_font.setBold(True)
        total_lbl = QLabel(f"Total lines scanned: {total}")
        total_lbl.setFont(total_font)
        self.main_layout.addWidget(total_lbl)
        
        new_lbl = QLabel(f"✨ New contacts to add: {new_count}")
        new_lbl.setStyleSheet("color: #2da44e;")
        self.main_layout.addWidget(new_lbl)
        
        upd_lbl = QLabel(f"🔄 Names to update (no nickname): {upd_count}")
        upd_lbl.setStyleSheet("color: #d4ac0d;")
        self.main_layout.addWidget(upd_lbl)
        
        pre_lbl = QLabel(f"🛡️ Preserved (existing nickname): {pre_count}")
        pre_lbl.setStyleSheet("color: gray;")
        self.main_layout.addWidget(pre_lbl)

        # Details list
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.main_layout.addWidget(self.scroll_area, 1)
        
        self._populate_details()

        # Footer Buttons
        self.btn_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        self.btn_layout.addWidget(self.cancel_btn)
        
        self.confirm_btn = QPushButton("Confirm & Import")
        self.confirm_btn.setStyleSheet("background-color: #2da44e; color: white;")
        self.confirm_btn.clicked.connect(self._do_confirm)
        self.btn_layout.addWidget(self.confirm_btn)
        
        self.main_layout.addLayout(self.btn_layout)

    def _populate_details(self):
        font_bold = QFont()
        font_bold.setPointSize(10)
        font_bold.setBold(True)
        font_small = QFont()
        font_small.setPointSize(9)

        if self.plan["new"]:
            lbl = QLabel("--- NEW ENTRIES ---")
            lbl.setFont(font_bold)
            self.scroll_layout.addWidget(lbl)
            
            for p, n in list(self.plan["new"].items())[:20]:
                item = QLabel(f"+ {n} ({p})")
                item.setFont(font_small)
                self.scroll_layout.addWidget(item)
                
            if len(self.plan["new"]) > 20:
                more = QLabel(f"... and {len(self.plan['new'])-20} more")
                font_italic = QFont(font_small)
                font_italic.setItalic(True)
                more.setFont(font_italic)
                self.scroll_layout.addWidget(more)
                
        if self.plan["update"]:
            lbl = QLabel("\n--- UPDATING NAMES ---")
            lbl.setFont(font_bold)
            self.scroll_layout.addWidget(lbl)
            
            for p, d in list(self.plan["update"].items())[:20]:
                item = QLabel(f"~ {p}: {d['old'] or 'None'} -> {d['new']}")
                item.setFont(font_small)
                self.scroll_layout.addWidget(item)
                
        self.scroll_layout.addStretch()

    def _do_confirm(self):
        success = contact_book.apply_import_plan(self.plan)
        self.import_confirmed.emit(success)
        self.accept()
