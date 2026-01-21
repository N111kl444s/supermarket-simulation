"""
Sidebar Component.
Refactored:
- Added "(Normalverteilung)" label to Shopping section.
- UPDATED: Added "(Gleichverteilung)" labels to Scan and Staff sections.
- LAYOUT UPDATE: Split 'Eingabe' tab into 3 sub-tabs (Laden, Kunden, Personal).
- NEW: Added hint text and spacing above sub-tabs.
- NEW: Added tooltip icons with calculation formulas for distributions.
- FIX: Removed invalid 'cursor' property from stylesheet (fixed console errors).
- FIX: Transparent background for scroll areas to match modern UI theme.
- FIX: Corrected cursor shape name (HelpCursor -> WhatsThisCursor).
- FIX: Removed margins from nested layouts in FormLayouts to ensure consistent alignment.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QScrollArea,
    QGroupBox,
    QFormLayout,
    QTimeEdit,
    QSpinBox,
    QDoubleSpinBox,
    QLabel,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QComboBox,
    QSizePolicy,
    QButtonGroup,
)
from PyQt6.QtCore import Qt, QTime
from PyQt6.QtGui import QBrush, QColor
import pyqtgraph as pg
from config import *


class Sidebar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        self.control_tabs = QTabWidget()
        layout.addWidget(self.control_tabs)

        self._init_input_tab()
        self._init_simulation_tab()
        self._init_stats_tab()
        self._init_editor_tab()
        self._init_data_tab()

    def _init_input_tab(self):
        # Container für den Eingabe-Tab
        container = QWidget()
        layout_container = QVBoxLayout(container)
        layout_container.setContentsMargins(5, 5, 5, 5)
        layout_container.setSpacing(10)

        # 1. Hinweistext & Abstand
        lbl_hint = QLabel(
            "Konfigurieren Sie hier die Simulationsparameter.\nNutzen Sie die Tabs unten für Details."
        )
        lbl_hint.setStyleSheet(
            "color: #555; font-style: italic; margin-bottom: 2px;"
        )
        lbl_hint.setWordWrap(True)
        layout_container.addWidget(lbl_hint)

        layout_container.addSpacing(5)

        # 2. Das Sub-Tab-Widget
        input_tabs = QTabWidget()

        # --- SUB-TAB 1: LADEN ---
        tab_shop = QWidget()
        l_shop = QVBoxLayout(tab_shop)
        l_shop.setAlignment(Qt.AlignmentFlag.AlignTop)
        l_shop.setSpacing(10)
        l_shop.setContentsMargins(5, 15, 5, 5)

        # Öffnungszeiten
        gb_time = QGroupBox("Öffnungszeiten")
        f_time = QFormLayout(gb_time)
        self.time_open = self._create_time_edit(DEFAULT_OPEN_TIME)
        self.time_close = self._create_time_edit(DEFAULT_CLOSE_TIME)
        f_time.addRow("Öffnen:", self.time_open)
        f_time.addRow("Schließen:", self.time_close)
        l_shop.addWidget(gb_time)

        # Störung
        gb_co = QGroupBox("Störungen & Kassen")
        f_co = QFormLayout(gb_co)
        self.checkout_fail_rate_normal = self._create_spin(0, 0, 100, " %")
        self.checkout_fail_rate_sb = self._create_spin(0, 0, 100, " %")
        f_co.addRow("Ausfall (Normal):", self.checkout_fail_rate_normal)
        f_co.addRow("Ausfall (SB):", self.checkout_fail_rate_sb)
        l_shop.addWidget(gb_co)

        input_tabs.addTab(tab_shop, "Laden")

        # --- SUB-TAB 2: KUNDEN ---
        tab_cust_container = QWidget()
        l_cust_cont = QVBoxLayout(tab_cust_container)
        l_cust_cont.setContentsMargins(0, 0, 0, 0)

        scroll_cust = QScrollArea()
        scroll_cust.setWidgetResizable(True)
        scroll_cust.setStyleSheet(
            "QScrollArea { border: none; background-color: transparent; }"
        )

        content_cust = QWidget()
        content_cust.setStyleSheet("background-color: transparent;")

        l_gb_cust = QVBoxLayout(content_cust)
        l_gb_cust.setAlignment(Qt.AlignmentFlag.AlignTop)
        l_gb_cust.setContentsMargins(5, 15, 5, 5)

        # Kundendichte
        l_gb_cust.addWidget(self._header("Kundendichte & Generierung"))
        l_gb_cust.addWidget(self._sublabel("(Exponentialverteilung)"))
        f_gen = QFormLayout()
        self.actor_count_input = self._create_spin(50, 1, 10000, " / Tag")
        self.disabled_prob_input = self._create_double_spin(10, 0, 100, " %")

        # Icon für Kundendichte
        row_anzahl = QHBoxLayout()
        # FIX: Margins auf 0 setzen, damit es bündig mit anderen Zeilen ist
        row_anzahl.setContentsMargins(0, 0, 0, 0)
        row_anzahl.addWidget(self.actor_count_input)
        row_anzahl.addWidget(
            self._create_help_label(
                "<b>Exponentialverteilung (Simulation)</b><br>"
                "Berechnet den Zeitabstand zwischen zwei Kunden.<br>"
                "<i>Formel:</i> <code>Interval = (Zeit / Anzahl) * random.uniform(0.7, 1.3)</code>"
            )
        )
        f_gen.addRow("Anzahl:", row_anzahl)
        f_gen.addRow("Behinderung:", self.disabled_prob_input)
        l_gb_cust.addLayout(f_gen)

        # Geschwindigkeit
        l_gb_cust.addWidget(self._header("Bewegungsgeschwindigkeit (px/s)"))
        f_move = QFormLayout()
        self.speed_walk_mean, self.speed_walk_std = self._create_dist_row(
            "Gehen:",
            2.5,
            0.5,
            f_move,
            tooltip="<b>Normalverteilung (Gauß)</b><br>"
            "Geschwindigkeit zufällig um den Mittelwert gestreut.<br>"
            "<i>Formel:</i> <code>v = random.normalvariate(Ø, σ)</code>",
        )
        self.speed_roll_mean, self.speed_roll_std = self._create_dist_row(
            "Rollen:",
            1.5,
            0.3,
            f_move,
            tooltip="<b>Normalverteilung (Gauß)</b><br>"
            "Geschwindigkeit zufällig um den Mittelwert gestreut.<br>"
            "<i>Formel:</i> <code>v = random.normalvariate(Ø, σ)</code>",
        )
        l_gb_cust.addLayout(f_move)

        # Einkauf
        l_gb_cust.addWidget(self._header("Einkauf"))
        l_gb_cust.addWidget(self._sublabel("(Normalverteilung)"))
        f_shop = QFormLayout()
        self.items_mean = self._create_spin(12, 1, 100)
        self.items_std = self._create_double_spin(4.0, 0, 20)
        row = QHBoxLayout()
        # FIX: Margins auf 0 setzen
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(QLabel("Ø:"))
        row.addWidget(self.items_mean)
        row.addWidget(QLabel("σ:"))
        row.addWidget(self.items_std)
        # Icon für Einkauf
        row.addWidget(
            self._create_help_label(
                "<b>Normalverteilung</b><br>"
                "Bestimmt die Anzahl der Artikel im Einkaufswagen.<br>"
                "<i>Formel:</i> <code>items = int(random.normalvariate(Ø, σ))</code>"
            )
        )
        f_shop.addRow("Artikelanzahl:", row)
        self.hand_scanner_prob = self._create_double_spin(5.0, 0, 100, " %")
        f_shop.addRow("Handscanner:", self.hand_scanner_prob)
        l_gb_cust.addLayout(f_shop)

        # Scannen
        l_gb_cust.addWidget(self._header("Scannen (Dauer in Sek)"))
        l_gb_cust.addWidget(self._sublabel("(Gleichverteilung)"))
        f_scan = QFormLayout()
        self.scan_speed_normal_min, self.scan_speed_normal_max = (
            self._create_range_row(
                "Normal:",
                0.5,
                1.5,
                f_scan,
                tooltip="<b>Gleichverteilung</b><br>"
                "Jeder Artikel braucht eine zufällige Zeit zwischen Min und Max.<br>"
                "<i>Formel:</i> <code>t = random.uniform(Min, Max)</code>",
            )
        )
        self.scan_speed_disabled_min, self.scan_speed_disabled_max = (
            self._create_range_row(
                "Behindert:",
                1.0,
                3.0,
                f_scan,
                tooltip="<b>Gleichverteilung</b><br>"
                "Jeder Artikel braucht eine zufällige Zeit zwischen Min und Max.<br>"
                "<i>Formel:</i> <code>t = random.uniform(Min, Max)</code>",
            )
        )
        l_gb_cust.addLayout(f_scan)

        scroll_cust.setWidget(content_cust)
        l_cust_cont.addWidget(scroll_cust)
        input_tabs.addTab(tab_cust_container, "Kunden")

        # --- SUB-TAB 3: PERSONAL ---
        tab_staff = QWidget()
        l_staff = QVBoxLayout(tab_staff)
        l_staff.setAlignment(Qt.AlignmentFlag.AlignTop)
        l_staff.setContentsMargins(5, 15, 5, 5)

        l_staff.addWidget(self._header("Scangeschwindigkeit (Sek/Artikel)"))
        l_staff.addWidget(self._sublabel("(Gleichverteilung)"))
        f_staff = QFormLayout()
        self.scan_speed_newbie_min, self.scan_speed_newbie_max = (
            self._create_range_row(
                "Azubi:",
                1.5,
                2.5,
                f_staff,
                tooltip="<b>Gleichverteilung</b><br>"
                "Scan-Dauer pro Artikel an bedienter Kasse.<br>"
                "<i>Formel:</i> <code>t = random.uniform(Min, Max)</code>",
            )
        )
        self.scan_speed_pro_min, self.scan_speed_pro_max = (
            self._create_range_row(
                "Festangestellt:",
                0.8,
                1.2,
                f_staff,
                tooltip="<b>Gleichverteilung</b><br>"
                "Scan-Dauer pro Artikel an bedienter Kasse.<br>"
                "<i>Formel:</i> <code>t = random.uniform(Min, Max)</code>",
            )
        )
        l_staff.addLayout(f_staff)

        input_tabs.addTab(tab_staff, "Personal")

        layout_container.addWidget(input_tabs)
        self.control_tabs.addTab(container, "Eingabe")

    def _init_simulation_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        gb_log = QGroupBox("Live Feed")
        l_log = QVBoxLayout(gb_log)
        self.list_log = QListWidget()
        self.list_log.setAlternatingRowColors(True)
        self.list_log.setStyleSheet("font-size: 11px;")
        l_log.addWidget(self.list_log)
        layout.addWidget(gb_log)
        gb_stat = QGroupBox("Live Status")
        f_stat = QFormLayout(gb_stat)
        self.lbl_queue_count = self._create_bold_label("0")
        self.lbl_customers_in_store = self._create_bold_label("0", "blue")
        self.lbl_total_customers = self._create_bold_label("0", "green")
        f_stat.addRow("Kunden in Warteschlange:", self.lbl_queue_count)
        f_stat.addRow("Kunden im Laden:", self.lbl_customers_in_store)
        f_stat.addRow("Kunden gesamt:", self.lbl_total_customers)
        layout.addWidget(gb_stat)
        self.control_tabs.addTab(widget, "Simulation")

    def _init_stats_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(COLOR_BG_PANEL)
        self.plot_widget.getAxis("bottom").setPen(
            pg.mkPen(color=COLOR_TEXT_MAIN)
        )
        self.plot_widget.getAxis("left").setPen(
            pg.mkPen(color=COLOR_TEXT_MAIN)
        )
        layout.addWidget(self.plot_widget)
        self.control_tabs.addTab(widget, "Statistiken")

    def _init_editor_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        gb_map = QGroupBox("Map-Verwaltung")
        l_map = QVBoxLayout(gb_map)
        r1 = QHBoxLayout()
        self.btn_new_map = QPushButton("Neu")
        self.btn_save_map = QPushButton("Speichern")
        self.btn_delete_map = QPushButton("Löschen")
        self.btn_delete_map.setStyleSheet(
            f"color: {COLOR_ERROR.name()}; border-color: {COLOR_ERROR.name()};"
        )
        r1.addWidget(self.btn_new_map)
        r1.addWidget(self.btn_save_map)
        r1.addWidget(self.btn_delete_map)
        l_map.addLayout(r1)

        r2 = QHBoxLayout()
        self.btn_set_background = QPushButton("🖼️ Bild wählen")
        self.btn_remove_background = QPushButton("❌")
        self.btn_remove_background.setFixedWidth(30)
        r2.addWidget(self.btn_set_background)
        r2.addWidget(self.btn_remove_background)
        l_map.addLayout(r2)

        r3 = QHBoxLayout()
        r3.addWidget(QLabel("Skalierung:"))
        self.spin_bg_scale = QDoubleSpinBox()
        self.spin_bg_scale.setRange(0.0001, 10.0)
        self.spin_bg_scale.setDecimals(4)
        self.spin_bg_scale.setSingleStep(0.01)
        self.spin_bg_scale.setValue(0.5)
        self.spin_bg_scale.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        r3.addWidget(self.spin_bg_scale)
        l_map.addLayout(r3)

        self.btn_move_map = QPushButton("🗺️ Karte zentrieren")
        self.btn_move_map.setCheckable(False)
        l_map.addWidget(self.btn_move_map)
        layout.addWidget(gb_map)

        gb_set = QGroupBox("Map Einstellungen")
        f_set = QFormLayout(gb_set)
        self.combo_global_exit = QComboBox()
        self.combo_global_exit.addItems(["Links", "Rechts", "Oben", "Unten"])
        self.combo_global_exit.setCurrentText("Rechts")
        f_set.addRow("Abgangsrichtung:", self.combo_global_exit)
        layout.addWidget(gb_set)

        layout.addWidget(QLabel("Werkzeuge:"))
        self.start_area_button = self._create_tool_btn("1. Startfläche")
        self.btn_start_route = self._create_tool_btn("2. Start-Route (Zulauf)")
        self.new_route_button = self._create_tool_btn("3. Shop-Route (Regale)")
        self.place_shelves_button = self._create_tool_btn(
            "4. Regale platzieren"
        )
        self.waiting_area_button = self._create_tool_btn(
            "5. Wartebereich (Kassen)"
        )
        self.btn_exit_route = self._create_tool_btn("6. Ausgangs-Route")
        self.btn_exit_area = self._create_tool_btn("7. Ausgangsfläche")

        for b in [
            self.start_area_button,
            self.btn_start_route,
            self.new_route_button,
            self.place_shelves_button,
            self.waiting_area_button,
            self.btn_exit_route,
            self.btn_exit_area,
        ]:
            layout.addWidget(b)

        layout.addSpacing(5)
        self.btn_visibility = QPushButton("👁️ Sichtbarkeit")
        self.btn_offsets = QPushButton("📏 Globale Offsets")
        self.btn_config_sizes = QPushButton("⚙️ Größen & Skalierung")
        layout.addWidget(self.btn_visibility)
        layout.addWidget(self.btn_offsets)
        layout.addWidget(self.btn_config_sizes)

        layout.addSpacing(15)
        layout.addWidget(QLabel("Kasse hinzufügen:"))
        row_k = QHBoxLayout()
        self.btn_kl = self._create_tool_btn("Normal (L)")
        self.btn_kr = self._create_tool_btn("Normal (R)")
        self.btn_sl = self._create_tool_btn("SB (L)")
        self.btn_sr = self._create_tool_btn("SB (R)")
        for b in [self.btn_kl, self.btn_kr, self.btn_sl, self.btn_sr]:
            row_k.addWidget(b)
        layout.addLayout(row_k)

        self.admin_toolbar = QGroupBox("Route aktiv")
        self.admin_toolbar.setStyleSheet(
            f"border: 1px solid {COLOR_ORANGE.name()}; background-color: {COLOR_BG_PANEL.name()};"
        )
        l_adm = QVBoxLayout(self.admin_toolbar)
        row_adm = QHBoxLayout()
        self.btn_save_admin = QPushButton("Speichern (OK)")
        self.btn_save_admin.setStyleSheet(
            f"background-color: {COLOR_SUCCESS.name()}; color: white; font-weight: bold;"
        )
        self.btn_cancel_route = QPushButton("Abbrechen")
        self.btn_cancel_route.setStyleSheet(
            f"color: {COLOR_ERROR.name()}; font-weight: bold;"
        )
        row_adm.addWidget(self.btn_save_admin)
        row_adm.addWidget(self.btn_cancel_route)
        l_adm.addLayout(row_adm)
        layout.addWidget(self.admin_toolbar)
        self.admin_toolbar.hide()

        scroll.setWidget(widget)
        self.control_tabs.addTab(scroll, "Editor")

    def _init_data_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.list_tabs = QTabWidget()
        w_r = QWidget()
        l_r = QVBoxLayout(w_r)
        self.route_list_widget = QListWidget()
        self.btn_del_route = QPushButton("Route Löschen")
        self.btn_del_route.setStyleSheet(f"color: {COLOR_ERROR.name()};")
        l_r.addWidget(self.route_list_widget)
        l_r.addWidget(self.btn_del_route)
        self.list_tabs.addTab(w_r, "Routen")
        w_o = QWidget()
        l_o = QVBoxLayout(w_o)
        self.object_list_widget = QListWidget()
        self.btn_edit_obj = QPushButton("Position bearbeiten")
        self.btn_del_obj = QPushButton("Objekt Löschen")
        self.btn_del_obj.setStyleSheet(f"color: {COLOR_ERROR.name()};")
        l_o.addWidget(self.object_list_widget)
        l_o.addWidget(self.btn_edit_obj)
        l_o.addWidget(self.btn_del_obj)
        self.list_tabs.addTab(w_o, "Items")
        layout.addWidget(self.list_tabs)
        self.control_tabs.addTab(widget, "Daten")

    # Helpers
    def _create_time_edit(self, time_tuple):
        te = QTimeEdit()
        te.setDisplayFormat("HH:mm")
        te.setTime(QTime(*time_tuple))
        te.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        return te

    def _create_spin(self, val, min_v, max_v, suffix=""):
        sb = QSpinBox()
        sb.setRange(min_v, max_v)
        sb.setValue(val)
        if suffix:
            sb.setSuffix(suffix)
        sb.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        return sb

    def _create_double_spin(self, val, min_v, max_v, suffix=""):
        sb = QDoubleSpinBox()
        sb.setRange(min_v, max_v)
        sb.setValue(val)
        sb.setSingleStep(0.1)
        if suffix:
            sb.setSuffix(suffix)
        sb.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        return sb

    def _create_help_label(self, tooltip):
        l = QLabel("❓")
        l.setStyleSheet("color: #3B82F6; font-weight: bold;")
        # FIX: Richtige Konstante für den Cursor
        l.setCursor(Qt.CursorShape.WhatsThisCursor)
        l.setToolTip(tooltip)
        l.setFixedWidth(20)
        return l

    def _create_dist_row(self, label, val_mean, val_std, layout, tooltip=None):
        h = QHBoxLayout()
        # FIX: Margins entfernen für saubere Ausrichtung
        h.setContentsMargins(0, 0, 0, 0)
        sb_mean = self._create_double_spin(val_mean, 0.1, 20.0)
        sb_std = self._create_double_spin(val_std, 0.0, 5.0)
        h.addWidget(QLabel("Ø:"))
        h.addWidget(sb_mean)
        h.addWidget(QLabel("σ:"))
        h.addWidget(sb_std)
        if tooltip:
            h.addWidget(self._create_help_label(tooltip))
        layout.addRow(label, h)
        return sb_mean, sb_std

    def _create_range_row(self, label, val_min, val_max, layout, tooltip=None):
        h = QHBoxLayout()
        # FIX: Margins entfernen für saubere Ausrichtung
        h.setContentsMargins(0, 0, 0, 0)
        sb_min = self._create_double_spin(val_min, 0.1, 10.0)
        sb_max = self._create_double_spin(val_max, 0.1, 10.0)
        h.addWidget(QLabel("Min:"))
        h.addWidget(sb_min)
        h.addWidget(QLabel("Max:"))
        h.addWidget(sb_max)
        if tooltip:
            h.addWidget(self._create_help_label(tooltip))
        layout.addRow(label, h)
        return sb_min, sb_max

    def _create_tool_btn(self, text):
        b = QPushButton(text)
        b.setCheckable(True)
        return b

    def _header(self, text):
        l = QLabel(text)
        l.setStyleSheet("font-weight: bold; color: #374151; margin-top: 10px;")
        return l

    def _sublabel(self, text):
        l = QLabel(text)
        l.setStyleSheet(
            "color: #6B7280; font-style: italic; font-size: 12px; margin-bottom: 2px;"
        )
        return l

    def _create_bold_label(self, text, color=None):
        l = QLabel(text)
        style = "font-weight: bold; font-size: 14px;"
        if color:
            style += f" color: {color};"
        l.setStyleSheet(style)
        return l
