"""Main Menu Screen with animated GIF background."""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QFont
from pathlib import Path
from config import IMAGE_DIR, COLOR_BG_MAIN, COLOR_ACCENT, COLOR_TEXT_MAIN, COLOR_BORDER


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

        self.btn_start = QPushButton()
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
        else:
            self.btn_start.setText("Simulation starten")
            self.btn_info.setText("Erklärung")
            self.btn_settings.setText("Einstellungen")
            self.btn_exit.setText("Beenden")

    def _on_start(self):
        if self.on_start_clicked:
            self.on_start_clicked()

    def _on_settings(self):
        if self.on_settings_clicked:
            self.on_settings_clicked()

    def _on_info(self):
        if self.on_info_clicked:
            self.on_info_clicked()
    
    def _on_exit(self):
        if self.on_exit_clicked:
            self.on_exit_clicked()
