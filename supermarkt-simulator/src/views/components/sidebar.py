"""
Sidebar Component.
Refactored:
- LAYOUT: Moved Live Stats and Log into the 'Statistiken' tab.
- CLEANUP: Removed permanent footer area.
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
            QGroupBox {{
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
                font-weight: bold;
                background-color: transparent;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 5px;
                background-color: #F5F7FA;
                color: #374151;
            }}
            
            /* --- HEADER BUTTONS --- */
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
            QPushButton.HeaderBtn:hover {{
                border-color: {accent};
                background-color: #EFF6FF;
            }}
            
            QPushButton#BtnLang {{
                font-size: 26px;
                padding-bottom: 2px;
            }}

            /* --- TABS --- */
            QTabWidget::pane {{
                border: 1px solid #D1D5DB;
                background: #FFFFFF;
                border-radius: 4px;
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
            
            /* --- LOG LIST --- */
            QListWidget {{
                background-color: #FFFFFF;
                border: 1px solid #D1D5DB;
                border-radius: 4px;
                font-size: 11px;
            }}
        """
        )

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # === HEADER (MODE & LANG) ===
        self.setup_header(main_layout)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #E5E7EB;")
        main_layout.addWidget(line)

        # === TABS ===
        self.main_tabs = QTabWidget()
        main_layout.addWidget(self.main_tabs)

        # 1. Eingabe
        self._init_tab_input()
        # 2. Statistiken (Hier sind jetzt Live Stats & Log)
        self._init_tab_stats()
        # 3. Editor
        self._init_tab_editor()

    def setup_header(self, layout):
        h_layout = QHBoxLayout()
        h_layout.setSpacing(10)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Simulation", "Editor"])
        self.mode_combo.setVisible(False)
        layout.addWidget(self.mode_combo)

        # --- MODE BUTTONS ---
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

        # --- LANGUAGE BUTTON ---
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

        # SUB 1: LADEN
        sub_shop = QWidget()
        l_shop = QVBoxLayout(sub_shop)
        gb_map = QGroupBox("Karte wählen")
        l_gb_map = QVBoxLayout(gb_map)
        self.map_combo = QComboBox()
        self.map_combo.setToolTip("Wähle eine gespeicherte Karte aus.")
        l_gb_map.addWidget(self.map_combo)
        l_shop.addWidget(gb_map)
        gb_time = QGroupBox("Zeitsteuerung")
        f_time = QFormLayout(gb_time)
        self.time_open = QTimeEdit(QTime(8, 0))
        self.time_close = QTimeEdit(QTime(20, 0))
        f_time.addRow("Öffnen:", self.time_open)
        f_time.addRow("Schließen:", self.time_close)
        l_shop.addWidget(gb_time)
        gb_co = QGroupBox("Störungen & Kassen")
        f_co = QFormLayout(gb_co)
        self.checkout_fail_rate_normal = self._create_spin(0, 0, 100, " %")
        self.checkout_fail_rate_sb = self._create_spin(0, 0, 100, " %")
        f_co.addRow("Ausfall Normal (%):", self.checkout_fail_rate_normal)
        f_co.addRow("Ausfall SB (%):", self.checkout_fail_rate_sb)
        l_shop.addWidget(gb_co)
        l_shop.addStretch()
        self.input_sub_tabs.addTab(sub_shop, "Laden")

        # SUB 2: KUNDEN
        sub_cust = QWidget()
        l_cust = QVBoxLayout(sub_cust)
        scroll_cust = QScrollArea()
        scroll_cust.setWidgetResizable(True)
        cust_content = QWidget()
        l_cust_content = QVBoxLayout(cust_content)
        gb_spawn = QGroupBox("Kundenaufkommen (Exp)")
        f_spawn = QFormLayout(gb_spawn)
        self.actor_count_input = QSpinBox()
        self.actor_count_input.setRange(1, 2000)
        self.actor_count_input.setValue(50)
        self.disabled_prob_input = self._create_spin(10, 0, 100, " %")
        f_spawn.addRow("Kunden / Tag:", self.actor_count_input)
        f_spawn.addRow("Anteil Beeintr. (%):", self.disabled_prob_input)
        l_cust_content.addWidget(gb_spawn)
        gb_speed = QGroupBox("Geschwindigkeit (Normal)")
        f_speed = QFormLayout(gb_speed)
        self.speed_walk_mean = self._create_double_spin(1.5, 0.5, 5.0)
        self.speed_walk_std = self._create_double_spin(0.3, 0.0, 2.0)
        self.speed_roll_mean = self._create_double_spin(1.0, 0.5, 4.0)
        self.speed_roll_std = self._create_double_spin(0.2, 0.0, 1.5)
        f_speed.addRow("Gehen Ø:", self.speed_walk_mean)
        f_speed.addRow("Gehen σ:", self.speed_walk_std)
        f_speed.addRow("Rollen Ø:", self.speed_roll_mean)
        f_speed.addRow("Rollen σ:", self.speed_roll_std)
        l_cust_content.addWidget(gb_speed)
        gb_cart = QGroupBox("Einkaufswagen (Normal)")
        f_cart = QFormLayout(gb_cart)
        self.items_mean = self._create_spin(15, 1, 100)
        self.items_std = self._create_spin(5, 0, 50)
        self.hand_scanner_prob = self._create_spin(20, 0, 100, " %")
        f_cart.addRow("Artikel Ø:", self.items_mean)
        f_cart.addRow("Artikel σ:", self.items_std)
        f_cart.addRow("Handscanner %:", self.hand_scanner_prob)
        l_cust_content.addWidget(gb_cart)
        gb_checkout = QGroupBox("Scan-Dauer (Gleich)")
        f_checkout = QFormLayout(gb_checkout)
        self.scan_speed_normal_min = self._create_double_spin(0.5, 0.1, 5.0)
        self.scan_speed_normal_max = self._create_double_spin(1.5, 0.1, 5.0)
        self.scan_speed_disabled_min = self._create_double_spin(1.0, 0.1, 8.0)
        self.scan_speed_disabled_max = self._create_double_spin(2.5, 0.1, 8.0)
        f_checkout.addRow("Normal Min:", self.scan_speed_normal_min)
        f_checkout.addRow("Normal Max:", self.scan_speed_normal_max)
        f_checkout.addRow("Einges. Min:", self.scan_speed_disabled_min)
        f_checkout.addRow("Einges. Max:", self.scan_speed_disabled_max)
        l_cust_content.addWidget(gb_checkout)
        l_cust_content.addStretch()
        scroll_cust.setWidget(cust_content)
        l_cust.addWidget(scroll_cust)
        self.input_sub_tabs.addTab(sub_cust, "Kunden")

        # SUB 3: PERSONAL
        sub_staff = QWidget()
        l_staff = QVBoxLayout(sub_staff)
        gb_cashier = QGroupBox("Kassierer (Sek/Artikel)")
        f_cashier = QFormLayout(gb_cashier)
        self.scan_speed_newbie_min = self._create_double_spin(1.5, 0.5, 5.0)
        self.scan_speed_newbie_max = self._create_double_spin(2.5, 0.5, 6.0)
        self.scan_speed_pro_min = self._create_double_spin(0.8, 0.2, 3.0)
        self.scan_speed_pro_max = self._create_double_spin(1.2, 0.2, 4.0)
        f_cashier.addRow("Azubi Min:", self.scan_speed_newbie_min)
        f_cashier.addRow("Azubi Max:", self.scan_speed_newbie_max)
        f_cashier.addRow("Profi Min:", self.scan_speed_pro_min)
        f_cashier.addRow("Profi Max:", self.scan_speed_pro_max)
        l_staff.addWidget(gb_cashier)
        gb_maint = QGroupBox("Wartung / Reparatur")
        f_maint = QFormLayout(gb_maint)
        self.worker_repair_min = self._create_double_spin(5.0, 1.0, 60.0, " s")
        self.worker_repair_max = self._create_double_spin(
            15.0, 1.0, 120.0, " s"
        )
        f_maint.addRow("Dauer Min:", self.worker_repair_min)
        f_maint.addRow("Dauer Max:", self.worker_repair_max)
        l_staff.addWidget(gb_maint)
        l_staff.addStretch()
        self.input_sub_tabs.addTab(sub_staff, "Personal")
        self.main_tabs.addTab(tab_input_container, "Eingabe")

    def _init_tab_stats(self):
        """
        Stats Tab now contains Live Stats and the Log.
        """
        tab_stats = QWidget()
        l_stats = QVBoxLayout(tab_stats)
        l_stats.setSpacing(15)
        l_stats.setContentsMargins(10, 10, 10, 10)

        # 1. LIVE STATS
        self.gb_stats = QGroupBox("Live Daten")
        # Ensure gb_stats references are available
        self.lbl_queue_count = QLabel("0")
        self.lbl_customers_in_store = QLabel("0")
        self.lbl_total_customers = QLabel("0")

        f_stats_grid = QFormLayout(self.gb_stats)
        f_stats_grid.addRow("Kunden in Schlange:", self.lbl_queue_count)
        f_stats_grid.addRow("Kunden im Laden:", self.lbl_customers_in_store)
        f_stats_grid.addRow("Kunden Gesamt:", self.lbl_total_customers)

        l_stats.addWidget(self.gb_stats)

        # 2. LOG
        gb_log = QGroupBox("Ereignis-Protokoll")
        l_log = QVBoxLayout(gb_log)
        self.list_log = QListWidget()
        # Flexible Höhe für das Log
        self.list_log.setMinimumHeight(200)
        l_log.addWidget(self.list_log)

        l_stats.addWidget(gb_log)

        # 3. Charts Platzhalter (Optional)
        self.plot_widget = None
        lbl_charts = QLabel("(Hier könnten Charts stehen)")
        lbl_charts.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_charts.setStyleSheet("color: #9CA3AF;")
        l_stats.addWidget(lbl_charts)

        l_stats.addStretch()
        self.main_tabs.addTab(tab_stats, "Statistiken")

    def _init_tab_editor(self):
        # ... (Identischer Editor Code) ...
        # COPY OF _init_tab_editor logic
        tab_editor_container = QWidget()
        l_editor_main = QVBoxLayout(tab_editor_container)
        l_editor_main.setContentsMargins(0, 5, 0, 0)
        self.editor_subtabs = QTabWidget()
        l_editor_main.addWidget(self.editor_subtabs)
        # Sub KARTE
        sub_map = QWidget()
        l_map = QVBoxLayout(sub_map)
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
        l_map.addStretch()
        self.editor_subtabs.addTab(sub_map, "Karte")
        # Sub WERKZEUGE
        sub_areas = QWidget()
        l_areas = QVBoxLayout(sub_areas)
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
        l_areas.addStretch()
        self.editor_subtabs.addTab(sub_areas, "Bereiche")
        # Sub ROUTEN
        sub_routes = QWidget()
        l_routes = QVBoxLayout(sub_routes)
        gb_route_tools = QGroupBox("Neue Route")
        l_rt = QVBoxLayout(gb_route_tools)
        self.btn_start_route = QPushButton("Eingang -> Laden")
        self.btn_start_route.setCheckable(True)
        self.new_route_button = QPushButton("Laden (Shop Loop)")
        self.new_route_button.setCheckable(True)
        self.btn_exit_route = QPushButton("Kasse -> Ausgang")
        self.btn_exit_route.setCheckable(True)
        l_rt.addWidget(self.btn_start_route)
        l_rt.addWidget(self.new_route_button)
        l_rt.addWidget(self.btn_exit_route)
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

    def _create_spin(self, val, min_v, max_v, suffix="", tooltip=""):
        sb = QSpinBox()
        sb.setRange(min_v, max_v)
        sb.setValue(val)
        sb.setSuffix(suffix)
        if tooltip:
            sb.setToolTip(tooltip)
        return sb

    def _create_double_spin(self, val, min_v, max_v, suffix="", tooltip=""):
        dsb = QDoubleSpinBox()
        dsb.setRange(min_v, max_v)
        dsb.setValue(val)
        dsb.setSingleStep(0.1)
        dsb.setSuffix(suffix)
        if tooltip:
            dsb.setToolTip(tooltip)
        return dsb

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
