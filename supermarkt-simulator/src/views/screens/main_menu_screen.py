"""Main Menu Screen with animated GIF background."""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QStyleOptionButton,
    QStylePainter,
    QStyle,
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QPixmap, QFont, QFontMetrics
from pathlib import Path
from config import IMAGE_DIR, COLOR_BG_MAIN, COLOR_ACCENT, COLOR_TEXT_MAIN, COLOR_BORDER


class LoadingButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._loading_icon = None
        self._loading_icon_size = QSize(18, 18)
        self._loading_icon_spacing = 8

    def set_loading_icon(self, icon=None, size=None, spacing=None):
        self._loading_icon = icon
        if size is not None:
            self._loading_icon_size = size
        if spacing is not None:
            self._loading_icon_spacing = spacing
        self.update()

    def paintEvent(self, event):
        painter = QStylePainter(self)
        opt = QStyleOptionButton()
        opt.initFrom(self)
        opt.text = ""
        painter.drawControl(QStyle.ControlElement.CE_PushButton, opt)

        rect = self.contentsRect()
        text = self.text()
        fm = QFontMetrics(self.font())

        if self._loading_icon:
            size = self._loading_icon_size
            spacing = self._loading_icon_spacing
            text_width = fm.horizontalAdvance(text)
            total_width = size.width() * 2 + spacing * 2 + text_width
            start_x = rect.center().x() - total_width / 2
            y = rect.center().y() - size.height() / 2

            pixmap = self._loading_icon.pixmap(size)
            painter.drawPixmap(int(start_x), int(y), pixmap)
            text_x = start_x + size.width() + spacing
            painter.drawText(
                int(text_x),
                int(rect.center().y() + fm.ascent() / 2),
                text,
            )
            right_x = text_x + text_width + spacing
            painter.drawPixmap(int(right_x), int(y), pixmap)
        else:
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)


class MainMenuScreen(QWidget):
    """Main menu screen displayed at application startup."""

    def __init__(self, translator=None):
        super().__init__()
        self.on_start_clicked = None
        self.on_settings_clicked = None
        self.on_info_clicked = None
        self.on_exit_clicked = None
        self.translator = translator
        self.movie = None
        self._loading_timer = None
        self._loading_step = 0
        self._base_start_text = ""
        self._loading_text = ""
        self._base_start_font = None

        self.setup_ui()

    def setup_ui(self):
        """Setup the main menu UI."""
        # Get colors from config
        bg_main = COLOR_BG_MAIN.name()
        accent = COLOR_ACCENT.name()
        border = COLOR_BORDER.name()
        text_main = COLOR_TEXT_MAIN.name()
        
        # Styles matching application design
        base_styles = f"""
            QPushButton {{
                background-color: #FFFFFF;
                border: 1px solid {border};
                border-radius: 6px;
                padding: 0px 24px;
                color: {text_main};
                font-weight: 700;
                font-size: 16px;
                min-height: 50px;
                min-width: 300px;
            }}
            QPushButton:hover {{
                background-color: #F8FAFC;
                border-color: {accent};
                color: {accent};
            }}
            QPushButton:pressed {{
                background-color: {accent};
                color: #FFFFFF;
            }}
            QPushButton#BtnStart[clicked="true"] {{
                background-color: {accent};
                color: #FFFFFF;
            }}
        """

        fallback_styles = (
            f"QWidget {{ background-color: {bg_main}; }}" + base_styles
        )

        # Apply fallback by default; if GIF loads successfully we'll replace stylesheet.
        self.setStyleSheet(fallback_styles)

        # Main layout - center everything
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setSpacing(0)
        
        # Add stretch at top to center content vertically
        main_layout.addStretch()

        # Buttons container (centered)
        button_layout = QVBoxLayout()
        button_layout.setSpacing(15)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_start = LoadingButton()
        self.btn_start.setObjectName("BtnStart")
        self.btn_start.clicked.connect(self._on_start)
        button_layout.addWidget(
            self.btn_start, alignment=Qt.AlignmentFlag.AlignCenter
        )

        self.btn_info = QPushButton()
        self.btn_info.clicked.connect(self._on_info)
        button_layout.addWidget(
            self.btn_info, alignment=Qt.AlignmentFlag.AlignCenter
        )

        self.btn_settings = QPushButton()
        self.btn_settings.clicked.connect(self._on_settings)
        button_layout.addWidget(
            self.btn_settings, alignment=Qt.AlignmentFlag.AlignCenter
        )

        self.btn_exit = QPushButton()
        self.btn_exit.clicked.connect(self._on_exit)
        button_layout.addWidget(
            self.btn_exit, alignment=Qt.AlignmentFlag.AlignCenter
        )

        main_layout.addLayout(button_layout)
        
        # Update button texts with translations
        self.update_translations()
        
        # Add stretch at bottom to center content vertically
        main_layout.addStretch()

        # Try to load a static background image and display it as a full-widget background.
        # Prefer PNG/JPG; if only GIF exists, use its first frame as a pixmap.
        candidates = [
            "menu_background.png",
            "menu_background.jpg",
            "menu_background.jpeg",
            "menu_background.gif",
        ]
        img_path = None
        for name in candidates:
            p = IMAGE_DIR / name
            if p.exists():
                img_path = p
                break

        if img_path:
            try:
                self._bg_pixmap = QPixmap(str(img_path))
                if not self._bg_pixmap.isNull():
                    self._bg_label = QLabel(self)
                    self._bg_label.setObjectName("menu_bg_label")
                    self._bg_label.setScaledContents(False)
                    self._bg_label.setAttribute(
                        Qt.WidgetAttribute.WA_TransparentForMouseEvents
                    )
                    # Apply base styles so the pixmap is visible
                    self.setStyleSheet(base_styles)
                    # initial placement
                    self._update_bg_pixmap(self.width(), self.height())
                    self._bg_label.lower()
            except Exception as e:
                print(f"Error loading background image: {e}")

    def _update_bg_pixmap(self, w, h):
        if (
            hasattr(self, "_bg_label")
            and hasattr(self, "_bg_pixmap")
            and not self._bg_pixmap.isNull()
        ):
            scaled = self._bg_pixmap.scaled(
                w,
                h,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._bg_label.setPixmap(scaled)
            self._bg_label.setGeometry(0, 0, w, h)

    def resizeEvent(self, event):
        sz = event.size()
        if hasattr(self, "_bg_pixmap") and not self._bg_pixmap.isNull():
            try:
                self._update_bg_pixmap(sz.width(), sz.height())
            except Exception:
                pass
        super().resizeEvent(event)

    def update_translations(self):
        """Update button texts with current translations."""
        if self.translator:
            self.btn_start.setText(self.translator.get("menu.start_simulation", "Simulation starten"))
            self.btn_info.setText(self.translator.get("menu.info", "Erklärung"))
            self.btn_settings.setText(self.translator.get("menu.settings", "Einstellungen"))
            self.btn_exit.setText(self.translator.get("menu.exit", "Beenden"))
            self.btn_start.setToolTip(
                self.translator.get("tooltips.button_menu_start", "Simulation starten")
            )
            self.btn_info.setToolTip(
                self.translator.get("tooltips.button_menu_info", "Info anzeigen")
            )
            self.btn_settings.setToolTip(
                self.translator.get("tooltips.button_menu_settings", "Einstellungen öffnen")
            )
            self.btn_exit.setToolTip(
                self.translator.get("tooltips.button_menu_exit", "Programm beenden")
            )
        else:
            self.btn_start.setText("Simulation starten")
            self.btn_info.setText("Erklärung")
            self.btn_settings.setText("Einstellungen")
            self.btn_exit.setText("Beenden")
            self.btn_start.setToolTip("Simulation starten")
            self.btn_info.setToolTip("Info anzeigen")
            self.btn_settings.setToolTip("Einstellungen öffnen")
            self.btn_exit.setToolTip("Programm beenden")
        self._base_start_text = self.btn_start.text()

    def _on_start(self):
        if self.on_start_clicked:
            self._flash_start_click()
            QTimer.singleShot(180, self._start_loading)
            QTimer.singleShot(200, self.on_start_clicked)

    def _flash_start_click(self):
        self.btn_start.setProperty("clicked", True)
        self.btn_start.style().unpolish(self.btn_start)
        self.btn_start.style().polish(self.btn_start)
        QTimer.singleShot(150, self._clear_start_click)

    def _clear_start_click(self):
        self.btn_start.setProperty("clicked", False)
        self.btn_start.style().unpolish(self.btn_start)
        self.btn_start.style().polish(self.btn_start)

    def _on_settings(self):
        if self.on_settings_clicked:
            self.on_settings_clicked()

    def _on_info(self):
        if self.on_info_clicked:
            self.on_info_clicked()
    
    def _on_exit(self):
        if self.on_exit_clicked:
            self.on_exit_clicked()

    def showEvent(self, event):
        self._stop_loading()
        super().showEvent(event)

    def _start_loading(self):
        if self._loading_timer:
            return
        if not self._base_start_text:
            self._base_start_text = self.btn_start.text()
        if self._base_start_font is None:
            self._base_start_font = self.btn_start.font()
        loading_text = (
            self.translator.get("menu.start_loading", "Simulation wird vorbereitet")
            if self.translator
            else "Simulation wird vorbereitet"
        )
        self._loading_text = loading_text
        loading_icon = self.style().standardIcon(
            QStyle.StandardPixmap.SP_BrowserReload
        )
        if isinstance(self.btn_start, LoadingButton):
            self.btn_start.set_loading_icon(loading_icon, QSize(18, 18), 8)
        self.btn_start.setEnabled(False)
        self.btn_info.setEnabled(False)
        self.btn_settings.setEnabled(False)
        self.btn_exit.setEnabled(False)

        self._loading_step = 0
        self._loading_timer = QTimer(self)
        self._loading_timer.setInterval(350)
        self._loading_timer.timeout.connect(self._tick_loading)
        self._loading_timer.start()
        self._tick_loading()

    def _tick_loading(self):
        dots = "." * (self._loading_step % 4)
        fm = QFontMetrics(self.btn_start.font())
        text_core = f"{self._loading_text}{dots}"
        available = max(0, self.btn_start.contentsRect().width() - 76)
        elided = fm.elidedText(text_core, Qt.TextElideMode.ElideRight, available)
        self.btn_start.setText(elided)
        self._loading_step += 1

    def _stop_loading(self):
        if self._loading_timer:
            self._loading_timer.stop()
            self._loading_timer.deleteLater()
            self._loading_timer = None
        self.btn_start.setEnabled(True)
        self.btn_info.setEnabled(True)
        self.btn_settings.setEnabled(True)
        self.btn_exit.setEnabled(True)
        if self._base_start_text:
            self.btn_start.setText(self._base_start_text)
        if self._base_start_font is not None:
            self.btn_start.setFont(self._base_start_font)
        if isinstance(self.btn_start, LoadingButton):
            self.btn_start.set_loading_icon(None)
        self._loading_text = ""
