"""Settings Screen for application configuration."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QGroupBox, QFormLayout, QDoubleSpinBox
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
        title_font.setPixelSize(32)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        main_layout.addWidget(self.title_label)
        
        # === ALLGEMEIN GROUP ===
        self.general_group = QGroupBox()
        general_layout = QFormLayout(self.general_group)
        
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
        
        general_layout.addRow(self.lang_label, self.lang_combo)
        main_layout.addWidget(self.general_group)

        # === STATISTIKEN GROUP ===
        self.statistics_group = QGroupBox()
        stats_main_layout = QVBoxLayout(self.statistics_group)
        
        # Satisfaction Settings (Zufriedenheit)
        self.satisfaction_box = QGroupBox()
        sat_layout = QFormLayout(self.satisfaction_box)
        
        self.sat_store_label = QLabel()
        self.sat_queue_label = QLabel()
        self.sat_store_spin = QDoubleSpinBox()
        self.sat_store_spin.setRange(1.0, 240.0)
        self.sat_store_spin.setSingleStep(1.0)
        self.sat_store_spin.setSuffix(" min")
        self.sat_queue_spin = QDoubleSpinBox()
        self.sat_queue_spin.setRange(0.5, 120.0)
        self.sat_queue_spin.setSingleStep(0.5)
        self.sat_queue_spin.setSuffix(" min")
        self.sat_store_spin.setValue(
            float(self.settings.get("satisfaction_store_target_min", 20.0))
        )
        self.sat_queue_spin.setValue(
            float(self.settings.get("satisfaction_queue_target_min", 5.0))
        )
        sat_layout.addRow(self.sat_store_label, self.sat_store_spin)
        sat_layout.addRow(self.sat_queue_label, self.sat_queue_spin)
        stats_main_layout.addWidget(self.satisfaction_box)
        
        # KPI: Überzeit
        self.overtime_box = QGroupBox()
        overtime_layout = QFormLayout(self.overtime_box)
        
        self.kpi_overtime_good_label = QLabel()
        self.kpi_overtime_warning_label = QLabel()
        self.kpi_overtime_good_spin = QDoubleSpinBox()
        self.kpi_overtime_good_spin.setRange(1.0, 60.0)
        self.kpi_overtime_good_spin.setSingleStep(1.0)
        self.kpi_overtime_good_spin.setSuffix(" min")
        self.kpi_overtime_good_spin.setValue(
            float(self.settings.get("kpi_overtime_good_max", 5.0))
        )
        self.kpi_overtime_warning_spin = QDoubleSpinBox()
        self.kpi_overtime_warning_spin.setRange(1.0, 120.0)
        self.kpi_overtime_warning_spin.setSingleStep(1.0)
        self.kpi_overtime_warning_spin.setSuffix(" min")
        self.kpi_overtime_warning_spin.setValue(
            float(self.settings.get("kpi_overtime_warning_max", 15.0))
        )
        overtime_layout.addRow(self.kpi_overtime_good_label, self.kpi_overtime_good_spin)
        overtime_layout.addRow(self.kpi_overtime_warning_label, self.kpi_overtime_warning_spin)
        stats_main_layout.addWidget(self.overtime_box)
        
        # KPI: Wartezeit
        self.wait_box = QGroupBox()
        wait_layout = QFormLayout(self.wait_box)
        
        self.kpi_wait_good_label = QLabel()
        self.kpi_wait_warning_label = QLabel()
        self.kpi_wait_good_spin = QDoubleSpinBox()
        self.kpi_wait_good_spin.setRange(1.0, 30.0)
        self.kpi_wait_good_spin.setSingleStep(0.5)
        self.kpi_wait_good_spin.setSuffix(" min")
        self.kpi_wait_good_spin.setValue(
            float(self.settings.get("kpi_wait_time_good_max", 5.0))
        )
        self.kpi_wait_warning_spin = QDoubleSpinBox()
        self.kpi_wait_warning_spin.setRange(1.0, 60.0)
        self.kpi_wait_warning_spin.setSingleStep(0.5)
        self.kpi_wait_warning_spin.setSuffix(" min")
        self.kpi_wait_warning_spin.setValue(
            float(self.settings.get("kpi_wait_time_warning_max", 8.0))
        )
        wait_layout.addRow(self.kpi_wait_good_label, self.kpi_wait_good_spin)
        wait_layout.addRow(self.kpi_wait_warning_label, self.kpi_wait_warning_spin)
        stats_main_layout.addWidget(self.wait_box)
        
        # KPI: Zufriedenheit
        self.kpi_sat_box = QGroupBox()
        kpi_sat_layout = QFormLayout(self.kpi_sat_box)
        
        self.kpi_satisfaction_good_label = QLabel()
        self.kpi_satisfaction_warning_label = QLabel()
        self.kpi_satisfaction_good_spin = QDoubleSpinBox()
        self.kpi_satisfaction_good_spin.setRange(0.0, 100.0)
        self.kpi_satisfaction_good_spin.setSingleStep(1.0)
        self.kpi_satisfaction_good_spin.setSuffix(" %")
        self.kpi_satisfaction_good_spin.setValue(
            float(self.settings.get("kpi_satisfaction_good_min", 75.0))
        )
        self.kpi_satisfaction_warning_spin = QDoubleSpinBox()
        self.kpi_satisfaction_warning_spin.setRange(0.0, 100.0)
        self.kpi_satisfaction_warning_spin.setSingleStep(1.0)
        self.kpi_satisfaction_warning_spin.setSuffix(" %")
        self.kpi_satisfaction_warning_spin.setValue(
            float(self.settings.get("kpi_satisfaction_warning_min", 50.0))
        )
        kpi_sat_layout.addRow(self.kpi_satisfaction_good_label, self.kpi_satisfaction_good_spin)
        kpi_sat_layout.addRow(self.kpi_satisfaction_warning_label, self.kpi_satisfaction_warning_spin)
        stats_main_layout.addWidget(self.kpi_sat_box)
        
        main_layout.addWidget(self.statistics_group)
        
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

        settings = {
            "language": language,
            "satisfaction_store_target_min": self.sat_store_spin.value(),
            "satisfaction_queue_target_min": self.sat_queue_spin.value(),
            "kpi_overtime_good_max": self.kpi_overtime_good_spin.value(),
            "kpi_overtime_warning_max": self.kpi_overtime_warning_spin.value(),
            "kpi_wait_time_good_max": self.kpi_wait_good_spin.value(),
            "kpi_wait_time_warning_max": self.kpi_wait_warning_spin.value(),
            "kpi_satisfaction_good_min": self.kpi_satisfaction_good_spin.value(),
            "kpi_satisfaction_warning_min": self.kpi_satisfaction_warning_spin.value(),
        }
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
            
            # General Group
            self.general_group.setTitle(self.translator.get("settings.general_group", "Allgemein"))
            self.lang_label.setText(self.translator.get("settings.language_label", "Sprache:"))
            
            # Statistics Group
            self.statistics_group.setTitle(
                self.translator.get("settings.statistics_group", "Statistiken")
            )
            self.satisfaction_box.setTitle(
                self.translator.get("settings.satisfaction_box", "Zufriedenheit")
            )
            self.sat_store_label.setText(
                self.translator.get(
                    "settings.satisfaction_store",
                    "Verweildauer Grenzwert:",
                )
            )
            self.sat_queue_label.setText(
                self.translator.get(
                    "settings.satisfaction_queue",
                    "Wartezeit Grenzwert:",
                )
            )
            
            # KPI Thresholds
            self.overtime_box.setTitle(
                self.translator.get("settings.kpi_overtime_box", "KPI: Überzeit")
            )
            self.kpi_overtime_good_label.setText(
                self.translator.get("settings.kpi_overtime_good", "Gut (max):")
            )
            self.kpi_overtime_warning_label.setText(
                self.translator.get("settings.kpi_overtime_warning", "Warnung (max):")
            )
            
            self.wait_box.setTitle(
                self.translator.get("settings.kpi_wait_box", "KPI: Wartezeit")
            )
            self.kpi_wait_good_label.setText(
                self.translator.get("settings.kpi_wait_good", "Gut (max):")
            )
            self.kpi_wait_warning_label.setText(
                self.translator.get("settings.kpi_wait_warning", "Warnung (max):")
            )
            
            self.kpi_sat_box.setTitle(
                self.translator.get("settings.kpi_satisfaction_box", "KPI: Zufriedenheit")
            )
            self.kpi_satisfaction_good_label.setText(
                self.translator.get("settings.kpi_satisfaction_good", "Gut (min):")
            )
            self.kpi_satisfaction_warning_label.setText(
                self.translator.get("settings.kpi_satisfaction_warning", "Warnung (min):")
            )
            
            # Buttons
            self.btn_save.setText(self.translator.get("settings.save", "Speichern"))
            self.btn_cancel.setText(self.translator.get("settings.cancel", "Abbrechen"))
            self.btn_save.setToolTip(
                self.translator.get("tooltips.button_settings_save", "Einstellungen speichern")
            )
            self.btn_cancel.setToolTip(
                self.translator.get("tooltips.button_settings_cancel", "Änderungen verwerfen")
            )
        else:
            self.title_label.setText("Einstellungen")
            self.general_group.setTitle("Allgemein")
            self.lang_label.setText("Sprache:")
            self.statistics_group.setTitle("Statistiken")
            self.sat_store_label.setText("Verweildauer Grenzwert (min):")
            self.sat_queue_label.setText("Wartezeit Grenzwert (min):")
            self.kpi_overtime_good_label.setText("Überzeit Gut (max):")
            self.kpi_overtime_warning_label.setText("Überzeit Warnung (max):")
            self.kpi_wait_good_label.setText("Wartezeit Gut (max):")
            self.kpi_wait_warning_label.setText("Wartezeit Warnung (max):")
            self.kpi_satisfaction_good_label.setText("Zufriedenheit Gut (min):")
            self.kpi_satisfaction_warning_label.setText("Zufriedenheit Warnung (min):")
            self.kpi_throughput_good_label.setText("Durchsatz Gut (min):")
            self.kpi_throughput_warning_label.setText("Durchsatz Warnung (min):")
            self.btn_save.setText("Speichern")
            self.btn_cancel.setText("Abbrechen")
            self.btn_save.setToolTip("Einstellungen speichern")
            self.btn_cancel.setToolTip("Änderungen verwerfen")
    
    def set_translator(self, translator):
        """Update translator reference."""
        self.translator = translator
