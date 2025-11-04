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

# <<< NEUE IMPORTE >>>
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


# <<< NEUE KLASSE: ClickableGroupBox >>>
class ClickableGroupBox(QGroupBox):
    """
    Eine QGroupBox, die ein 'clicked'-Signal aussendet,
    wenn man mit der linken Maustaste darauf klickt.
    """

    clicked = pyqtSignal()  # Definiert das Signal

    def __init__(self, title, parent=None):
        super().__init__(title, parent)

    def mousePressEvent(self, event):
        """Überschreibt das Maus-Klick-Event."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Prüfen, ob der Klick auf dem Titel-Label war (optional)
            # Hier: Jeder Klick auf die Box zählt
            self.clicked.emit()  # Sendet das Signal

        # Wichtig: Das Event trotzdem weitergeben,
        # damit Kinder-Widgets (z.B. die Szene) es auch bekommen können
        super().mousePressEvent(event)


# 1. Das Hauptfenster
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Prototyp 2: 4-Quadranten-Layout (Projekt: Piep)")
        self.setGeometry(100, 100, 1400, 900)

        # <<< NEU: Status für Vollbild >>>
        self.is_sim_maximized = False

        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # <<< GEÄNDERT: Wir speichern die Reihen als QWidgets >>>
        # Das macht das Ausblenden der gesamten Reihe einfacher.

        # --- Obere Reihe (als QWidget) ---
        self.top_row_widget = QWidget()
        top_row_layout = QHBoxLayout(self.top_row_widget)
        top_row_layout.setContentsMargins(0, 0, 0, 0)
        top_row_layout.setSpacing(10)

        self.top_left_group = self.create_top_left_quadrant()
        self.top_right_group = self.create_top_right_quadrant()
        top_row_layout.addWidget(self.top_left_group, 1)
        top_row_layout.addWidget(self.top_right_group, 1)

        # --- Untere Reihe (als QWidget) ---
        self.bottom_row_widget = QWidget()
        bottom_row_layout = QHBoxLayout(self.bottom_row_widget)
        bottom_row_layout.setContentsMargins(0, 0, 0, 0)
        bottom_row_layout.setSpacing(10)

        self.bottom_left_group = self.create_bottom_left_quadrant()
        self.bottom_right_group = self.create_bottom_right_quadrant()
        bottom_row_layout.addWidget(self.bottom_left_group, 1)
        bottom_row_layout.addWidget(self.bottom_right_group, 1)

        # Reihen zum Hauptlayout hinzufügen
        main_layout.addWidget(self.top_row_widget, 1)
        main_layout.addWidget(self.bottom_row_widget, 1)

    # --- Quadranten-Erstellungs-Methoden ---

    def create_top_left_quadrant(self):
        # (Diese Methode ist unverändert)
        group_box = QGroupBox("Eingabeparameter")
        layout = QFormLayout(group_box)
        layout.setSpacing(10)
        # ... (Alle Eingabefelder wie QLineEdit, QSpinBox, etc.)
        self.sim_name_input = QLineEdit("Simulation_01")
        self.actor_count_input = QSpinBox()
        self.actor_count_input.setValue(1)
        self.actor_count_input.setMinimum(1)
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(50, 500)
        self.speed_slider.setValue(150)
        self.sim_mode_combo = QComboBox()
        self.sim_mode_combo.addItems(["Modus A", "Modus B", "Modus C"])
        self.logging_checkbox = QCheckBox("Logging aktivieren")
        self.logging_checkbox.setChecked(True)
        self.start_sim_button = QPushButton("Simulation starten")
        self.start_sim_button.setObjectName("StartButton")
        layout.addRow(QLabel("Simulations-Name:"), self.sim_name_input)
        layout.addRow(QLabel("Aktor-Anzahl:"), self.actor_count_input)
        layout.addRow(QLabel("Geschwindigkeit:"), self.speed_slider)
        layout.addRow(QLabel("Simulations-Modus:"), self.sim_mode_combo)
        layout.addRow(self.logging_checkbox)
        layout.addRow(self.start_sim_button)
        return group_box

    def create_top_right_quadrant(self):
        # (Diese Methode ist unverändert)
        group_box = QGroupBox("Ausgabe & Analyse")
        layout = QVBoxLayout(group_box)
        values_layout = QFormLayout()
        values_layout.addRow(QLabel("Gesamtlaufzeit:"), QLabel("0.00 s"))
        values_layout.addRow(QLabel("Aktoren im Ziel:"), QLabel("0 / 0"))
        values_layout.addRow(QLabel("Durchschnittszeit:"), QLabel("N/A"))
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(COLOR_WHITE_BG)
        self.plot_widget.setTitle(
            "Ergebnisse (Live)", color=COLOR_DARK_TEXT.name()
        )
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.plot(
            [0, 1, 2, 3, 4],
            [0, 5, 10, 8, 12],
            pen=pg.mkPen(color=COLOR_GREEN, width=2),
        )
        layout.addLayout(values_layout)
        layout.addWidget(self.plot_widget)
        return group_box

    def create_bottom_left_quadrant(self):
        """Erstellt die klickbare Simulations-Ansicht (Unten-Links)."""

        # <<< GEÄNDERT: Verwendet ClickableGroupBox >>>
        group_box = ClickableGroupBox("Live-Simulation (Miniatur)")
        # Signal mit unserer Umschalt-Funktion verbinden
        group_box.clicked.connect(self.toggle_simulation_fullscreen)

        layout = QVBoxLayout(group_box)

        # <<< NEU: Button zum Verkleinern >>>
        self.minimize_sim_button = QPushButton(
            "Zurück zur 4-Quadranten-Ansicht"
        )
        self.minimize_sim_button.setObjectName("MinimizeButton")  # Für QSS
        self.minimize_sim_button.clicked.connect(
            self.toggle_simulation_fullscreen
        )
        self.minimize_sim_button.hide()  # Am Anfang versteckt
        layout.addWidget(self.minimize_sim_button)

        # Simulations-Szene (unverändert)
        self.sim_scene = QGraphicsScene()
        self.sim_scene.setBackgroundBrush(QBrush(COLOR_LIGHT_BG))
        self.sim_scene.setSceneRect(0, 0, 400, 300)

        self.sim_view = QGraphicsView(self.sim_scene)
        self.sim_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Beispiel-Items (unverändert)
        self.sim_scene.addEllipse(
            50,
            50,
            10,
            10,
            QPen(COLOR_TURQUOISE.darker(150)),
            QBrush(COLOR_TURQUOISE.lighter(130)),
        )
        self.sim_scene.addEllipse(
            200,
            150,
            10,
            10,
            QPen(COLOR_TURQUOISE.darker(150)),
            QBrush(COLOR_TURQUOISE.lighter(130)),
        )
        self.sim_scene.addEllipse(
            50 - 6,
            50 - 6,
            12,
            12,
            QPen(COLOR_ORANGE.darker(150)),
            QBrush(COLOR_ORANGE),
        )

        layout.addWidget(self.sim_view)
        return group_box

    def create_bottom_right_quadrant(self):
        # (Diese Methode ist unverändert)
        group_box = QGroupBox("Zukünftige Anforderungen")
        layout = QVBoxLayout(group_box)
        placeholder_text = "Hier ist Platz für zukünftige Anforderungen..."
        self.placeholder_widget = QTextEdit()
        self.placeholder_widget.setReadOnly(True)
        self.placeholder_widget.setText(placeholder_text)
        layout.addWidget(self.placeholder_widget)
        return group_box

    # <<< NEUE METHODE: toggle_simulation_fullscreen >>>
    def toggle_simulation_fullscreen(self):
        """Schaltet die Sichtbarkeit der Quadranten um."""

        # Zustand umkehren
        self.is_sim_maximized = not self.is_sim_maximized

        if self.is_sim_maximized:
            # --- MAXIMIEREN ---
            # Andere Quadranten ausblenden
            self.top_row_widget.hide()  # Obere Reihe (enthält TL und TR)
            self.bottom_right_group.hide()  # Platzhalter (BR)

            # Verkleinern-Button anzeigen
            self.minimize_sim_button.show()
            self.bottom_left_group.setTitle("Live-Simulation (Vollbild)")

        else:
            # --- MINIMIEREN (Normalansicht) ---
            # Andere Quadranten wieder einblenden
            self.top_row_widget.show()
            self.bottom_right_group.show()

            # Verkleinern-Button verstecken
            self.minimize_sim_button.hide()
            self.bottom_left_group.setTitle("Live-Simulation (Miniatur)")


# --- Anwendung starten ---
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # --- Globales Stylesheet "PROJEKT: PIEP" (Erweitert) ---
    app.setStyleSheet(
        """
        /* ... (Alle QWidget, QGroupBox, QPushButton Stile von vorhin) ... */
        
        QWidget {{
            font-family: 'Segoe UI', 'Sans-Serif';
            font-size: 10pt;
            color: {COLOR_DARK_TEXT.name()};
        }}
        QMainWindow, QWidget {{
            background-color: {COLOR_WHITE_BG.name()};
        }}
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
        QPushButton {{
            color: white; border: none; padding: 8px 14px;
            font-size: 10pt; font-weight: bold; border-radius: 4px;
        }}
        QPushButton:disabled {{
            background-color: {COLOR_BORDER.name()};
            color: {COLOR_MEDIUM_TEXT.name()};
        }}
        QPushButton#StartButton {{
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FF8000, stop:1 {COLOR_ORANGE.name()});
        }}
        QPushButton#StartButton:hover {{
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FF9000, stop:1 #FF7C00);
        }}
        
        /* <<< NEU: Stil für den Verkleinern-Button (Türkis) >>> */
        QPushButton#MinimizeButton {{
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 {COLOR_TURQUOISE.name()}, stop:1 #0090C0);
        }}
        QPushButton#MinimizeButton:hover {{
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #00C0E0, stop:1 #00A0C0);
        }}

        /* ... (Alle Stile für QLineEdit, QSlider, QGraphicsView etc.) ... */
        
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
        QComboBox::drop-down {{ border: none; }}
        QCheckBox::indicator {{
            width: 16px; height: 16px;
            border: 1px solid {COLOR_BORDER.name()};
            border-radius: 4px;
            background-color: {COLOR_LIGHT_BG.name()};
        }}
        QCheckBox::indicator:checked {{
            background-color: {COLOR_ORANGE.name()};
            border-color: {COLOR_ORANGE.darker(120).name()};
        }}
        QSlider::groove:horizontal {{
            background: {COLOR_BORDER.name()}; height: 6px; border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: {COLOR_ORANGE.name()};
            width: 16px; height: 16px; margin: -5px 0; border-radius: 8px;
        }}
        QGraphicsView {{
            border: 1px solid {COLOR_BORDER.name()};
            border-radius: 4px;
        }}
        QFormLayout QLabel {{
            font-size: 10pt;
            color: {COLOR_MEDIUM_TEXT.name()};
            padding-top: 5px;
        }}
        """
    )

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
