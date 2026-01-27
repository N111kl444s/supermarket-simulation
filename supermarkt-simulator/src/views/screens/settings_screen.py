"""Settings Screen for application configuration."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from config import COLOR_BG_MAIN, COLOR_ACCENT, COLOR_TEXT_MAIN, COLOR_BORDER


class SettingsScreen(QWidget):
    """Settings screen for language and other preferences."""
    
    settings_changed = pyqtSignal(dict)  # Emits settings dict when saved
    back_requested = pyqtSignal()  # Signal to go back to main menu
    
    def __init__(self, settings=None, translator=None):
        super().__init__()
        self.settings = settings or {}
        self.translator = translator
        self.original_language = None  # Track original language for cancel
        self.pending_settings = {}
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the settings UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setSpacing(20)
        
        # Title
        self.title_label = QLabel()
        title_font = QFont()
        title_font.setPointSize(32)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        main_layout.addWidget(self.title_label)
        
        # Settings Group
        self.settings_group = QGroupBox()
        form_layout = QFormLayout(self.settings_group)
        
        # Language dropdown
        self.lang_label = QLabel()
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["🇩🇪 Deutsch", "🇺🇸 English"])
        
        # Set current language
        current_lang = self.settings.get("language", "de")
        index = 0 if current_lang == "de" else 1
        self.lang_combo.setCurrentIndex(index)
        
        # Connect language change for live preview
        self.lang_combo.currentIndexChanged.connect(self._on_language_preview)
        
        form_layout.addRow(self.lang_label, self.lang_combo)
        main_layout.addWidget(self.settings_group)
        
        main_layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.btn_save = QPushButton()
        self.btn_save.clicked.connect(self._on_save)
        button_layout.addWidget(self.btn_save)
        
        self.btn_cancel = QPushButton()
        self.btn_cancel.clicked.connect(self._on_cancel)
        button_layout.addWidget(self.btn_cancel)
        
        main_layout.addLayout(button_layout)
        
        # Update texts with translations
        self.update_translations()
        
        # Get colors from config
        bg_main = COLOR_BG_MAIN.name()
        accent = COLOR_ACCENT.name()
        border = COLOR_BORDER.name()
        text_main = COLOR_TEXT_MAIN.name()
        
        self.setStyleSheet(f"""
            SettingsScreen {{
                background-color: {bg_main};
            }}
            QLabel {{
                color: {text_main};
            }}
            QGroupBox {{
                color: {accent};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 10px;
                margin-top: 10px;
                font-weight: 700;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                background-color: {bg_main};
            }}
            QComboBox {{
                background-color: #FFFFFF;
                color: {text_main};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 5px;
                min-height: 38px;
                font-weight: bold;
            }}
            QPushButton {{
                background-color: #FFFFFF;
                color: {text_main};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: 700;
                font-size: 14px;
                min-height: 38px;
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
        """)
    
    def _on_language_preview(self):
        """Preview language change without saving."""
        lang_text = self.lang_combo.currentText()
        language = "de" if "Deutsch" in lang_text else "en"
        
        # Temporarily change language for preview
        if self.translator:
            self.translator.set_language(language)
    
    def _on_save(self):
        """Save settings and emit signal."""
        lang_text = self.lang_combo.currentText()
        language = "de" if "Deutsch" in lang_text else "en"
        
        settings = {"language": language}
        self.settings_changed.emit(settings)
        self.back_requested.emit()
    
    def _on_cancel(self):
        """Cancel and restore original language."""
        # Restore original language if it was changed
        if self.original_language and self.translator:
            self.translator.set_language(self.original_language)
        self.back_requested.emit()
    
    def showEvent(self, event):
        """Store original language when screen is shown."""
        super().showEvent(event)
        if self.translator:
            self.original_language = self.translator.get_current_language()
    
    def update_translations(self):
        """Update UI texts with current translations."""
        if self.translator:
            self.title_label.setText(self.translator.get("settings.title", "Einstellungen"))
            self.settings_group.setTitle(self.translator.get("settings.language_group", "Spracheinstellungen"))
            self.lang_label.setText(self.translator.get("settings.language_label", "Sprache:"))
            self.btn_save.setText(self.translator.get("settings.save", "Speichern"))
            self.btn_cancel.setText(self.translator.get("settings.cancel", "Abbrechen"))
        else:
            self.title_label.setText("Einstellungen")
            self.settings_group.setTitle("Spracheinstellungen")
            self.lang_label.setText("Sprache:")
            self.btn_save.setText("Speichern")
            self.btn_cancel.setText("Abbrechen")
    
    def set_translator(self, translator):
        """Update translator reference."""
        self.translator = translator
