"""
Sidebar Component.
Refactored:
- FEATURE: Added 'btn_worker_route' to Editor -> Routen Tab.
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
    QFrame,
    QApplication,
    QStyle,
)
from PyQt6.QtCore import QTime, Qt
from config import COLOR_ACCENT


class Sidebar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.apply_styles()

    def apply_styles(self):
        accent = COLOR_ACCENT.name()
        self.setStyleSheet(
            f"""
            Sidebar {{
                background-color: #FFFFFF;
                border-right: 1px solid #D1D5DB;
            }}
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollArea > QWidget > QWidget {{
                background: transparent;
            }}
            
            QPushButton.HeaderBtn {{
                background-color: #FFFFFF;
                border: 1px solid #D1D5DB;
                border-radius: 8px;
                font-weight: 700;
                color: #4B5563;
                font-size: 14px;
                height: 44px;
            }}
            QPushButton.HeaderBtn:checked {{
                background-color: {accent};
                color: white;
                border: 1px solid {accent};
            }}
            QPushButton#BtnLang {{
                font-size: 26px;
                padding-bottom: 2px;
            }}

            QTabWidget::pane {{
                border: 1px solid #D1D5DB;
                background: #FFFFFF;
                border-radius: 4px;
                margin-top: 6px; 
            }}
            QTabBar::tab {{
                background: #E5E7EB;
                border: 1px solid #D1D5DB;
                padding: 8px 12px;
                border-bottom: none;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background: #FFFFFF;
                border-bottom: 1px solid #FFFFFF; 
                font-weight: bold;
            }}
            
            QGroupBox {{
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 5px; 
                font-weight: bold;
                background-color: #F9FAFB; 
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 5px;
                color: #374151;
            }}
        """
        )

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # === HEADER ===
        self.setup_header(main_layout)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #E5E7EB;")
        main_layout.addWidget(line)

        # === MAIN TABS ===
        self.main_tabs = QTabWidget()
        main_layout.addWidget(self.main_tabs)

        self._init_tab_input()
        self._init_tab_stats()
        self._init_tab_editor()

    def setup_header(self, layout):
        h_layout = QHBoxLayout()
        h_layout.setSpacing(10)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Simulation", "Editor"])
        self.mode_combo.setVisible(False)
        layout.addWidget(self.mode_combo)

        self.mode_group = QButtonGroup(self)

        self.btn_mode_sim = QPushButton("Simulation")
        self.btn_mode_sim.setProperty("class", "HeaderBtn")
        self.btn_mode_sim.setCheckable(True)
        self.btn_mode_sim.setChecked(True)
        self.btn_mode_sim.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_sim.setStyleSheet(
            "border-top-right-radius: 0; border-bottom-right-radius: 0; border-right: none;"
        )

        self.btn_mode_edit = QPushButton("Editor")
        self.btn_mode_edit.setProperty("class", "HeaderBtn")
        self.btn_mode_edit.setCheckable(True)
        self.btn_mode_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_edit.setStyleSheet(
            "border-top-left-radius: 0; border-bottom-left-radius: 0;"
        )

        self.mode_group.addButton(self.btn_mode_sim)
        self.mode_group.addButton(self.btn_mode_edit)

        self.btn_mode_sim.clicked.connect(
            lambda: self.mode_combo.setCurrentIndex(0)
        )
        self.btn_mode_edit.clicked.connect(
            lambda: self.mode_combo.setCurrentIndex(1)
        )
        self.mode_combo.currentIndexChanged.connect(self._sync_mode_buttons)

        h_mode = QHBoxLayout()
        h_mode.setSpacing(0)
        h_mode.addWidget(self.btn_mode_sim)
        h_mode.addWidget(self.btn_mode_edit)
        h_layout.addLayout(h_mode, 1)

        self.btn_lang = QPushButton("🇩🇪")
        self.btn_lang.setObjectName("BtnLang")
        self.btn_lang.setProperty("class", "HeaderBtn")
        self.btn_lang.setCheckable(False)
        self.btn_lang.setFixedWidth(60)
        self.btn_lang.clicked.connect(self._toggle_lang)
        h_layout.addWidget(self.btn_lang, 0)

        layout.addLayout(h_layout)

    def _init_tab_input(self):
        tab_input_container = QWidget()
        l_input_main = QVBoxLayout(tab_input_container)
        l_input_main.setContentsMargins(0, 5, 0, 0)

        self.input_sub_tabs = QTabWidget()
        l_input_main.addWidget(self.input_sub_tabs)

        self._setup_shop_tab()
        self._setup_cust_tab()
        self._setup_staff_tab()

        self.main_tabs.addTab(tab_input_container, "Eingabe")

    def _setup_shop_tab(self):
        sub_shop = QWidget()
        l_shop = QVBoxLayout(sub_shop)
        l_shop.setAlignment(Qt.AlignmentFlag.AlignTop)

        gb_map = QGroupBox("Karte wählen")
        v_map = QVBoxLayout(gb_map)
        self.map_combo = QComboBox()
        v_map.addWidget(self.map_combo)
        l_shop.addWidget(gb_map)

        gb_time = QGroupBox("Zeitsteuerung")
        v_time = QVBoxLayout(gb_time)
        f_time = QFormLayout()
        self.time_open = QTimeEdit(QTime(8, 0))
        self.time_close = QTimeEdit(QTime(20, 0))
        f_time.addRow("Öffnen:", self.time_open)
        f_time.addRow("Schließen:", self.time_close)
        v_time.addLayout(f_time)
        l_shop.addWidget(gb_time)

        gb_co = QGroupBox("Kassenstörungen")
        v_co = QVBoxLayout(gb_co)
        self._add_gb_header(
            v_co,
            "(Wahrscheinlichkeit in %)",
            "Chance, dass eine Kasse pro Minute ausfällt.",
        )
        f_co = QFormLayout()
        self.checkout_fail_rate_normal = self._create_spin(0, 0, 100, " %")
        self.checkout_fail_rate_sb = self._create_spin(0, 0, 100, " %")
        f_co.addRow("Ausfall (Normal):", self.checkout_fail_rate_normal)
        f_co.addRow("Ausfall (SB):", self.checkout_fail_rate_sb)
        v_co.addLayout(f_co)
        l_shop.addWidget(gb_co)

        self.input_sub_tabs.addTab(sub_shop, "Laden")

    def _setup_cust_tab(self):
        tab_cust_container = QWidget()
        l_cust_cont = QVBoxLayout(tab_cust_container)
        l_cust_cont.setContentsMargins(0, 0, 0, 0)
        scroll_cust = QScrollArea()
        scroll_cust.setWidgetResizable(True)
        content_cust = QWidget()
        l_gb_cust = QVBoxLayout(content_cust)
        l_gb_cust.setAlignment(Qt.AlignmentFlag.AlignTop)
        l_gb_cust.setSpacing(15)

        gb_spawn = QGroupBox("Kundenaufkommen")
        v_spawn = QVBoxLayout(gb_spawn)
        self._add_gb_header(
            v_spawn, "(Exponentialverteilung)", "Zeitabstände zwischen Kunden."
        )
        f_spawn = QFormLayout()
        self.actor_count_input = self._create_spin(50, 1, 10000)
        self.disabled_prob_input = self._create_spin(10, 0, 100, " %")
        f_spawn.addRow("Kunden / Tag:", self.actor_count_input)
        f_spawn.addRow("Anteil Beeintr.:", self.disabled_prob_input)
        v_spawn.addLayout(f_spawn)
        l_gb_cust.addWidget(gb_spawn)

        gb_speed = QGroupBox("Geschwindigkeit")
        v_speed = QVBoxLayout(gb_speed)
        self._add_gb_header(v_speed, "(Normalverteilung)", "Gauß-Verteilung.")
        f_speed = QFormLayout()
        self.speed_walk_mean, self.speed_walk_std = self._create_dist_row(
            "Gehen:", 2.5, 0.5, f_speed
        )
        self.speed_roll_mean, self.speed_roll_std = self._create_dist_row(
            "Rollen:", 1.5, 0.3, f_speed
        )
        v_speed.addLayout(f_speed)
        l_gb_cust.addWidget(gb_speed)

        gb_cart = QGroupBox("Einkaufswagen")
        v_cart = QVBoxLayout(gb_cart)
        self._add_gb_header(
            v_cart, "(Normalverteilung)", "Anzahl der Artikel im Wagen."
        )
        f_cart = QFormLayout()
        self.items_mean = self._create_spin(15, 1, 100)
        self.items_std = self._create_double_spin(5.0, 0, 50)
        h_it = QHBoxLayout()
        h_it.addWidget(QLabel("Ø:"))
        h_it.addWidget(self.items_mean)
        h_it.addWidget(QLabel("σ:"))
        h_it.addWidget(self.items_std)
        f_cart.addRow("Artikel:", h_it)
        self.hand_scanner_prob = self._create_spin(20, 0, 100, " %")
        f_cart.addRow("Handscanner:", self.hand_scanner_prob)
        v_cart.addLayout(f_cart)
        l_gb_cust.addWidget(gb_cart)

        gb_scan = QGroupBox("Scan-Dauer (Kunde)")
        v_scan = QVBoxLayout(gb_scan)
        self._add_gb_header(v_scan, "(Gleichverteilung)", "Zeit pro Artikel.")
        f_scan = QFormLayout()
        self.scan_speed_normal_min, self.scan_speed_normal_max = (
            self._create_range_row("Normal:", 0.5, 1.5, f_scan)
        )
        self.scan_speed_disabled_min, self.scan_speed_disabled_max = (
            self._create_range_row("Einges.:", 1.0, 3.0, f_scan)
        )
        v_scan.addLayout(f_scan)
        l_gb_cust.addWidget(gb_scan)

        gb_pay = QGroupBox("Zahlungsmethoden")
        v_pay = QVBoxLayout(gb_pay)
        self._add_gb_header(v_pay, "(Verteilung in %)", "Ergibt 100%.")
        f_pay = QFormLayout()
        self.payment_cash = self._create_double_spin(30.0, 0, 100, " %")
        self.payment_card = self._create_double_spin(70.0, 0, 100, " %")
        self.payment_cash.valueChanged.connect(
            lambda v: self.payment_card.setValue(100.0 - v)
        )
        self.payment_card.valueChanged.connect(
            lambda v: self.payment_cash.setValue(100.0 - v)
        )
        f_pay.addRow("Bargeld:", self.payment_cash)
        f_pay.addRow("Karte:", self.payment_card)
        v_pay.addLayout(f_pay)
        l_gb_cust.addWidget(gb_pay)

        scroll_cust.setWidget(content_cust)
        l_cust_cont.addWidget(scroll_cust)
        self.input_sub_tabs.addTab(tab_cust_container, "Kunden")

    def _setup_staff_tab(self):
        tab_staff = QWidget()
        l_staff = QVBoxLayout(tab_staff)
        l_staff.setAlignment(Qt.AlignmentFlag.AlignTop)
        l_staff.setSpacing(15)

        gb_cashier = QGroupBox("Kassierer Geschwindigkeit")
        v_cashier = QVBoxLayout(gb_cashier)
        self._add_gb_header(v_cashier, "(Sek/Artikel)", "Scan-Tempo.")
        f_cashier = QFormLayout()
        self.scan_speed_newbie_min, self.scan_speed_newbie_max = (
            self._create_range_row("Azubi:", 1.5, 2.5, f_cashier)
        )
        self.scan_speed_pro_min, self.scan_speed_pro_max = (
            self._create_range_row("Profi:", 0.8, 1.2, f_cashier)
        )
        v_cashier.addLayout(f_cashier)
        l_staff.addWidget(gb_cashier)

        gb_paytime = QGroupBox("Bezahldauer")
        v_paytime = QVBoxLayout(gb_paytime)
        self._add_gb_header(v_paytime, "(Sekunden)", "Dauer des Vorgangs.")
        f_paytime = QFormLayout()
        self.pay_duration_cash_min, self.pay_duration_cash_max = (
            self._create_range_row("Bargeld:", 3.0, 8.0, f_paytime)
        )
        self.pay_duration_card_min, self.pay_duration_card_max = (
            self._create_range_row("Karte:", 1.0, 4.0, f_paytime)
        )
        v_paytime.addLayout(f_paytime)
        l_staff.addWidget(gb_paytime)

        gb_maint = QGroupBox("Wartung / Reparatur")
        v_maint = QVBoxLayout(gb_maint)
        self._add_gb_header(v_maint, "(Sekunden)", "Reparaturdauer.")
        f_maint = QFormLayout()
        self.worker_repair_min, self.worker_repair_max = (
            self._create_range_row("Dauer:", 5.0, 15.0, f_maint)
        )
        v_maint.addLayout(f_maint)
        l_staff.addWidget(gb_maint)

        self.input_sub_tabs.addTab(tab_staff, "Personal")

    def _init_tab_stats(self):
        tab_stats = QWidget()
        l_stats = QVBoxLayout(tab_stats)
        l_stats.setSpacing(15)
        l_stats.setContentsMargins(10, 10, 10, 10)

        self.gb_stats = QGroupBox("Live Daten")
        self.lbl_queue_count = QLabel("0")
        self.lbl_customers_in_store = QLabel("0")
        self.lbl_total_customers = QLabel("0")

        f_stats_grid = QFormLayout(self.gb_stats)
        f_stats_grid.addRow("Kunden in Schlange:", self.lbl_queue_count)
        f_stats_grid.addRow("Kunden im Laden:", self.lbl_customers_in_store)
        f_stats_grid.addRow("Kunden Gesamt:", self.lbl_total_customers)
        l_stats.addWidget(self.gb_stats)

        gb_log = QGroupBox("Ereignis-Protokoll")
        l_log = QVBoxLayout(gb_log)
        self.list_log = QListWidget()
        self.list_log.setMinimumHeight(200)
        l_log.addWidget(self.list_log)
        l_stats.addWidget(gb_log)

        self.plot_widget = None
        l_stats.addStretch()
        self.main_tabs.addTab(tab_stats, "Statistiken")

    def _init_tab_editor(self):
        tab_editor_container = QWidget()
        l_editor_main = QVBoxLayout(tab_editor_container)
        l_editor_main.setContentsMargins(0, 5, 0, 0)
        self.editor_subtabs = QTabWidget()
        l_editor_main.addWidget(self.editor_subtabs)

        # Sub KARTE
        sub_map = QWidget()
        l_map = QVBoxLayout(sub_map)
        l_map.setAlignment(Qt.AlignmentFlag.AlignTop)

        gb_map_file = QGroupBox("Datei")
        l_map_file = QVBoxLayout(gb_map_file)
        self.btn_new_map = QPushButton("Neue Karte")
        self.btn_save_map = QPushButton("Karte Speichern")
        self.btn_delete_map = QPushButton("Karte Löschen")
        l_map_file.addWidget(self.btn_new_map)
        l_map_file.addWidget(self.btn_save_map)
        l_map_file.addWidget(self.btn_delete_map)
        l_map.addWidget(gb_map_file)

        gb_map_bg = QGroupBox("Hintergrund")
        l_map_bg = QVBoxLayout(gb_map_bg)
        self.btn_set_background = QPushButton("Bild laden...")
        self.btn_remove_background = QPushButton("Bild entfernen")
        h_scale = QHBoxLayout()
        h_scale.addWidget(QLabel("Zoom:"))
        self.spin_bg_scale = QDoubleSpinBox()
        self.spin_bg_scale.setRange(0.01, 5.0)
        self.spin_bg_scale.setSingleStep(0.01)
        self.spin_bg_scale.setDecimals(2)
        self.spin_bg_scale.setValue(1.0)
        h_scale.addWidget(self.spin_bg_scale)
        l_map_bg.addWidget(self.btn_set_background)
        l_map_bg.addWidget(self.btn_remove_background)
        l_map_bg.addLayout(h_scale)
        l_map.addWidget(gb_map_bg)

        gb_map_opts = QGroupBox("Optionen")
        l_map_opts = QVBoxLayout(gb_map_opts)
        self.btn_move_map = QPushButton("Karte verschieben")
        self.btn_move_map.setCheckable(True)
        h_exit = QHBoxLayout()
        h_exit.addWidget(QLabel("Exit Richtung:"))
        self.combo_global_exit = QComboBox()
        self.combo_global_exit.addItems(["Rechts", "Links", "Oben", "Unten"])
        h_exit.addWidget(self.combo_global_exit)
        l_map_opts.addWidget(self.btn_move_map)
        l_map_opts.addLayout(h_exit)
        l_map.addWidget(gb_map_opts)

        self.editor_subtabs.addTab(sub_map, "Karte")

        # Sub WERKZEUGE
        sub_areas = QWidget()
        l_areas = QVBoxLayout(sub_areas)
        l_areas.setAlignment(Qt.AlignmentFlag.AlignTop)

        gb_areas = QGroupBox("Flächen zeichnen")
        l_areas_btn = QVBoxLayout(gb_areas)
        self.start_area_button = QPushButton("Start-Bereich")
        self.start_area_button.setCheckable(True)
        self.waiting_area_button = QPushButton("Warte-Bereich")
        self.waiting_area_button.setCheckable(True)
        self.btn_exit_area = QPushButton("Ausgangs-Bereich")
        self.btn_exit_area.setCheckable(True)
        self.btn_worker_area = QPushButton("Wartungs-Bereich")
        self.btn_worker_area.setCheckable(True)
        self.btn_worker_area.setStyleSheet(
            "QPushButton:checked { background-color: #F59E0B; color: white; }"
        )
        l_areas_btn.addWidget(self.start_area_button)
        l_areas_btn.addWidget(self.waiting_area_button)
        l_areas_btn.addWidget(self.btn_exit_area)
        l_areas_btn.addWidget(self.btn_worker_area)
        l_areas.addWidget(gb_areas)

        gb_view = QGroupBox("Anzeige")
        l_view = QVBoxLayout(gb_view)
        self.btn_visibility = QPushButton("Ebenen / Sichtbarkeit")
        self.btn_offsets = QPushButton("Offsets Konfigurieren")
        self.btn_config_sizes = QPushButton("Größen Konfigurieren")
        l_view.addWidget(self.btn_visibility)
        l_view.addWidget(self.btn_offsets)
        l_view.addWidget(self.btn_config_sizes)
        l_areas.addWidget(gb_view)

        self.editor_subtabs.addTab(sub_areas, "Bereiche")

        # Sub ROUTEN
        sub_routes = QWidget()
        l_routes = QVBoxLayout(sub_routes)
        l_routes.setAlignment(Qt.AlignmentFlag.AlignTop)

        gb_route_tools = QGroupBox("Neue Route")
        l_rt = QVBoxLayout(gb_route_tools)
        self.btn_start_route = QPushButton("Eingang -> Laden")
        self.btn_start_route.setCheckable(True)
        self.new_route_button = QPushButton("Laden (Shop Loop)")
        self.new_route_button.setCheckable(True)
        self.btn_exit_route = QPushButton("Kasse -> Ausgang")
        self.btn_exit_route.setCheckable(True)

        # NEU: Button für Techniker Route
        self.btn_worker_route = QPushButton("Route: Techniker")
        self.btn_worker_route.setCheckable(True)
        self.btn_worker_route.setStyleSheet(
            "QPushButton:checked { background-color: #F59E0B; color: white; }"
        )

        l_rt.addWidget(self.btn_start_route)
        l_rt.addWidget(self.new_route_button)
        l_rt.addWidget(self.btn_exit_route)
        l_rt.addWidget(self.btn_worker_route)
        l_routes.addWidget(gb_route_tools)

        self.admin_toolbar = QWidget()
        self.admin_toolbar.setVisible(False)
        l_atb = QHBoxLayout(self.admin_toolbar)
        l_atb.setContentsMargins(0, 0, 0, 0)
        self.btn_save_admin = QPushButton("✓ Fertig")
        self.btn_save_admin.setStyleSheet(
            "background-color: #10B981; color: white; font-weight: bold;"
        )
        self.btn_cancel_route = QPushButton("✕ Abbrechen")
        l_atb.addWidget(self.btn_save_admin)
        l_atb.addWidget(self.btn_cancel_route)
        l_routes.addWidget(self.admin_toolbar)

        gb_route_list = QGroupBox("Vorhandene Routen")
        l_rl = QVBoxLayout(gb_route_list)
        self.route_list_widget = QListWidget()
        self.btn_del_route = QPushButton("Route löschen")
        l_rl.addWidget(self.route_list_widget)
        l_rl.addWidget(self.btn_del_route)
        l_routes.addWidget(gb_route_list)

        self.editor_subtabs.addTab(sub_routes, "Routen")

        # Sub OBJEKTE
        sub_objs = QWidget()
        l_objs = QVBoxLayout(sub_objs)
        l_objs.setAlignment(Qt.AlignmentFlag.AlignTop)

        gb_shelves = QGroupBox("Regale")
        l_sh = QVBoxLayout(gb_shelves)
        self.place_shelves_button = QPushButton("+ Regal platzieren")
        self.place_shelves_button.setCheckable(True)
        l_sh.addWidget(self.place_shelves_button)
        l_objs.addWidget(gb_shelves)

        gb_checkouts = QGroupBox("Kassen")
        l_ch = QVBoxLayout(gb_checkouts)
        r1 = QHBoxLayout()
        self.btn_kl = QPushButton("Normal (L)")
        self.btn_kl.setCheckable(True)
        self.btn_kr = QPushButton("Normal (R)")
        self.btn_kr.setCheckable(True)
        r1.addWidget(self.btn_kl)
        r1.addWidget(self.btn_kr)
        r2 = QHBoxLayout()
        self.btn_sl = QPushButton("SB (L)")
        self.btn_sl.setCheckable(True)
        self.btn_sr = QPushButton("SB (R)")
        self.btn_sr.setCheckable(True)
        r2.addWidget(self.btn_sl)
        r2.addWidget(self.btn_sr)
        l_ch.addLayout(r1)
        l_ch.addLayout(r2)
        l_objs.addWidget(gb_checkouts)

        gb_obj_list = QGroupBox("Objekt Liste")
        l_ol = QVBoxLayout(gb_obj_list)
        self.object_list_widget = QListWidget()
        h_act = QHBoxLayout()
        self.btn_edit_obj = QPushButton("Bearbeiten")
        self.btn_del_obj = QPushButton("Löschen")
        h_act.addWidget(self.btn_edit_obj)
        h_act.addWidget(self.btn_del_obj)
        l_ol.addWidget(self.object_list_widget)
        l_ol.addLayout(h_act)
        l_objs.addWidget(gb_obj_list)

        self.editor_subtabs.addTab(sub_objs, "Objekte")

        self.main_tabs.addTab(tab_editor_container, "Editor")

    def _create_spin(self, val, min_v, max_v, suffix=""):
        sb = QSpinBox()
        sb.setRange(min_v, max_v)
        sb.setValue(val)
        if suffix:
            sb.setSuffix(suffix)
        return sb

    def _create_double_spin(self, val, min_v, max_v, suffix=""):
        dsb = QDoubleSpinBox()
        dsb.setRange(min_v, max_v)
        dsb.setValue(val)
        dsb.setSingleStep(0.1)
        if suffix:
            dsb.setSuffix(suffix)
        return dsb

    def _create_help_icon(self, tooltip):
        lbl = QLabel()
        icon = QApplication.style().standardIcon(
            QStyle.StandardPixmap.SP_MessageBoxQuestion
        )
        lbl.setPixmap(icon.pixmap(14, 14))
        lbl.setToolTip(tooltip)
        lbl.setCursor(Qt.CursorShape.WhatsThisCursor)
        return lbl

    def _add_gb_header(self, layout, subtitle, tooltip=None):
        row = QHBoxLayout()
        row.setContentsMargins(5, 0, 0, 5)
        lbl_sub = QLabel(subtitle)
        lbl_sub.setStyleSheet(
            "color: #6B7280; font-style: italic; font-size: 11px;"
        )
        row.addWidget(lbl_sub)
        if tooltip:
            icon = self._create_help_icon(tooltip)
            row.addWidget(icon)
        row.addStretch()
        layout.addLayout(row)

    def _create_dist_row(self, label, val_mean, val_std, layout):
        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
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
        sb_min = self._create_double_spin(val_min, 0.1, 10.0)
        sb_max = self._create_double_spin(val_max, 0.1, 10.0)
        h.addWidget(QLabel("Min:"))
        h.addWidget(sb_min)
        h.addWidget(QLabel("Max:"))
        h.addWidget(sb_max)
        layout.addRow(label, h)
        return sb_min, sb_max

    def _toggle_lang(self):
        if self.btn_lang.text() == "🇩🇪":
            self.btn_lang.setText("🇺🇸")
        else:
            self.btn_lang.setText("🇩🇪")

    def _sync_mode_buttons(self, index):
        if index == 0:
            self.btn_mode_sim.setChecked(True)
            self.btn_mode_edit.setChecked(False)
        else:
            self.btn_mode_sim.setChecked(False)
            self.btn_mode_edit.setChecked(True)
