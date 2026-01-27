"""Info Screen with application information."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class InfoScreen(QWidget):
    """Info screen with application explanation."""
    
    back_requested = pyqtSignal()  # Signal to go back to main menu
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the info UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setSpacing(20)
        
        # Title
        title = QLabel("Erklärung - Supermarkt Simulator")
        title_font = QFont()
        title_font.setPointSize(32)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(15)
        
        info_text = QLabel("""
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
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #333333; font-size: 14px;")
        content_layout.addWidget(info_text)
        content_layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
        # Back button
        self.btn_back = QPushButton("← Zurück zum Hauptmenü")
        self.btn_back.clicked.connect(self.back_requested.emit)
        main_layout.addWidget(self.btn_back)
        
        self.setStyleSheet("""
            InfoScreen {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333333;
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
