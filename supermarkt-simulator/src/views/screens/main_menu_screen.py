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

IMAGE_DIR = Path(__file__).parent.parent.parent / "assets" / "images"


class MainMenuScreen(QWidget):
    """Main menu screen displayed at application startup."""

    def __init__(self):
        super().__init__()
        self.on_start_clicked = None
        self.on_settings_clicked = None
        self.on_info_clicked = None
        self.movie = None

        self.setup_ui()

    def setup_ui(self):
        """Setup the main menu UI."""
        # Styles (buttons and labels). Background applied only when GIF missing.
        base_styles = """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: bold;
                min-width: 300px;
                min-height: 60px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
            QLabel {
                color: white;
            }
        """

        fallback_styles = (
            "QWidget { background-color: #1f1f1f; }" + base_styles
        )

        # Apply fallback by default; if GIF loads successfully we'll replace stylesheet.
        self.setStyleSheet(fallback_styles)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setSpacing(30)

        # Title
        title = QLabel("Supermarkt Simulator")
        title_font = QFont()
        title_font.setPointSize(48)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        main_layout.addSpacing(60)

        # Buttons container (centered)
        button_layout = QVBoxLayout()
        button_layout.setSpacing(15)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_start = QPushButton("▶ Simulation starten")
        self.btn_start.clicked.connect(self._on_start)
        button_layout.addWidget(
            self.btn_start, alignment=Qt.AlignmentFlag.AlignCenter
        )

        self.btn_settings = QPushButton("⚙ Einstellungen")
        self.btn_settings.clicked.connect(self._on_settings)
        button_layout.addWidget(
            self.btn_settings, alignment=Qt.AlignmentFlag.AlignCenter
        )

        self.btn_info = QPushButton("ℹ Erklärung")
        self.btn_info.clicked.connect(self._on_info)
        button_layout.addWidget(
            self.btn_info, alignment=Qt.AlignmentFlag.AlignCenter
        )

        main_layout.addLayout(button_layout)
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

    def _on_start(self):
        if self.on_start_clicked:
            self.on_start_clicked()

    def _on_settings(self):
        if self.on_settings_clicked:
            self.on_settings_clicked()

    def _on_info(self):
        if self.on_info_clicked:
            self.on_info_clicked()
