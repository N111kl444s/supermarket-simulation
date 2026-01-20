"""
Sidebar Component.
Refactored:
- Layout cleanup: Tooltips (Help Icons) moved next to distribution labels.
- Added explicit "(Normalverteilung)" label to Movement section.
- Removed tooltips from individual input rows for cleaner look.
- Helper method `_add_sublabel_with_help` introduced.
- FIX: Replaced emoji label with robust QToolButton using standard Qt Help Icon.
- FIX: Consistent margins/spacing for all spinbox rows.
- NEW: Added Payment Configuration (Cash/Card percentages linked to sum 100%).
- NEW: Added Payment Duration settings (Min/Max).
- NEW: Added Maintenance Duration settings in 'Laden' tab.
- NEW: Added Editor tools for Worker Spawn and Routes.
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
    QStyle,
    QToolButton,
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
        lbl_hint = QLabel("Konfigurieren Sie hier die Simulationsparameter.\nNutzen Sie die Tabs unten für Details.")
        lbl_hint.setStyleSheet("color: #555; font-style: italic; margin-bottom: 2px;")
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

        # Störung & Wartung (NEU)
        gb_co = QGroupBox("Störungen & Kassen")
        l_co = QVBoxLayout(gb_co)
        
        f_co = QFormLayout()
        self.checkout_fail_rate_normal = self._create_spin(0, 0, 100, " %")
        self.checkout_fail_rate_sb = self._create_spin(0, 0, 100, " %")
        f_co.addRow("Ausfall (Normal):", self.checkout_fail_rate_normal)
        f_co.addRow("Ausfall (SB):", self.checkout_fail_rate_sb)
        l_co.addLayout(f_co)
        
        self._add_sublabel_with_help(l_co, "Wartungsdauer (Gleichverteilung)",
            "<b>Dauer der Reparatur</b><br>"
            "Zeit, die der Arbeiter an der Kasse verbringt."
        )
        f_maint = QFormLayout()
        self.maintain_duration_min, self.maintain_duration_max = (
            self._create_range_row("Dauer (s):", 20.0, 60.0, f_maint)
        )
        l_co.addLayout(f_maint)
        
        l_shop.addWidget(gb_co)

        input_tabs.addTab(tab_shop, "Laden")

        # --- SUB-TAB 2: KUNDEN ---
        tab_cust_container = QWidget()
        l_cust_cont = QVBoxLayout(tab_cust_container)
        l_cust_cont.setContentsMargins(0, 0, 0, 0)
        
        scroll_cust = QScrollArea()
        scroll_cust.setWidgetResizable(True)
        scroll_cust.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        content_cust = QWidget()
        content_cust.setStyleSheet("background-color: transparent;") 
        
        l_gb_cust = QVBoxLayout(content_cust)
        l_gb_cust.setAlignment(Qt.AlignmentFlag.AlignTop)
        l_gb_cust.setContentsMargins(5, 15, 5, 5)

        # Kundendichte
        l_gb_cust.addWidget(self._header("Kundendichte & Generierung"))
        self._add_sublabel_with_help(l_gb_cust, "(Exponentialverteilung)",
            "<b>Exponentialverteilung (Simulation)</b><br>"
            "Berechnet den Zeitabstand zwischen zwei Kunden.<br>"
            "<i>Formel:</i> <code>Interval = (Zeit / Anzahl) * random.uniform(0.7, 1.3)</code>"
        )
        f_gen = QFormLayout()
        self.actor_count_input = self._create_spin(50, 1, 10000, " / Tag")
        self.disabled_prob_input = self._create_double_spin(10, 0, 100, " %")
        f_gen.addRow("Anzahl:", self.actor_count_input)
        f_gen.addRow("Behinderung:", self.disabled_prob_input)
        l_gb_cust.addLayout(f_gen)

        # Geschwindigkeit
        l_gb_cust.addWidget(self._header("Bewegungsgeschwindigkeit (px/s)"))
        self._add_sublabel_with_help(l_gb_cust, "(Normalverteilung)",
            "<b>Normalverteilung (Gauß)</b><br>"
            "Geschwindigkeit zufällig um den Mittelwert gestreut.<br>"
            "<i>Formel:</i> <code>v = random.normalvariate(Ø, σ)</code>"
        )
        f_move = QFormLayout()
        self.speed_walk_mean, self.speed_walk_std = self._create_dist_row(
            "Gehen:", 2.5, 0.5, f_move
        )
        self.speed_roll_mean, self.speed_roll_std = self._create_dist_row(
            "Rollen:", 1.5, 0.3, f_move
        )
        l_gb_cust.addLayout(f_move)

        # Einkauf
        l_gb_cust.addWidget(self._header("Einkauf"))
        self._add_sublabel_with_help(l_gb_cust, "(Normalverteilung)",
            "<b>Normalverteilung</b><br>"
            "Bestimmt die Anzahl der Artikel im Einkaufswagen.<br>"
            "<i>Formel:</i> <code>items = int(random.normalvariate(Ø, σ))</code>"
        )
        f_shop = QFormLayout()
        self.items_mean = self._create_spin(12, 1, 100)
        self.items_std = self._create_double_spin(4.0, 0, 20)
        
        row_items = QHBoxLayout()
        row_items.setContentsMargins(0, 0, 0, 0)
        row_items.setSpacing(5)
        row_items.addWidget(QLabel("Ø:"))
        row_items.addWidget(self.items_mean)
        row_items.addWidget(QLabel("σ:"))
        row_items.addWidget(self.items_std)
        
        f_shop.addRow("Artikelanzahl:", row_items)
        self.hand_scanner_prob = self._create_double_spin(5.0, 0, 100, " %")
        f_shop.addRow("Handscanner:", self.hand_scanner_prob)
        l_gb_cust.addLayout(f_shop)

        # Scannen
        l_gb_cust.addWidget(self._header("Scannen (Dauer in Sek)"))
        self._add_sublabel_with_help(l_gb_cust, "(Gleichverteilung)",
            "<b>Gleichverteilung</b><br>"
            "Jeder Artikel braucht eine zufällige Zeit zwischen Min und Max.<br>"
            "<i>Formel:</i> <code>t = random.uniform(Min, Max)</code>"
        )
        f_scan = QFormLayout()
        self.scan_speed_normal_min, self.scan_speed_normal_max = (
            self._create_range_row("Normal:", 0.5, 1.5, f_scan)
        )
        self.scan_speed_disabled_min, self.scan_speed_disabled_max = (
            self._create_range_row("Behindert:", 1.0, 3.0, f_scan)
        )
        l_gb_cust.addLayout(f_scan)

        # Bezahlmethoden
        l_gb_cust.addWidget(self._header("Bezahlmethoden & Dauer"))
        self._add_sublabel_with_help(l_gb_cust, "(Abhängigkeit & Gleichverteilung)",
            "<b>Bargeld vs. Karte</b><br>"
            "Muss zusammen 100% ergeben.<br><br>"
            "<b>Bezahldauer</b><br>"
            "Zeit an der Kasse nach dem Scannen."
        )
        f_pay = QFormLayout()
        
        self.prob_cash = self._create_spin(30, 0, 100, " %")
        self.prob_card = self._create_spin(70, 0, 100, " %")
        
        self.prob_cash.valueChanged.connect(self._on_cash_changed)
        self.prob_card.valueChanged.connect(self._on_card_changed)

        f_pay.addRow("Bargeld:", self.prob_cash)
        f_pay.addRow("Kreditkarte:", self.prob_card)
        l_gb_cust.addLayout(f_pay)

        f_pay_dur = QFormLayout()
        self.pay_duration_cash_min, self.pay_duration_cash_max = (
            self._create_range_row("Dauer Bargeld (s):", 5.0, 15.0, f_pay_dur)
        )
        self.pay_duration_card_min, self.pay_duration_card_max = (
            self._create_range_row("Dauer Karte (s):", 3.0, 8.0, f_pay_dur)
        )
        l_gb_cust.addLayout(f_pay_dur)
        
        scroll_cust.setWidget(content_cust)
        l_cust_cont.addWidget(scroll_cust)
        input_tabs.addTab(tab_cust_container, "Kunden")

        # --- SUB-TAB 3: PERSONAL ---
        tab_staff = QWidget()
        l_staff = QVBoxLayout(tab_staff)
        l_staff.setAlignment(Qt.AlignmentFlag.AlignTop)
        l_staff.setContentsMargins(5, 15, 5, 5)
        
        l_staff.addWidget(self._header("Scangeschwindigkeit (Sek/Artikel)"))
        self._add_sublabel_with_help(l_staff, "(Gleichverteilung)",
            "<b>Gleichverteilung</b><br>"
            "Scan-Dauer pro Artikel an bedienter Kasse.<br>"
            "<i>Formel:</i> <code>t = random.uniform(Min, Max)</code>"
        )
        f_staff = QFormLayout()
        self.scan_speed_newbie_min, self.scan_speed_newbie_max = (
            self._create_range_row("Azubi:", 1.5, 2.5, f_staff)
        )
        self.scan_speed_pro_min, self.scan_speed_pro_max = (
            self._create_range_row("Festangestellt:", 0.8, 1.2, f_staff)
        )
        l_staff.addLayout(f_staff)
        
        input_tabs.addTab(tab_staff, "Personal")

        layout_container.addWidget(input_tabs)
        self.control_tabs.addTab(container, "Eingabe")

    # --- Event Handler für Bezahlmethoden ---
    def _on_cash_changed(self, val):
        self.prob_card.blockSignals(True)
        self.prob_card.setValue(100 - val)
        self.prob_card.blockSignals(False)

    def _on_card_changed(self, val):
        self.prob_cash.blockSignals(True)
        self.prob_cash.setValue(100 - val)
        self.prob_cash.blockSignals(False)

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

        # NEU: Arbeiter Tools
        layout.addSpacing(5)
        layout.addWidget(QLabel("Arbeiter / Wartung:"))
        row_worker = QHBoxLayout()
        self.btn_worker_spawn = self._create_tool_btn("👷 Startpunkt")
        self.btn_worker_route = self._create_tool_btn("🚧 Wartungs-Route")
        row_worker.addWidget(self.btn_worker_spawn)
        row_worker.addWidget(self.btn_worker_route)
        layout.addLayout(row_worker)

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
        # FIX: Verwende QToolButton mit Standard-Icon für sauberes Rendering
        btn = QToolButton()
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxQuestion)
        btn.setIcon(icon)
        btn.setCursor(Qt.CursorShape.WhatsThisCursor)
        btn.setToolTip(tooltip)
        # Transparent und ohne Border, damit es wie ein Icon wirkt
        btn.setStyleSheet("border: none; background-color: transparent;")
        btn.setFixedSize(24, 24)
        return btn

    def _add_sublabel_with_help(self, layout, text, tooltip):
        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(5)
        
        lbl = self._sublabel(text) # Returns a QLabel
        h.addWidget(lbl)
        
        if tooltip:
            icon = self._create_help_label(tooltip)
            h.addWidget(icon)
        
        h.addStretch() # Align to left
        layout.addLayout(h)

    def _create_dist_row(self, label, val_mean, val_std, layout):
        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(5)
        sb_mean = self._create_double_spin(val_mean, 0.1, 20.0)
        sb_std = self._create_double_spin(val_std, 0.0, 5.0)
        h.addWidget(QLabel("Ø:"))
        h.addWidget(sb_mean)
        h.addWidget(QLabel("σ:"))
        h.addWidget(sb_std)
        layout.addRow(label, h)
        return sb_mean, sb_std

    def _create_range_row(self, label, val_min, val_max, layout):
        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(5)
        sb_min = self._create_double_spin(val_min, 0.1, 10.0)
        sb_max = self._create_double_spin(val_max, 0.1, 10.0)
        h.addWidget(QLabel("Min:"))
        h.addWidget(sb_min)
        h.addWidget(QLabel("Max:"))
        h.addWidget(sb_max)
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