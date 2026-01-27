"""Settings Screen for application configuration."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class SettingsScreen(QWidget):
    """Settings screen for language and other preferences."""
    
    settings_changed = pyqtSignal(dict)  # Emits settings dict when saved
    back_requested = pyqtSignal()  # Signal to go back to main menu
    
    def __init__(self, settings=None, translator=None):
        super().__init__()
        self.settings = settings or {}
        self.translator = translator
        self.pending_settings = {}
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the settings UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setSpacing(20)
        
        # Title
        title = QLabel("Einstellungen")
        title_font = QFont()
        title_font.setPointSize(32)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)
        
        # Settings Group
        settings_group = QGroupBox("Spracheinstellungen")
        form_layout = QFormLayout(settings_group)
        
        # Language dropdown
        lang_label = QLabel("Sprache:")
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["🇩🇪 Deutsch", "🇺🇸 English"])
        
        # Set current language
        current_lang = self.settings.get("language", "de")
        index = 0 if current_lang == "de" else 1
        self.lang_combo.setCurrentIndex(index)
        
        form_layout.addRow(lang_label, self.lang_combo)
        main_layout.addWidget(settings_group)
        
        main_layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.btn_save = QPushButton("💾 Speichern")
        self.btn_save.clicked.connect(self._on_save)
        button_layout.addWidget(self.btn_save)
        
        self.btn_cancel = QPushButton("✕ Abbrechen")
        self.btn_cancel.clicked.connect(self.back_requested.emit)
        button_layout.addWidget(self.btn_cancel)
        
        main_layout.addLayout(button_layout)
        
        self.setStyleSheet("""
            SettingsScreen {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333333;
            }
            QGroupBox {
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 10px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            QComboBox {
                background-color: white;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 5px;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
    
    def _on_save(self):
        """Save settings and emit signal."""
        lang_text = self.lang_combo.currentText()
        language = "de" if "Deutsch" in lang_text else "en"
        
        settings = {"language": language}
        self.settings_changed.emit(settings)
        self.back_requested.emit()
    
    def set_translator(self, translator):
        """Update translator reference."""
        self.translator = translator
