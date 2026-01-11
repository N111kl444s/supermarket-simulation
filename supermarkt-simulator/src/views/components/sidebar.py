"""
Sidebar Component.
Contains the TabWidget with Input, Simulation, Statistics, Editor, and Data tabs.
Updated: Default background scale UI set to 0.5.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QScrollArea, QGroupBox, QFormLayout, 
    QTimeEdit, QSpinBox, QDoubleSpinBox, QLabel, QHBoxLayout, QListWidget,
    QPushButton, QComboBox, QSizePolicy
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
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content.setObjectName("ConfigContent")
        layout = QVBoxLayout(content)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(12)

        # Öffnungszeiten
        gb_time = QGroupBox("Öffnungszeiten")
        f_time = QFormLayout(gb_time)
        self.time_open = self._create_time_edit(DEFAULT_OPEN_TIME)
        self.time_close = self._create_time_edit(DEFAULT_CLOSE_TIME)
        f_time.addRow("Öffnen:", self.time_open)
        f_time.addRow("Schließen:", self.time_close)
        layout.addWidget(gb_time)

        # Kunden
        gb_cust = QGroupBox("Kunden Konfiguration")
        l_cust = QVBoxLayout(gb_cust)
        
        l_cust.addWidget(self._header("Kundendichte & Generierung"))
        l_cust.addWidget(self._sublabel("(Exponentialverteilung)"))
        
        f_gen = QFormLayout()
        self.actor_count_input = self._create_spin(50, 1, 10000, " / Tag")
        self.disabled_prob_input = self._create_double_spin(10, 0, 100, " %")
        f_gen.addRow("Anzahl:", self.actor_count_input)
        f_gen.addRow("Behinderung:", self.disabled_prob_input)
        l_cust.addLayout(f_gen)

        l_cust.addWidget(self._header("Bewegungsgeschwindigkeit (px/s)"))
        f_move = QFormLayout()
        self.speed_walk_mean, self.speed_walk_std = self._create_dist_row("Gehen:", 2.5, 0.5, f_move)
        self.speed_roll_mean, self.speed_roll_std = self._create_dist_row("Rollen:", 1.5, 0.3, f_move)
        l_cust.addLayout(f_move)

        l_cust.addWidget(self._header("Einkauf"))
        f_shop = QFormLayout()
        self.items_mean = self._create_spin(12, 1, 100)
        self.items_std = self._create_double_spin(4.0, 0, 20)
        row = QHBoxLayout()
        row.addWidget(QLabel("Ø:"))
        row.addWidget(self.items_mean)
        row.addWidget(QLabel("σ:"))
        row.addWidget(self.items_std)
        f_shop.addRow("Artikelanzahl:", row)
        
        self.hand_scanner_prob = self._create_double_spin(5.0, 0, 100, " %")
        f_shop.addRow("Handscanner:", self.hand_scanner_prob)
        l_cust.addLayout(f_shop)

        l_cust.addWidget(self._header("Scannen (Dauer in Sek)"))
        f_scan = QFormLayout()
        self.scan_speed_normal_min, self.scan_speed_normal_max = self._create_range_row("Normal:", 0.5, 1.5, f_scan)
        self.scan_speed_disabled_min, self.scan_speed_disabled_max = self._create_range_row("Behindert:", 1.0, 3.0, f_scan)
        l_cust.addLayout(f_scan)
        layout.addWidget(gb_cust)

        # Personal
        gb_staff = QGroupBox("Personal Konfiguration")
        l_staff = QVBoxLayout(gb_staff)
        l_staff.addWidget(self._header("Scangeschwindigkeit (Sek/Artikel)"))
        f_staff = QFormLayout()
        self.scan_speed_newbie_min, self.scan_speed_newbie_max = self._create_range_row("Azubi:", 1.5, 2.5, f_staff)
        self.scan_speed_pro_min, self.scan_speed_pro_max = self._create_range_row("Festangestellt:", 0.8, 1.2, f_staff)
        l_staff.addLayout(f_staff)
        layout.addWidget(gb_staff)

        # Kassen
        gb_co = QGroupBox("Kassen Eigenschaften")
        f_co = QFormLayout(gb_co)
        self.checkout_fail_rate_normal = self._create_spin(0, 0, 100, " %")
        self.checkout_fail_rate_sb = self._create_spin(0, 0, 100, " %")
        f_co.addRow("Ausfall (Normal):", self.checkout_fail_rate_normal)
        f_co.addRow("Ausfall (SB):", self.checkout_fail_rate_sb)
        layout.addWidget(gb_co)

        scroll.setWidget(content)
        self.control_tabs.addTab(scroll, "Eingabe")

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
        self.plot_widget.getAxis("bottom").setPen(pg.mkPen(color=COLOR_TEXT_MAIN))
        self.plot_widget.getAxis("left").setPen(pg.mkPen(color=COLOR_TEXT_MAIN))
        layout.addWidget(self.plot_widget)
        self.control_tabs.addTab(widget, "Statistiken")

    def _init_editor_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Map Verwaltung
        gb_map = QGroupBox("Map-Verwaltung")
        l_map = QVBoxLayout(gb_map)
        r1 = QHBoxLayout()
        self.btn_new_map = QPushButton("Neu")
        self.btn_save_map = QPushButton("Speichern")
        self.btn_delete_map = QPushButton("Löschen")
        self.btn_delete_map.setStyleSheet(f"color: {COLOR_ERROR.name()}; border-color: {COLOR_ERROR.name()};")
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
        # UPDATE: Standard auf 0.5
        self.spin_bg_scale = self._create_double_spin(0.5, 0.1, 10.0)
        r3.addWidget(self.spin_bg_scale)
        l_map.addLayout(r3)
        layout.addWidget(gb_map)

        # Settings
        gb_set = QGroupBox("Map Einstellungen")
        f_set = QFormLayout(gb_set)
        self.combo_global_exit = QComboBox()
        self.combo_global_exit.addItems(["Links", "Rechts", "Oben", "Unten"])
        self.combo_global_exit.setCurrentText("Rechts")
        f_set.addRow("Abgangsrichtung:", self.combo_global_exit)
        layout.addWidget(gb_set)

        # Tools
        layout.addWidget(QLabel("Werkzeuge:"))
        self.start_area_button = self._create_tool_btn("1. Startfläche")
        self.btn_start_route = self._create_tool_btn("2. Start-Route (Zulauf)")
        self.new_route_button = self._create_tool_btn("3. Shop-Route (Regale)")
        self.place_shelves_button = self._create_tool_btn("4. Regale platzieren")
        self.waiting_area_button = self._create_tool_btn("5. Wartebereich (Kassen)")
        self.btn_exit_route = self._create_tool_btn("6. Ausgangs-Route")
        self.btn_exit_area = self._create_tool_btn("7. Ausgangsfläche")
        
        for b in [self.start_area_button, self.btn_start_route, self.new_route_button, 
                  self.place_shelves_button, self.waiting_area_button, self.btn_exit_route, self.btn_exit_area]:
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
        for b in [self.btn_kl, self.btn_kr, self.btn_sl, self.btn_sr]: row_k.addWidget(b)
        layout.addLayout(row_k)

        # Admin Toolbar (Hidden)
        self.admin_toolbar = QGroupBox("Route aktiv")
        self.admin_toolbar.setStyleSheet(f"border: 1px solid {COLOR_ORANGE.name()}; background-color: {COLOR_BG_PANEL.name()};")
        l_adm = QVBoxLayout(self.admin_toolbar)
        row_adm = QHBoxLayout()
        self.btn_save_admin = QPushButton("Speichern (OK)")
        self.btn_save_admin.setStyleSheet(f"background-color: {COLOR_SUCCESS.name()}; color: white; font-weight: bold;")
        self.btn_cancel_route = QPushButton("Abbrechen")
        self.btn_cancel_route.setStyleSheet(f"color: {COLOR_ERROR.name()}; font-weight: bold;")
        row_adm.addWidget(self.btn_save_admin)
        row_adm.addWidget(self.btn_cancel_route)
        l_adm.addLayout(row_adm)
        layout.addWidget(self.admin_toolbar)
        self.admin_toolbar.hide()

        self.control_tabs.addTab(widget, "Editor")

    def _init_data_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.list_tabs = QTabWidget()
        
        # Routes List
        w_r = QWidget()
        l_r = QVBoxLayout(w_r)
        self.route_list_widget = QListWidget()
        self.btn_del_route = QPushButton("Route Löschen")
        self.btn_del_route.setStyleSheet(f"color: {COLOR_ERROR.name()};")
        l_r.addWidget(self.route_list_widget)
        l_r.addWidget(self.btn_del_route)
        self.list_tabs.addTab(w_r, "Routen")
        
        # Items List
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

    # --- Helpers ---
    def _create_time_edit(self, time_tuple):
        te = QTimeEdit()
        te.setDisplayFormat("HH:mm")
        te.setTime(QTime(*time_tuple))
        te.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return te

    def _create_spin(self, val, min_v, max_v, suffix=""):
        sb = QSpinBox()
        sb.setRange(min_v, max_v)
        sb.setValue(val)
        if suffix: sb.setSuffix(suffix)
        sb.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return sb

    def _create_double_spin(self, val, min_v, max_v, suffix=""):
        sb = QDoubleSpinBox()
        sb.setRange(min_v, max_v)
        sb.setValue(val)
        sb.setSingleStep(0.1)
        if suffix: sb.setSuffix(suffix)
        sb.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return sb

    def _create_dist_row(self, label, val_mean, val_std, layout):
        h = QHBoxLayout()
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
        l.setStyleSheet("color: #6B7280; font-style: italic; font-size: 12px; margin-bottom: 2px;")
        return l

    def _create_bold_label(self, text, color=None):
        l = QLabel(text)
        style = "font-weight: bold; font-size: 14px;"
        if color: style += f" color: {color};"
        l.setStyleSheet(style)
        return l