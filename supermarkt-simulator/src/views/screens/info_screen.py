"""Info Screen with application information."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from config import COLOR_BG_MAIN, COLOR_ACCENT, COLOR_TEXT_MAIN, COLOR_BORDER


class InfoScreen(QWidget):
    """Info screen with application explanation."""
    
    back_requested = pyqtSignal()  # Signal to go back to main menu
    
    def __init__(self, translator=None):
        super().__init__()
        self.translator = translator
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the info UI."""
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
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(15)
        
        self.info_text = QLabel()
        self.info_text.setWordWrap(True)
        self.info_text.setStyleSheet(f"color: {COLOR_TEXT_MAIN.name()}; font-size: 14px;")
        content_layout.addWidget(self.info_text)
        content_layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
        # Back button
        self.btn_back = QPushButton()
        self.btn_back.clicked.connect(self.back_requested.emit)
        main_layout.addWidget(self.btn_back)
        
        # Update texts with translations
        self.update_translations()
        
        # Get colors from config
        bg_main = COLOR_BG_MAIN.name()
        accent = COLOR_ACCENT.name()
        text_main = COLOR_TEXT_MAIN.name()
        border = COLOR_BORDER.name()
        
        self.setStyleSheet(f"""
            InfoScreen {{
                background-color: {bg_main};
            }}
            QLabel {{
                color: {text_main};
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

    
    def update_translations(self):
        """Update UI texts with current translations."""
        if self.translator:
            self.title_label.setText(self.translator.get("info.title", "Erklärung - Supermarkt Simulator"))
            self.info_text.setText(self.translator.get("info.content", ""))
            self.btn_back.setText(self.translator.get("info.back", "Zurück zum Hauptmenü"))
            self.btn_back.setToolTip(
                self.translator.get("tooltips.button_info_back", "Zum Hauptmenü")
            )
        else:
            self.title_label.setText("Erklärung - Supermarkt Simulator")
            self.btn_back.setText("Zurück zum Hauptmenü")
            self.btn_back.setToolTip("Zum Hauptmenü")
            # Default German content
            self.info_text.setText("""
<h2>Willkommen zum Supermarkt Simulator!</h2>

<p><b>Überblick:</b></p>
<p>Der Supermarkt Simulator ist ein Werkzeug zur Simulation und Optimierung von Supermarkt-Abläufen. 
Sie können verschiedene Szenarien erstellen, die Kundenströme simulieren und die Effizienz Ihres 
virtuellen Supermarkts analysieren.</p>

<p><b>Hauptfunktionen:</b></p>
<ul>
<li><b>Simulation:</b> Führen Sie realistische Supermarkt-Szenarien durch</li>
<li><b>Editor:</b> Erstellen und bearbeiten Sie eigene Supermarkt-Layouts</li>
<li><b>Statistiken:</b> Analysieren Sie Kundenströme und Warteschlangen</li>
<li><b>Mehrsprachig:</b> Unterstützung für Deutsch und Englisch</li>
</ul>

<p><b>So funktioniert es:</b></p>
<ol>
<li>Wählen Sie eine vordefinierte Karte oder erstellen Sie Ihre eigene im Editor-Modus</li>
<li>Stellen Sie die Simulationsparameter ein (Anzahl Kunden, Öffnungszeiten, etc.)</li>
<li>Starten Sie die Simulation und beobachten Sie, wie die Kunden einkaufen</li>
<li>Analysieren Sie die Ergebnisse und optimieren Sie Ihr Layout</li>
</ol>

<p><b>Tipps:</b></p>
<ul>
<li>Experimentieren Sie mit unterschiedlichen Kassen-Konfigurationen</li>
<li>Beobachten Sie Warteschlangen während der Simulation</li>
<li>Nutzen Sie den Editor, um neue Layouts zu erstellen</li>
<li>Die Statistiken helfen bei der Optimierung</li>
</ul>

<p><i>Version 1.0 - Viel Spaß beim Simulieren!</i></p>
            """)