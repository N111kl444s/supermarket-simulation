import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QGraphicsView,
    QGraphicsScene,
    QLabel,
    QTextEdit,
    QGroupBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QSlider,
    QComboBox,
    QCheckBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPen, QBrush, QColor, QFont, QPainter

import pyqtgraph as pg

# --- Projekt: Piep Farbpalette (basierend auf Logo) ---
COLOR_ORANGE = QColor("#FF6A00")
COLOR_TURQUOISE = QColor("#00B0D0")
COLOR_GREEN = QColor("#50C878")
COLOR_DARK_TEXT = QColor("#333333")
COLOR_MEDIUM_TEXT = QColor("#666666")
COLOR_LIGHT_BG = QColor("#F8F8F8")
COLOR_WHITE_BG = QColor("#FFFFFF")
COLOR_BORDER = QColor("#E0E0E0")


# --- Helfer-Klasse aus P2.1 ---
class ClickableGroupBox(QGroupBox):
    clicked = pyqtSignal()

    def __init__(self, title, parent=None):
        super().__init__(title, parent)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


# 1. Das Hauptfenster
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Prototyp 3: Supermarkt-Simulator (Projekt: Piep)")
        self.setGeometry(100, 100, 1400, 900)

        self.is_sim_maximized = False

        # Leere Layouts, die dynamisch gefüllt werden
        self.kassen_layout = None
        self.sb_kassen_layout_row1 = None
        self.sb_kassen_layout_row2 = None

        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Obere Reihe (Widget)
        self.top_row_widget = QWidget()
        top_row_layout = QHBoxLayout(self.top_row_widget)
        top_row_layout.setContentsMargins(0, 0, 0, 0)
        top_row_layout.setSpacing(10)

        self.top_left_group = self.create_top_left_quadrant()
        self.top_right_group = self.create_top_right_quadrant()
        top_row_layout.addWidget(self.top_left_group, 1)
        top_row_layout.addWidget(self.top_right_group, 1)

        # Untere Reihe (Widget)
        self.bottom_row_widget = QWidget()
        bottom_row_layout = QHBoxLayout(self.bottom_row_widget)
        bottom_row_layout.setContentsMargins(0, 0, 0, 0)
        bottom_row_layout.setSpacing(10)

        self.bottom_left_group = self.create_bottom_left_quadrant()
        self.bottom_right_group = self.create_bottom_right_quadrant()
        bottom_row_layout.addWidget(
            self.bottom_left_group, 2
        )  # Live-Ansicht (links) kriegt mehr Platz
        bottom_row_layout.addWidget(self.bottom_right_group, 1)

        main_layout.addWidget(self.top_row_widget, 1)
        main_layout.addWidget(
            self.bottom_row_widget, 2
        )  # Untere Reihe kriegt mehr Platz

    # --- Quadranten-Erstellungs-Methoden ---

    def create_top_left_quadrant(self):
        """Erstellt die Eingabemaske (Oben-Links)."""
        group_box = QGroupBox("Konfiguration")
        layout = QFormLayout(group_box)
        layout.setSpacing(10)

        # <<< NEUE EINGABEN >>>
        self.kassen_count_input = QSpinBox()
        self.kassen_count_input.setValue(4)  # Standardwert 4 Kassen
        self.kassen_count_input.setMinimum(0)

        self.sb_kassen_count_input = QSpinBox()
        self.sb_kassen_count_input.setValue(6)  # Standardwert 6 SB-Kassen
        self.sb_kassen_count_input.setMinimum(0)

        self.generate_button = QPushButton("Layout generieren")
        self.generate_button.setObjectName(
            "GenerateButton"
        )  # Grüner Button-Stil
        self.generate_button.clicked.connect(self.on_generate_layout)

        self.start_sim_button = QPushButton("Simulation starten")
        self.start_sim_button.setObjectName("StartButton")
        self.start_sim_button.setEnabled(
            False
        )  # Erst nach Generierung aktivieren

        layout.addRow(QLabel("Anzahl Kassen:"), self.kassen_count_input)
        layout.addRow(QLabel("Anzahl SB-Kassen:"), self.sb_kassen_count_input)
        layout.addRow(self.generate_button)
        layout.addRow(self.start_sim_button)

        return group_box

    def create_top_right_quadrant(self):
        """Erstellt die Ausgabemaske (Oben-Rechts)."""
        group_box = QGroupBox("Ausgabe & Analyse")
        layout = QVBoxLayout(group_box)

        values_layout = QFormLayout()
        values_layout.addRow(
            QLabel("Warteschlange (Kasse):"), QLabel("0 Personen")
        )
        values_layout.addRow(
            QLabel("Warteschlange (SB):"), QLabel("0 Personen")
        )
        values_layout.addRow(QLabel("Auslastung Kassen:"), QLabel("0%"))

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(COLOR_WHITE_BG)
        self.plot_widget.setTitle(
            "Warteschlangen-Länge (Live)", color=COLOR_DARK_TEXT.name()
        )
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.plotItem.getAxis("left").setLabel("Personen")
        self.plot_widget.plotItem.getAxis("bottom").setLabel("Zeit (s)")

        layout.addLayout(values_layout)
        layout.addWidget(self.plot_widget)
        return group_box

    def create_bottom_left_quadrant(self):
        """Erstellt die klickbare Simulations-Ansicht (Unten-Links)."""
        group_box = ClickableGroupBox("Live-Ansicht (Miniatur)")
        group_box.clicked.connect(self.toggle_simulation_fullscreen)

        # Hauptlayout für diesen Quadranten (Vertikal)
        main_v_layout = QVBoxLayout(group_box)

        # Button zum Verkleinern (zuerst hinzugefügt, aber versteckt)
        self.minimize_sim_button = QPushButton("Zurück zur Dashboard-Ansicht")
        self.minimize_sim_button.setObjectName("MinimizeButton")
        self.minimize_sim_button.clicked.connect(
            self.toggle_simulation_fullscreen
        )
        self.minimize_sim_button.hide()
        main_v_layout.addWidget(self.minimize_sim_button)

        # <<< NEUES INTERNES LAYOUT (BASIEREND AUF SKIZZE) >>>
        # Wir teilen den Bereich horizontal (links Kasse/Warte, rechts Supermarkt)
        sim_layout = QHBoxLayout()

        # Linke Spalte
        left_column = QVBoxLayout()
        kassen_group = QGroupBox("Kassenbereich")
        self.kassen_layout = QVBoxLayout(
            kassen_group
        )  # Layout, das wir dynamisch füllen
        self.kassen_layout.setSpacing(5)

        warte_group = QGroupBox("Wartebereich")
        warte_layout = QVBoxLayout(warte_group)
        # Platzhalter für wartebereich.png
        self.warte_view = QGraphicsView()
        self.warte_scene = QGraphicsScene()
        self.warte_scene.setBackgroundBrush(QBrush(COLOR_LIGHT_BG))
        self.warte_view.setScene(self.warte_scene)
        warte_layout.addWidget(self.warte_view)

        left_column.addWidget(kassen_group, 1)  # Stretch 1
        left_column.addWidget(warte_group, 1)  # Stretch 1

        # Rechte Spalte
        supermarkt_group = QGroupBox("Supermarkt")
        supermarkt_layout = QVBoxLayout(supermarkt_group)
        # Platzhalter für supermarkt.png
        self.supermarkt_view = QGraphicsView()
        self.supermarkt_scene = QGraphicsScene()
        self.supermarkt_scene.setBackgroundBrush(
            QBrush(COLOR_LIGHT_BG.darker(105))
        )
        self.supermarkt_view.setScene(self.supermarkt_scene)
        supermarkt_layout.addWidget(self.supermarkt_view)

        sim_layout.addLayout(left_column, 1)  # Linke Spalte (Stretch 1)
        sim_layout.addWidget(supermarkt_group, 2)  # Rechte Spalte (Stretch 2)

        main_v_layout.addLayout(sim_layout)
        return group_box

    def create_bottom_right_quadrant(self):
        """Erstellt den Platzhalter (Unten-Rechts)."""
        group_box = QGroupBox(
            "Log-Ausgabe"
        )  # Umbenannt von "Zukünftige Anforderungen"
        layout = QVBoxLayout(group_box)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setText(
            "Log-Ausgaben des Simulators erscheinen hier...\n"
        )

        layout.addWidget(self.log_output)
        return group_box

    # --- Helfer-Methoden ---

    def _clear_layout(self, layout):
        """Leert ein Layout von all seinen Widgets."""
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                # Falls es ein verschachteltes Layout ist
                self._clear_layout(item.layout())

    def _create_kasse_widget(self, text, color):
        """Erstellt ein Platzhalter-Widget für eine Kasse."""
        # Sobald Sie 'kasse.png' haben, ersetzen Sie dies
        # durch ein QLabel mit setPixmap()

        kasse = QLabel(text)
        kasse.setFixedSize(60, 40)
        kasse.setAlignment(Qt.AlignmentFlag.AlignCenter)
        kasse.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        kasse.setStyleSheet(
            """
            background-color: {color.name()};
            color: white;
            border: 1px solid {color.darker(150).name()};
            border-radius: 4px;
        """
        )
        return kasse

    def on_generate_layout(self):
        """Füllt den Kassenbereich dynamisch basierend auf der Konfiguration."""
        self.log_output.append("Generiere Kassen-Layout...")

        # 1. Alle alten Layouts und Widgets im Kassenbereich löschen
        self._clear_layout(self.kassen_layout)

        # 2. Reguläre Kassen (Horizontal)
        kassen_count = self.kassen_count_input.value()
        if kassen_count > 0:
            kassen_hbox = QHBoxLayout()
            kassen_hbox.setSpacing(5)
            for i in range(kassen_count):
                kasse_widget = self._create_kasse_widget(
                    f"KASSE {i+1}", COLOR_TURQUOISE
                )
                kassen_hbox.addWidget(kasse_widget)
            kassen_hbox.addStretch()
            self.kassen_layout.addLayout(kassen_hbox)

        # 3. SB-Kassen (2 Reihen, Vertikal)
        sb_kassen_count = self.sb_kassen_count_input.value()
        if sb_kassen_count > 0:
            sb_vbox = QVBoxLayout()
            self.sb_kassen_layout_row1 = QHBoxLayout()
            self.sb_kassen_layout_row2 = QHBoxLayout()

            for i in range(sb_kassen_count):
                sb_kasse_widget = self._create_kasse_widget(
                    f"SB {i+1}", COLOR_GREEN
                )
                if i % 2 == 0:  # Abwechselnd auf Reihe 1 und 2 verteilen
                    self.sb_kassen_layout_row1.addWidget(sb_kasse_widget)
                else:
                    self.sb_kassen_layout_row2.addWidget(sb_kasse_widget)

            self.sb_kassen_layout_row1.addStretch()
            self.sb_kassen_layout_row2.addStretch()

            sb_vbox.addLayout(self.sb_kassen_layout_row1)
            sb_vbox.addLayout(self.sb_kassen_layout_row2)
            self.kassen_layout.addLayout(sb_vbox)

        self.kassen_layout.addStretch()
        self.start_sim_button.setEnabled(True)  # Simulation kann jetzt starten
        self.log_output.append(
            f"Layout mit {kassen_count} Kassen und {sb_kassen_count} SB-Kassen erstellt."
        )

    def toggle_simulation_fullscreen(self):
        """Schaltet die Sichtbarkeit der Quadranten um."""
        self.is_sim_maximized = not self.is_sim_maximized

        if self.is_sim_maximized:
            # Maximieren
            self.top_row_widget.hide()
            self.bottom_right_group.hide()
            self.minimize_sim_button.show()
            self.bottom_left_group.setTitle("Live-Ansicht (Vollbild)")
        else:
            # Minimieren (Normalansicht)
            self.top_row_widget.show()
            self.bottom_right_group.show()
            self.minimize_sim_button.hide()
            self.bottom_left_group.setTitle("Live-Ansicht (Miniatur)")


# --- Anwendung starten ---
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # --- Globales Stylesheet "PROJEKT: PIEP" (Erweitert für P3) ---
    app.setStyleSheet(
        """
        /* Globale Stile */
        QWidget {{
            font-family: 'Segoe UI', 'Sans-Serif';
            font-size: 10pt;
            color: {COLOR_DARK_TEXT.name()};
        }}
        QMainWindow, QWidget {{
            background-color: {COLOR_WHITE_BG.name()};
        }}

        /* QGroupBox Styling für Quadranten */
        QGroupBox {{
            background-color: {COLOR_WHITE_BG.name()};
            border: 1px solid {COLOR_BORDER.name()};
            border-radius: 5px;
            margin-top: 10px;
            padding: 10px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 5px;
            left: 10px;
            color: {COLOR_TURQUOISE.name()};
            font-size: 11pt;
            font-weight: bold;
        }}
        
        /* Titel der inneren Boxen (Kasse, Warte, Supermarkt) kleiner */
        QGroupBox QGroupBox::title {{
            color: {COLOR_MEDIUM_TEXT.name()};
            font-size: 9pt;
            font-weight: bold;
        }}
        QGroupBox QGroupBox {{
             padding: 5px; /* Weniger Padding für innere Boxen */
        }}

        /* Knöpfe */
        QPushButton {{
            color: white; border: none; padding: 8px 14px;
            font-size: 10pt; font-weight: bold; border-radius: 4px;
        }}
        QPushButton:disabled {{
            background-color: {COLOR_BORDER.name()};
            color: {COLOR_MEDIUM_TEXT.name()};
        }}
        /* Start-Button (Orange) */
        QPushButton#StartButton {{
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FF8000, stop:1 {COLOR_ORANGE.name()});
        }}
        QPushButton#StartButton:hover {{
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FF9000, stop:1 #FF7C00);
        }}
        
        /* Generate-Button (Grün) */
        QPushButton#GenerateButton {{
             background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 {COLOR_GREEN.name()}, stop:1 #40A060);
        }}
        QPushButton#GenerateButton:hover {{
             background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #60D080, stop:1 #50B070);
        }}
        
        /* Minimize-Button (Türkis) */
        QPushButton#MinimizeButton {{
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 {COLOR_TURQUOISE.name()}, stop:1 #0090C0);
        }}
        QPushButton#MinimizeButton:hover {{
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #00C0E0, stop:1 #00A0C0);
        }}

        /* Styling für Eingabefelder */
        QLineEdit, QSpinBox, QComboBox, QTextEdit {{
            background-color: {COLOR_LIGHT_BG.name()};
            border: 1px solid {COLOR_BORDER.name()};
            border-radius: 4px;
            padding: 5px;
            font-size: 10pt;
        }}
        QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus {{
            border: 1px solid {COLOR_ORANGE.name()};
        }}
        
        /* Log-Ausgabe (speziell) */
        QTextEdit#LogOutput {{
            font-family: 'Consolas', 'Courier New', 'monospace';
            font-size: 9pt;
            color: {COLOR_MEDIUM_TEXT.name()};
        }}

        /* Grafik-Ansicht */
        QGraphicsView {{
            border: 1px solid {COLOR_BORDER.name()};
            border-radius: 4px;
        }}
        
        /* Labels in Form-Layouts */
        QFormLayout QLabel {{
            font-size: 10pt;
            color: {COLOR_MEDIUM_TEXT.name()};
            padding-top: 5px;
        }}
        """
    )

    window = MainWindow()
    window.show()
    sys.exit(app)
