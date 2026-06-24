import os
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPixmap, QColor, QBrush, QFont
from PySide6.QtCore import Qt, Signal, QPoint, QRect

try:
    from timezonefinder import TimezoneFinder
    HAS_TZFINDER = True
except ImportError:
    HAS_TZFINDER = False

class TimezoneMapWidget(QWidget):
    timezoneSelected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        if HAS_TZFINDER:
            self.tf = TimezoneFinder()
        self.setMinimumSize(600, 300)
        
        base_path = os.path.dirname(os.path.abspath(__file__))
        map_path = os.path.join(base_path, "world_map.jpg")
        
        self.map_pixmap = QPixmap(map_path)
        self.selected_point = None
        self.selected_timezone = "Local"
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.zoomed_in = False
        self.zoom_quadrant = (0, 0) # (col, row)

    def set_timezone(self, tz_str):
        self.selected_timezone = tz_str
        self.selected_point = None
        self.update()

    def _get_lat_lon(self, click_x, click_y, scaled_width, scaled_height):
        if not self.zoomed_in:
            lon = (click_x / scaled_width) * 360 - 180
            lat = 90 - (click_y / scaled_height) * 180
        else:
            col, row = self.zoom_quadrant
            lon = -180 + col * 180 + (click_x / scaled_width) * 180
            lat = 90 - row * 90 - (click_y / scaled_height) * 90
        return lat, lon

    def _get_px(self, lat, lon, scaled_width, scaled_height):
        if not self.zoomed_in:
            px_x = (lon + 180) / 360 * scaled_width
            px_y = (90 - lat) / 180 * scaled_height
            return px_x, px_y
        else:
            col, row = self.zoom_quadrant
            q_col = 0 if lon <= 0 else 1
            q_row = 0 if lat >= 0 else 1
            if q_col != col or q_row != row:
                return None, None
            
            px_x = (lon - (-180 + col * 180)) / 180 * scaled_width
            px_y = (90 - row * 90 - lat) / 90 * scaled_height
            return px_x, px_y

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.map_pixmap.isNull():
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Map image not found")
            return
            
        rect = self.rect()
        if not self.zoomed_in:
            src_rect = self.map_pixmap.rect()
        else:
            w = self.map_pixmap.width() // 2
            h = self.map_pixmap.height() // 2
            col, row = self.zoom_quadrant
            src_rect = QRect(col * w, row * h, w, h)
            
        sub_pixmap = self.map_pixmap.copy(src_rect)
        scaled_pixmap = sub_pixmap.scaled(rect.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        x = (rect.width() - scaled_pixmap.width()) // 2
        y = (rect.height() - scaled_pixmap.height()) // 2
        
        painter.drawPixmap(x, y, scaled_pixmap)
        
        if self.selected_point is not None:
            lat, lon = self.selected_point
            px_x, px_y = self._get_px(lat, lon, scaled_pixmap.width(), scaled_pixmap.height())
            
            if px_x is not None and px_y is not None:
                dot_x = x + px_x
                dot_y = y + px_y
                
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(255, 0, 0, 200)))
                painter.drawEllipse(QPoint(int(dot_x), int(dot_y)), 6, 6)

                painter.setPen(QColor(0, 0, 0))
                painter.drawText(int(dot_x) + 10, int(dot_y) + 5, self.selected_timezone)

        painter.setPen(QColor(50, 50, 50, 200))
        font = QFont()
        font.setBold(True)
        painter.setFont(font)
        if not self.zoomed_in:
            painter.drawText(10, 20, "Click a quadrant to zoom in")
        else:
            painter.drawText(10, 20, "Right-click to zoom out")

    def mousePressEvent(self, event):
        if not HAS_TZFINDER:
            return

        if event.button() == Qt.MouseButton.RightButton:
            if self.zoomed_in:
                self.zoomed_in = False
                self.update()
            return

        rect = self.rect()
        
        if not self.zoomed_in:
            src_rect = self.map_pixmap.rect()
        else:
            w = self.map_pixmap.width() // 2
            h = self.map_pixmap.height() // 2
            col, row = self.zoom_quadrant
            src_rect = QRect(col * w, row * h, w, h)
            
        sub_pixmap = self.map_pixmap.copy(src_rect)
        scaled_pixmap = sub_pixmap.scaled(rect.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        x_offset = (rect.width() - scaled_pixmap.width()) // 2
        y_offset = (rect.height() - scaled_pixmap.height()) // 2
        
        click_x = event.position().x() - x_offset
        click_y = event.position().y() - y_offset
        
        if 0 <= click_x <= scaled_pixmap.width() and 0 <= click_y <= scaled_pixmap.height():
            if not self.zoomed_in:
                col = 0 if click_x < scaled_pixmap.width() / 2 else 1
                row = 0 if click_y < scaled_pixmap.height() / 2 else 1
                self.zoomed_in = True
                self.zoom_quadrant = (col, row)
                self.update()
            else:
                lat, lon = self._get_lat_lon(click_x, click_y, scaled_pixmap.width(), scaled_pixmap.height())
                tz_str = self.tf.timezone_at(lng=lon, lat=lat)
                if tz_str:
                    self.selected_point = (lat, lon)
                    self.selected_timezone = tz_str
                    self.timezoneSelected.emit(tz_str)
                    self.update()
