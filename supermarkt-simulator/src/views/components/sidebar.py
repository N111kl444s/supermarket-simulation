"""
Sidebar Component.
Refactored:
- STYLE: Added margin-top to QTabWidget::pane to create space between tabs and content.
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
from PyQt6.QtCore import QTime, Qt, pyqtSignal
from config import COLOR_ACCENT, COLOR_ERROR, COLOR_SUCCESS, COLOR_BG_PANEL


class Sidebar(QWidget):
    language_changed = pyqtSignal(str)

    def __init__(self, parent=None, translator=None):
        super().__init__(parent)
        self.translator = translator
        self.widget_refs = {}  # Store references to all translatable widgets
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
            /* Transparent ScrollArea Fix */
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollArea > QWidget > QWidget {{
                background: transparent;
            }}
            
            /* Header Buttons */
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

            /* Tabs */
            QTabWidget::pane {{
                border: 1px solid #D1D5DB;
                background: #FFFFFF;
                border-radius: 4px;
                /* HIER IST DER SPACE: */
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
                /* Optional: Den Tab etwas wachsen lassen, damit er über den Margin ragt (Overlay Look)
                   margin-bottom: -1px; 
                */
            }}
            
            /* Modern GroupBox */
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

        # 1. EINGABE (mit Subtabs)
        self._init_tab_input()

        # 2. STATISTIKEN
        self._init_tab_stats()

        # 3. EDITOR
        self._init_tab_editor()

    # ==========================================
    # HEADER LOGIC
    # ==========================================
    def setup_header(self, layout):
        h_layout = QHBoxLayout()
        h_layout.setSpacing(10)

        self.mode_combo = QComboBox()
        sim_text = (
            self.translator.get("sidebar.header.simulation")
            if self.translator
            else "Simulation"
        )
        edit_text = (
            self.translator.get("sidebar.header.editor")
            if self.translator
            else "Editor"
        )
        self.mode_combo.addItems([sim_text, edit_text])
        self.mode_combo.setVisible(False)
        layout.addWidget(self.mode_combo)

        # Mode Buttons
        self.mode_group = QButtonGroup(self)

        self.btn_mode_sim = QPushButton(sim_text)
        self.btn_mode_sim.setProperty("class", "HeaderBtn")
        self.btn_mode_sim.setCheckable(True)
        self.btn_mode_sim.setChecked(True)
        self.btn_mode_sim.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_sim.setStyleSheet(
            "border-top-right-radius: 0; border-bottom-right-radius: 0; border-right: none;"
        )

        self.btn_mode_edit = QPushButton(edit_text)
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

        # Language
        lang_text = (
            self.translator.get("sidebar.language")
            if self.translator
            else "🇩🇪"
        )
        self.btn_lang = QPushButton(lang_text)
        self.btn_lang.setObjectName("BtnLang")
        self.btn_lang.setProperty("class", "HeaderBtn")
        self.btn_lang.setCheckable(False)
        self.btn_lang.setFixedWidth(60)
        self.btn_lang.clicked.connect(self._toggle_lang)
        h_layout.addWidget(self.btn_lang, 0)

        layout.addLayout(h_layout)

    # ==========================================
    # HELPER: GroupBox Header
    # ==========================================
    def _add_gb_header(self, layout, subtitle, tooltip=None):
        """Adds a subtitle row with help icon inside a GroupBox Layout."""
        row = QHBoxLayout()
        row.setContentsMargins(5, 0, 0, 5)  # Etwas Abstand

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

    # ==========================================
    # TAB 1: EINGABE
    # ==========================================
    def _init_tab_input(self):
        tab_input_container = QWidget()
        l_input_main = QVBoxLayout(tab_input_container)
        l_input_main.setContentsMargins(0, 5, 0, 0)

        self.input_sub_tabs = QTabWidget()
        l_input_main.addWidget(self.input_sub_tabs)

        # --- SUB 1: LADEN ---
        self._setup_shop_tab()

        # --- SUB 2: KUNDEN (Old Layout Style) ---
        self._setup_cust_tab()

        # --- SUB 3: PERSONAL (Old Layout Style) ---
        self._setup_staff_tab()

        # --- SUB 4: KONFLIKTE ---
        self._setup_conflicts_tab()

        input_tab_text = (
            self.translator.get("sidebar.tabs.input")
            if self.translator
            else "Eingabe"
        )
        self.main_tabs.addTab(tab_input_container, input_tab_text)

    def _setup_shop_tab(self):
        sub_shop = QWidget()
        l_shop = QVBoxLayout(sub_shop)
        l_shop.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 1. Map
        map_select_text = (
            self.translator.get("sidebar.input.map_select")
            if self.translator
            else "Karte wählen"
        )
        gb_map = QGroupBox(map_select_text)
        v_map = QVBoxLayout(gb_map)
        self.map_combo = QComboBox()
        v_map.addWidget(self.map_combo)
        l_shop.addWidget(gb_map)

        # 2. Time
        time_control_text = (
            self.translator.get("sidebar.input.time_control")
            if self.translator
            else "Zeitsteuerung"
        )
        gb_time = QGroupBox(time_control_text)
        v_time = QVBoxLayout(gb_time)
        f_time = QFormLayout()
        self.time_open = QTimeEdit(QTime(8, 0))
        self.time_close = QTimeEdit(QTime(20, 0))
        open_text = (
            self.translator.get("sidebar.input.time_open")
            if self.translator
            else "Öffnen:"
        )
        close_text = (
            self.translator.get("sidebar.input.time_close")
            if self.translator
            else "Schließen:"
        )
        f_time.addRow(open_text, self.time_open)
        f_time.addRow(close_text, self.time_close)
        v_time.addLayout(f_time)
        l_shop.addWidget(gb_time)

        shop_tab_text = (
            self.translator.get("sidebar.input.shop_tab")
            if self.translator
            else "Laden"
        )
        self.input_sub_tabs.addTab(sub_shop, shop_tab_text)

    def _setup_cust_tab(self):
        # Setup Scroll Area Logic
        tab_cust_container = QWidget()
        l_cust_cont = QVBoxLayout(tab_cust_container)
        l_cust_cont.setContentsMargins(0, 0, 0, 0)
        scroll_cust = QScrollArea()
        scroll_cust.setWidgetResizable(True)
        content_cust = QWidget()
        l_gb_cust = QVBoxLayout(content_cust)
        l_gb_cust.setAlignment(Qt.AlignmentFlag.AlignTop)
        l_gb_cust.setSpacing(15)

        # 1. Spawn
        cv_title = (
            self.translator.get("sidebar.input.customer_volume")
            if self.translator
            else "Kundenaufkommen"
        )
        cv_day = (
            self.translator.get("sidebar.input.customers_per_day")
            if self.translator
            else "Kunden / Tag:"
        )
        cv_share = (
            self.translator.get("sidebar.input.share_disabled")
            if self.translator
            else "Anteil Beeintr.:"
        )
        cv_desc = (
            self.translator.get("tooltips.customer_volume")
            if self.translator
            else "Zeitabstände zwischen Kunden sind zufällig (Poisson-Prozess)."
        )
        gb_spawn = QGroupBox(cv_title)
        v_spawn = QVBoxLayout(gb_spawn)
        self._add_gb_header(
            v_spawn,
            "(Exponentialverteilung)",
            cv_desc,
        )
        f_spawn = QFormLayout()
        self.actor_count_input = self._create_spin(50, 1, 10000)
        self.disabled_prob_input = self._create_spin(10, 0, 100, " %")
        f_spawn.addRow(cv_day, self.actor_count_input)
        f_spawn.addRow(cv_share, self.disabled_prob_input)
        v_spawn.addLayout(f_spawn)
        l_gb_cust.addWidget(gb_spawn)

        # 2. Speed
        speed_title = (
            self.translator.get("sidebar.input.speed")
            if self.translator
            else "Geschwindigkeit"
        )
        speed_walk = (
            self.translator.get("sidebar.input.walking")
            if self.translator
            else "Gehen:"
        )
        speed_roll = (
            self.translator.get("sidebar.input.rolling")
            if self.translator
            else "Rollen:"
        )
        speed_desc = (
            self.translator.get("tooltips.speed")
            if self.translator
            else "Gauß-Verteilung mit Mittelwert (Ø) und Standardabweichung (σ)."
        )
        gb_speed = QGroupBox(speed_title)
        v_speed = QVBoxLayout(gb_speed)
        self._add_gb_header(
            v_speed,
            "(Normalverteilung)",
            speed_desc,
        )
        f_speed = QFormLayout()
        self.speed_walk_mean, self.speed_walk_std = self._create_dist_row(
            speed_walk, 2.5, 0.5, f_speed
        )
        self.speed_roll_mean, self.speed_roll_std = self._create_dist_row(
            speed_roll, 1.5, 0.3, f_speed
        )
        v_speed.addLayout(f_speed)
        l_gb_cust.addWidget(gb_speed)

        # 3. Cart
        cart_title = (
            self.translator.get("sidebar.input.shopping_cart")
            if self.translator
            else "Einkaufswagen"
        )
        cart_items = (
            self.translator.get("sidebar.input.items")
            if self.translator
            else "Artikel:"
        )
        cart_scanner = (
            self.translator.get("sidebar.input.hand_scanner")
            if self.translator
            else "Handscanner:"
        )
        cart_desc = (
            self.translator.get("tooltips.cart")
            if self.translator
            else "Anzahl der Artikel im Wagen."
        )
        gb_cart = QGroupBox(cart_title)
        v_cart = QVBoxLayout(gb_cart)
        self._add_gb_header(v_cart, "(Normalverteilung)", cart_desc)
        f_cart = QFormLayout()
        self.items_mean = self._create_spin(15, 1, 100)
        self.items_std = self._create_double_spin(5.0, 0, 50)
        # Custom Row for Items
        h_it = QHBoxLayout()
        h_it.addWidget(QLabel("Ø:"))
        h_it.addWidget(self.items_mean)
        h_it.addWidget(QLabel("σ:"))
        h_it.addWidget(self.items_std)
        f_cart.addRow(cart_items, h_it)

        self.hand_scanner_prob = self._create_spin(20, 0, 100, " %")
        f_cart.addRow(cart_scanner, self.hand_scanner_prob)
        v_cart.addLayout(f_cart)
        l_gb_cust.addWidget(gb_cart)

        # 4. Scan Speed (Customer side - SB)
        scan_title = (
            self.translator.get("sidebar.input.scan_duration")
            if self.translator
            else "Scan-Dauer (Kunde)"
        )
        scan_normal = (
            self.translator.get("sidebar.input.scan_normal")
            if self.translator
            else "Normal:"
        )
        scan_disabled = (
            self.translator.get("sidebar.input.scan_disabled")
            if self.translator
            else "Einges.:"
        )
        scan_desc = (
            self.translator.get("tooltips.scan")
            if self.translator
            else "Zufällige Zeit pro Artikel zwischen Min und Max."
        )
        gb_scan = QGroupBox(scan_title)
        v_scan = QVBoxLayout(gb_scan)
        self._add_gb_header(
            v_scan,
            "(Gleichverteilung)",
            scan_desc,
        )
        f_scan = QFormLayout()
        self.scan_speed_normal_min, self.scan_speed_normal_max = (
            self._create_range_row(scan_normal, 0.5, 1.5, f_scan)
        )
        self.scan_speed_disabled_min, self.scan_speed_disabled_max = (
            self._create_range_row(scan_disabled, 1.0, 3.0, f_scan)
        )
        v_scan.addLayout(f_scan)
        l_gb_cust.addWidget(gb_scan)

        # 5. Payment
        payment_title = (
            self.translator.get("sidebar.input.payment_methods")
            if self.translator
            else "Zahlungsmethoden"
        )
        payment_cash = (
            self.translator.get("sidebar.input.payment_cash")
            if self.translator
            else "Bargeld:"
        )
        payment_card = (
            self.translator.get("sidebar.input.payment_card")
            if self.translator
            else "Karte:"
        )
        payment_desc = (
            self.translator.get("tooltips.payment")
            if self.translator
            else "Muss sich auf 100% ergänzen."
        )
        gb_pay = QGroupBox(payment_title)
        v_pay = QVBoxLayout(gb_pay)
        self._add_gb_header(v_pay, "(Verteilung in %)", payment_desc)
        f_pay = QFormLayout()
        self.payment_cash = self._create_double_spin(30.0, 0, 100, " %")
        self.payment_card = self._create_double_spin(70.0, 0, 100, " %")
        # Auto-Balance Logic
        self.payment_cash.valueChanged.connect(
            lambda v: self.payment_card.setValue(100.0 - v)
        )
        self.payment_card.valueChanged.connect(
            lambda v: self.payment_cash.setValue(100.0 - v)
        )
        f_pay.addRow(payment_cash, self.payment_cash)
        f_pay.addRow(payment_card, self.payment_card)
        v_pay.addLayout(f_pay)
        l_gb_cust.addWidget(gb_pay)

        scroll_cust.setWidget(content_cust)
        l_cust_cont.addWidget(scroll_cust)
        cust_tab = (
            self.translator.get("sidebar.input.customers_tab")
            if self.translator
            else "Kunden"
        )
        self.input_sub_tabs.addTab(tab_cust_container, cust_tab)

    def _setup_staff_tab(self):
        tab_staff = QWidget()
        l_staff = QVBoxLayout(tab_staff)
        l_staff.setAlignment(Qt.AlignmentFlag.AlignTop)
        l_staff.setSpacing(15)

        # Translations
        cashier_title = (
            self.translator.get("sidebar.input.cashier_speed")
            if self.translator
            else "Kassierer Geschwindigkeit"
        )
        cashier_newbie = (
            self.translator.get("sidebar.input.cashier_newbie")
            if self.translator
            else "Azubi:"
        )
        cashier_pro = (
            self.translator.get("sidebar.input.cashier_pro")
            if self.translator
            else "Profi:"
        )
        cashier_desc = (
            self.translator.get("tooltips.cashier")
            if self.translator
            else "Scan-Tempo des Personals."
        )
        paytime_title = (
            self.translator.get("sidebar.input.payment_duration")
            if self.translator
            else "Bezahldauer"
        )
        paytime_cash = (
            self.translator.get("sidebar.input.payment_cash_label")
            if self.translator
            else "Bargeld:"
        )
        paytime_card = (
            self.translator.get("sidebar.input.payment_card_label")
            if self.translator
            else "Karte:"
        )
        paytime_desc = (
            self.translator.get("tooltips.paytime")
            if self.translator
            else "Dauer des Bezahlvorgangs."
        )
        conflict_title = (
            self.translator.get("sidebar.input.conflict_resolution")
            if self.translator
            else "Konfliktbewältigung"
        )
        conflict_duration = (
            self.translator.get("sidebar.input.conflict_duration")
            if self.translator
            else "Dauer:"
        )
        conflict_desc = (
            self.translator.get("tooltips.conflict")
            if self.translator
            else "Wie lange ein Techniker braucht."
        )

        # 1. Cashier Scan
        gb_cashier = QGroupBox(cashier_title)
        v_cashier = QVBoxLayout(gb_cashier)
        self._add_gb_header(
            v_cashier,
            "(Sek/Artikel - Gleichverteilung)",
            cashier_desc,
        )
        f_cashier = QFormLayout()
        self.scan_speed_newbie_min, self.scan_speed_newbie_max = (
            self._create_range_row(cashier_newbie, 1.5, 2.5, f_cashier)
        )
        self.scan_speed_pro_min, self.scan_speed_pro_max = (
            self._create_range_row(cashier_pro, 0.8, 1.2, f_cashier)
        )
        v_cashier.addLayout(f_cashier)
        l_staff.addWidget(gb_cashier)

        # 2. Pay Duration
        gb_paytime = QGroupBox(paytime_title)
        v_paytime = QVBoxLayout(gb_paytime)
        self._add_gb_header(
            v_paytime,
            "(Sekunden - Gleichverteilung)",
            paytime_desc,
        )
        f_paytime = QFormLayout()
        self.pay_duration_cash_min, self.pay_duration_cash_max = (
            self._create_range_row(paytime_cash, 3.0, 8.0, f_paytime)
        )
        self.pay_duration_card_min, self.pay_duration_card_max = (
            self._create_range_row(paytime_card, 1.0, 4.0, f_paytime)
        )
        v_paytime.addLayout(f_paytime)
        l_staff.addWidget(gb_paytime)

        # 3. Conflict Resolution
        gb_maint = QGroupBox(conflict_title)
        v_maint = QVBoxLayout(gb_maint)
        self._add_gb_header(
            v_maint,
            "(Sekunden - Gleichverteilung)",
            conflict_desc,
        )
        f_maint = QFormLayout()
        self.worker_repair_min, self.worker_repair_max = (
            self._create_range_row(conflict_duration, 5.0, 15.0, f_maint)
        )
        v_maint.addLayout(f_maint)
        l_staff.addWidget(gb_maint)

        staff_tab = (
            self.translator.get("sidebar.input.staff_tab")
            if self.translator
            else "Personal"
        )
        self.input_sub_tabs.addTab(tab_staff, staff_tab)

    def _setup_conflicts_tab(self):
        tab_conflicts = QWidget()
        l_conflicts = QVBoxLayout(tab_conflicts)
        l_conflicts.setAlignment(Qt.AlignmentFlag.AlignTop)
        l_conflicts.setSpacing(15)

        # Translations
        checkout_title = (
            self.translator.get("sidebar.input.checkout_failures")
            if self.translator
            else "Kassenstörungen"
        )
        checkout_normal = (
            self.translator.get("sidebar.input.failure_normal")
            if self.translator
            else "Ausfall (Normal):"
        )
        checkout_sb = (
            self.translator.get("sidebar.input.failure_sb")
            if self.translator
            else "Ausfall (SB):"
        )
        checkout_desc = (
            self.translator.get("tooltips.checkout_fail")
            if self.translator
            else "Chance, dass eine Kasse pro Minute ausfällt."
        )
        annoy_title = (
            self.translator.get("sidebar.input.customer_annoyance")
            if self.translator
            else "Verärgerung der Kunden"
        )
        annoy_rate = (
            self.translator.get("sidebar.input.annoyance_rate")
            if self.translator
            else "Verärgerung:"
        )
        annoy_desc = (
            self.translator.get("tooltips.annoyance")
            if self.translator
            else "Chance, dass ein Kunde verärgert wird."
        )

        # 1. Failures
        gb_co = QGroupBox(checkout_title)
        v_co = QVBoxLayout(gb_co)
        self._add_gb_header(
            v_co,
            "(Wahrscheinlichkeit in %)",
            checkout_desc,
        )
        f_co = QFormLayout()
        self.checkout_fail_rate_normal = self._create_spin(0, 0, 100, " %")
        self.checkout_fail_rate_sb = self._create_spin(0, 0, 100, " %")
        f_co.addRow(checkout_normal, self.checkout_fail_rate_normal)
        f_co.addRow(checkout_sb, self.checkout_fail_rate_sb)
        v_co.addLayout(f_co)
        l_conflicts.addWidget(gb_co)

        # 2. Customer Annoyance
        gb_annoy = QGroupBox(annoy_title)
        v_annoy = QVBoxLayout(gb_annoy)
        self._add_gb_header(
            v_annoy,
            "(Wahrscheinlichkeit in %)",
            annoy_desc,
        )
        f_annoy = QFormLayout()
        self.customer_annoyance_rate = self._create_spin(0, 0, 100, " %")
        f_annoy.addRow(annoy_rate, self.customer_annoyance_rate)
        v_annoy.addLayout(f_annoy)
        l_conflicts.addWidget(gb_annoy)

        conflicts_tab = (
            self.translator.get("sidebar.input.conflicts_tab")
            if self.translator
            else "Konflikte"
        )
        self.input_sub_tabs.addTab(tab_conflicts, conflicts_tab)

    # ==========================================
    # TAB 2: STATISTIKEN
    # ==========================================
    def _init_tab_stats(self):
        tab_stats = QWidget()
        l_stats = QVBoxLayout(tab_stats)
        l_stats.setSpacing(15)
        l_stats.setContentsMargins(10, 10, 10, 10)

        # Translations
        live_data_title = (
            self.translator.get("sidebar.stats.live_data")
            if self.translator
            else "Live Daten"
        )
        queue_label = (
            self.translator.get("sidebar.stats.queue_count")
            if self.translator
            else "Kunden in Schlange:"
        )
        store_label = (
            self.translator.get("sidebar.stats.customers_in_store")
            if self.translator
            else "Kunden im Laden:"
        )
        total_label = (
            self.translator.get("sidebar.stats.total_customers")
            if self.translator
            else "Kunden Gesamt:"
        )
        event_log_title = (
            self.translator.get("sidebar.stats.event_log")
            if self.translator
            else "Ereignis-Protokoll"
        )

        self.gb_stats = QGroupBox(live_data_title)
        self.lbl_queue_count = QLabel("0")
        self.lbl_customers_in_store = QLabel("0")
        self.lbl_total_customers = QLabel("0")

        f_stats_grid = QFormLayout(self.gb_stats)
        f_stats_grid.addRow(queue_label, self.lbl_queue_count)
        f_stats_grid.addRow(store_label, self.lbl_customers_in_store)
        f_stats_grid.addRow(total_label, self.lbl_total_customers)
        l_stats.addWidget(self.gb_stats)

        gb_log = QGroupBox(event_log_title)
        l_log = QVBoxLayout(gb_log)
        self.list_log = QListWidget()
        self.list_log.setMinimumHeight(200)
        l_log.addWidget(self.list_log)
        l_stats.addWidget(gb_log)

        self.plot_widget = None
        l_stats.addStretch()
        stats_tab = (
            self.translator.get("sidebar.tabs.stats")
            if self.translator
            else "Statistiken"
        )
        self.main_tabs.addTab(tab_stats, stats_tab)

    # ==========================================
    # TAB 3: EDITOR
    # ==========================================
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

        # Translations for Map Tab
        file_title = (
            self.translator.get("sidebar.editor.map_file")
            if self.translator
            else "Datei"
        )
        new_map = (
            self.translator.get("sidebar.editor.new_map")
            if self.translator
            else "Neue Karte"
        )
        save_map = (
            self.translator.get("sidebar.editor.save_map")
            if self.translator
            else "Karte Speichern"
        )
        delete_map = (
            self.translator.get("sidebar.editor.delete_map")
            if self.translator
            else "Karte Löschen"
        )
        bg_title = (
            self.translator.get("sidebar.editor.background")
            if self.translator
            else "Hintergrund"
        )
        load_image = (
            self.translator.get("sidebar.editor.load_image")
            if self.translator
            else "Bild laden..."
        )
        remove_image = (
            self.translator.get("sidebar.editor.remove_image")
            if self.translator
            else "Bild entfernen"
        )
        zoom_label = (
            self.translator.get("sidebar.editor.zoom")
            if self.translator
            else "Zoom:"
        )
        options_title = (
            self.translator.get("sidebar.editor.map_options")
            if self.translator
            else "Optionen"
        )
        move_map_btn = (
            self.translator.get("sidebar.editor.move_map")
            if self.translator
            else "Karte verschieben"
        )
        exit_direction = (
            self.translator.get("sidebar.editor.exit_direction")
            if self.translator
            else "Exit Richtung:"
        )

        gb_map_file = QGroupBox(file_title)
        l_map_file = QVBoxLayout(gb_map_file)
        self.btn_new_map = QPushButton(new_map)
        self.btn_save_map = QPushButton(save_map)
        self.btn_delete_map = QPushButton(delete_map)
        l_map_file.addWidget(self.btn_new_map)
        l_map_file.addWidget(self.btn_save_map)
        l_map_file.addWidget(self.btn_delete_map)
        l_map.addWidget(gb_map_file)

        gb_map_bg = QGroupBox(bg_title)
        l_map_bg = QVBoxLayout(gb_map_bg)
        self.btn_set_background = QPushButton(load_image)
        self.btn_remove_background = QPushButton(remove_image)
        h_scale = QHBoxLayout()
        h_scale.addWidget(QLabel(zoom_label))
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

        gb_map_opts = QGroupBox(options_title)
        l_map_opts = QVBoxLayout(gb_map_opts)
        self.btn_move_map = QPushButton(move_map_btn)
        self.btn_move_map.setCheckable(True)
        h_exit = QHBoxLayout()
        h_exit.addWidget(QLabel(exit_direction))
        self.combo_global_exit = QComboBox()
        self.combo_global_exit.addItems(["Rechts", "Links", "Oben", "Unten"])
        h_exit.addWidget(self.combo_global_exit)
        l_map_opts.addWidget(self.btn_move_map)
        l_map_opts.addLayout(h_exit)
        l_map.addWidget(gb_map_opts)

        map_tab = (
            self.translator.get("sidebar.editor.map_tab")
            if self.translator
            else "Karte"
        )
        self.editor_subtabs.addTab(sub_map, map_tab)

        # Sub WERKZEUGE
        sub_areas = QWidget()
        l_areas = QVBoxLayout(sub_areas)
        l_areas.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Translations for Areas Tab
        areas_title = (
            self.translator.get("sidebar.editor.draw_areas")
            if self.translator
            else "Flächen zeichnen"
        )
        start_area = (
            self.translator.get("sidebar.editor.start_area")
            if self.translator
            else "Start-Bereich"
        )
        waiting_area = (
            self.translator.get("sidebar.editor.waiting_area")
            if self.translator
            else "Warte-Bereich"
        )
        exit_area = (
            self.translator.get("sidebar.editor.exit_area")
            if self.translator
            else "Ausgangs-Bereich"
        )
        display_title = (
            self.translator.get("sidebar.editor.display")
            if self.translator
            else "Anzeige"
        )
        visibility_btn = (
            self.translator.get("sidebar.editor.visibility")
            if self.translator
            else "Ebenen / Sichtbarkeit"
        )
        offsets_btn = (
            self.translator.get("sidebar.editor.configure_offsets")
            if self.translator
            else "Offsets Konfigurieren"
        )
        sizes_btn = (
            self.translator.get("sidebar.editor.configure_sizes")
            if self.translator
            else "Größen Konfigurieren"
        )

        gb_areas = QGroupBox(areas_title)
        l_areas_btn = QVBoxLayout(gb_areas)
        self.start_area_button = QPushButton(start_area)
        self.start_area_button.setCheckable(True)
        self.waiting_area_button = QPushButton(waiting_area)
        self.waiting_area_button.setCheckable(True)
        self.btn_exit_area = QPushButton(exit_area)
        self.btn_exit_area.setCheckable(True)
        l_areas_btn.addWidget(self.start_area_button)
        l_areas_btn.addWidget(self.waiting_area_button)
        l_areas_btn.addWidget(self.btn_exit_area)
        l_areas.addWidget(gb_areas)

        gb_view = QGroupBox(display_title)
        l_view = QVBoxLayout(gb_view)
        self.btn_visibility = QPushButton(visibility_btn)
        self.btn_offsets = QPushButton(offsets_btn)
        self.btn_config_sizes = QPushButton(sizes_btn)
        l_view.addWidget(self.btn_visibility)
        l_view.addWidget(self.btn_offsets)
        l_view.addWidget(self.btn_config_sizes)
        l_areas.addWidget(gb_view)

        areas_tab = (
            self.translator.get("sidebar.editor.areas_tab")
            if self.translator
            else "Bereiche"
        )
        self.editor_subtabs.addTab(sub_areas, areas_tab)

        # Sub ROUTEN
        sub_routes = QWidget()
        l_routes = QVBoxLayout(sub_routes)
        l_routes.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Translations for Routes Tab
        new_route_title = (
            self.translator.get("sidebar.editor.new_route")
            if self.translator
            else "Neue Route"
        )
        route_entrance = (
            self.translator.get("sidebar.editor.route_entrance_to_shop")
            if self.translator
            else "Eingang -> Laden"
        )
        route_shop = (
            self.translator.get("sidebar.editor.route_shop_loop")
            if self.translator
            else "Laden (Shop Loop)"
        )
        route_exit = (
            self.translator.get("sidebar.editor.route_checkout_to_exit")
            if self.translator
            else "Kasse -> Ausgang"
        )
        finish_btn = (
            self.translator.get("sidebar.editor.finish")
            if self.translator
            else "✓ Fertig"
        )
        cancel_btn = (
            self.translator.get("sidebar.editor.cancel")
            if self.translator
            else "✕ Abbrechen"
        )
        existing_routes = (
            self.translator.get("sidebar.editor.existing_routes")
            if self.translator
            else "Vorhandene Routen"
        )
        delete_route = (
            self.translator.get("sidebar.editor.delete_route")
            if self.translator
            else "Route löschen"
        )

        gb_route_tools = QGroupBox(new_route_title)
        l_rt = QVBoxLayout(gb_route_tools)
        self.btn_start_route = QPushButton(route_entrance)
        self.btn_start_route.setCheckable(True)
        self.new_route_button = QPushButton(route_shop)
        self.new_route_button.setCheckable(True)
        self.btn_exit_route = QPushButton(route_exit)
        self.btn_exit_route.setCheckable(True)
        l_rt.addWidget(self.btn_start_route)
        l_rt.addWidget(self.new_route_button)
        l_rt.addWidget(self.btn_exit_route)
        l_routes.addWidget(gb_route_tools)

        self.admin_toolbar = QWidget()
        self.admin_toolbar.setVisible(False)
        l_atb = QHBoxLayout(self.admin_toolbar)
        l_atb.setContentsMargins(0, 0, 0, 0)
        self.btn_save_admin = QPushButton(finish_btn)
        self.btn_save_admin.setStyleSheet(
            "background-color: #10B981; color: white; font-weight: bold;"
        )
        self.btn_cancel_route = QPushButton(cancel_btn)
        l_atb.addWidget(self.btn_save_admin)
        l_atb.addWidget(self.btn_cancel_route)
        l_routes.addWidget(self.admin_toolbar)

        gb_route_list = QGroupBox(existing_routes)
        l_rl = QVBoxLayout(gb_route_list)
        self.route_list_widget = QListWidget()
        self.btn_del_route = QPushButton(delete_route)
        l_rl.addWidget(self.route_list_widget)
        l_rl.addWidget(self.btn_del_route)
        l_routes.addWidget(gb_route_list)

        routes_tab = (
            self.translator.get("sidebar.editor.routes_tab")
            if self.translator
            else "Routen"
        )
        self.editor_subtabs.addTab(sub_routes, routes_tab)

        # Sub OBJEKTE
        sub_objs = QWidget()
        l_objs = QVBoxLayout(sub_objs)
        l_objs.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Translations for Objects Tab
        shelves_title = (
            self.translator.get("sidebar.editor.shelves")
            if self.translator
            else "Regale"
        )
        place_shelf = (
            self.translator.get("sidebar.editor.place_shelf")
            if self.translator
            else "+ Regal platzieren"
        )
        checkouts_title = (
            self.translator.get("sidebar.editor.checkouts")
            if self.translator
            else "Kassen"
        )
        checkout_nl = (
            self.translator.get("sidebar.editor.checkout_normal_left")
            if self.translator
            else "Normal (L)"
        )
        checkout_nr = (
            self.translator.get("sidebar.editor.checkout_normal_right")
            if self.translator
            else "Normal (R)"
        )
        checkout_sl = (
            self.translator.get("sidebar.editor.checkout_sb_left")
            if self.translator
            else "SB (L)"
        )
        checkout_sr = (
            self.translator.get("sidebar.editor.checkout_sb_right")
            if self.translator
            else "SB (R)"
        )
        obj_list_title = (
            self.translator.get("sidebar.editor.object_list")
            if self.translator
            else "Objekt Liste"
        )
        edit_btn = (
            self.translator.get("sidebar.editor.edit")
            if self.translator
            else "Bearbeiten"
        )
        delete_btn = (
            self.translator.get("sidebar.editor.delete")
            if self.translator
            else "Löschen"
        )

        gb_shelves = QGroupBox(shelves_title)
        l_sh = QVBoxLayout(gb_shelves)
        self.place_shelves_button = QPushButton(place_shelf)
        self.place_shelves_button.setCheckable(True)
        l_sh.addWidget(self.place_shelves_button)
        l_objs.addWidget(gb_shelves)

        gb_checkouts = QGroupBox(checkouts_title)
        l_ch = QVBoxLayout(gb_checkouts)
        r1 = QHBoxLayout()
        self.btn_kl = QPushButton(checkout_nl)
        self.btn_kl.setCheckable(True)
        self.btn_kr = QPushButton(checkout_nr)
        self.btn_kr.setCheckable(True)
        r1.addWidget(self.btn_kl)
        r1.addWidget(self.btn_kr)
        r2 = QHBoxLayout()
        self.btn_sl = QPushButton(checkout_sl)
        self.btn_sl.setCheckable(True)
        self.btn_sr = QPushButton(checkout_sr)
        self.btn_sr.setCheckable(True)
        r2.addWidget(self.btn_sl)
        r2.addWidget(self.btn_sr)
        l_ch.addLayout(r1)
        l_ch.addLayout(r2)
        l_objs.addWidget(gb_checkouts)

        gb_obj_list = QGroupBox(obj_list_title)
        l_ol = QVBoxLayout(gb_obj_list)
        self.object_list_widget = QListWidget()
        h_act = QHBoxLayout()
        self.btn_edit_obj = QPushButton(edit_btn)
        self.btn_del_obj = QPushButton(delete_btn)
        h_act.addWidget(self.btn_edit_obj)
        h_act.addWidget(self.btn_del_obj)
        l_ol.addWidget(self.object_list_widget)
        l_ol.addLayout(h_act)
        l_objs.addWidget(gb_obj_list)

        objects_tab = (
            self.translator.get("sidebar.editor.objects_tab")
            if self.translator
            else "Objekte"
        )
        self.editor_subtabs.addTab(sub_objs, objects_tab)

        editor_tab = (
            self.translator.get("sidebar.tabs.editor")
            if self.translator
            else "Editor"
        )
        self.main_tabs.addTab(tab_editor_container, editor_tab)

    # ==========================================
    # HELPERS
    # ==========================================

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
        lbl.setPixmap(icon.pixmap(14, 14))  # Kleines Icon
        lbl.setToolTip(tooltip)
        lbl.setCursor(Qt.CursorShape.WhatsThisCursor)
        return lbl

    def _add_gb_header(self, layout, subtitle, tooltip=None):
        """Adds a subtitle row with help icon inside a GroupBox Layout."""
        row = QHBoxLayout()
        row.setContentsMargins(5, 0, 0, 5)  # Etwas Abstand

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
            self.language_changed.emit("en")
        else:
            self.btn_lang.setText("🇩🇪")
            self.language_changed.emit("de")

    def _sync_mode_buttons(self, index):
        if index == 0:
            self.btn_mode_sim.setChecked(True)
            self.btn_mode_edit.setChecked(False)
        else:
            self.btn_mode_sim.setChecked(False)
            self.btn_mode_edit.setChecked(True)

    def refresh_translations(self, translator):
        """Update ALL UI text with new translations. Comprehensive refresh of all widgets."""
        self.translator = translator

        # 1. Update main tab titles
        self.main_tabs.setTabText(0, translator.get("sidebar.tabs.input"))
        self.main_tabs.setTabText(1, translator.get("sidebar.tabs.stats"))
        self.main_tabs.setTabText(2, translator.get("sidebar.tabs.editor"))

        # 2. Update input subtabs
        if self.input_sub_tabs.count() > 0:
            self.input_sub_tabs.setTabText(
                0, translator.get("sidebar.input.shop_tab")
            )
        if self.input_sub_tabs.count() > 1:
            self.input_sub_tabs.setTabText(
                1, translator.get("sidebar.input.customers_tab")
            )
        if self.input_sub_tabs.count() > 2:
            self.input_sub_tabs.setTabText(
                2, translator.get("sidebar.input.staff_tab")
            )
        if self.input_sub_tabs.count() > 3:
            self.input_sub_tabs.setTabText(
                3, translator.get("sidebar.input.conflicts_tab")
            )

        # 3. Update editor subtabs
        if hasattr(self, "editor_subtabs") and self.editor_subtabs:
            if self.editor_subtabs.count() > 0:
                self.editor_subtabs.setTabText(
                    0, translator.get("sidebar.editor.map_tab")
                )
            if self.editor_subtabs.count() > 1:
                self.editor_subtabs.setTabText(
                    1, translator.get("sidebar.editor.areas_tab")
                )
            if self.editor_subtabs.count() > 2:
                self.editor_subtabs.setTabText(
                    2, translator.get("sidebar.editor.routes_tab")
                )
            if self.editor_subtabs.count() > 3:
                self.editor_subtabs.setTabText(
                    3, translator.get("sidebar.editor.objects_tab")
                )

        # 4. Recursively update all widgets in the sidebar
        self._update_all_widgets(self, translator)

    def _update_all_widgets(self, widget, translator):
        """Recursively update all child widgets with translations."""
        if isinstance(widget, QGroupBox):
            # Update group box titles - find the translation key
            current_title = widget.title()
            new_title = self._translate_text(current_title, translator)
            if new_title != current_title:
                widget.setTitle(new_title)

        elif isinstance(widget, QPushButton):
            # Update button text
            current_text = widget.text()
            if current_text and current_text.strip():
                new_text = self._translate_text(current_text, translator)
                if new_text != current_text:
                    widget.setText(new_text)

            # Update button tooltips
            tooltip = widget.toolTip()
            if tooltip:
                new_tooltip = self._translate_text(tooltip, translator)
                if new_tooltip != tooltip:
                    widget.setToolTip(new_tooltip)

        elif isinstance(widget, QLabel):
            # Update label text
            current_text = widget.text()
            if (
                current_text
                and current_text.strip()
                and not current_text.isspace()
            ):
                new_text = self._translate_text(current_text, translator)
                if new_text != current_text:
                    widget.setText(new_text)

        elif isinstance(widget, QFormLayout):
            # Update form layout labels
            for i in range(widget.rowCount()):
                label_item = widget.itemAt(i, QFormLayout.ItemRole.LabelRole)
                if label_item and isinstance(label_item.widget(), QLabel):
                    label_widget = label_item.widget()
                    current_text = label_widget.text()
                    if current_text:
                        new_text = self._translate_text(
                            current_text, translator
                        )
                        if new_text != current_text:
                            label_widget.setText(new_text)

        # Recursively process all children
        if hasattr(widget, "children"):
            for child in widget.children():
                if child:
                    self._update_all_widgets(child, translator)

    def _translate_text(self, text, translator):
        """Attempt to find translation for text by checking all known translation keys."""
        # Create a mapping of display text to translation keys
        text_mapping = {
            # Shop Tab
            "Karte wählen": "sidebar.input.map_select",
            "Zeitsteuerung": "sidebar.input.time_control",
            "Öffnen:": "sidebar.input.time_open",
            "Schließen:": "sidebar.input.time_close",
            # Customer Tab
            "Kundenaufkommen": "sidebar.input.customer_volume",
            "Kunden / Tag:": "sidebar.input.customers_per_day",
            "Anteil Beeintr.:": "sidebar.input.share_disabled",
            "Geschwindigkeit": "sidebar.input.speed",
            "Gehen:": "sidebar.input.walking",
            "Rollen:": "sidebar.input.rolling",
            "Einkaufswagen": "sidebar.input.shopping_cart",
            "Artikel:": "sidebar.input.items",
            "Handscanner:": "sidebar.input.hand_scanner",
            "Scan-Dauer (Kunde)": "sidebar.input.scan_duration",
            "Normal:": "sidebar.input.scan_normal",
            "Einges.:": "sidebar.input.scan_disabled",
            "Zahlungsmethoden": "sidebar.input.payment_methods",
            "Bargeld:": "sidebar.input.payment_cash",
            "Karte:": "sidebar.input.payment_card",
            # Staff Tab
            "Kassierer Geschwindigkeit": "sidebar.input.cashier_speed",
            "Azubi:": "sidebar.input.cashier_newbie",
            "Profi:": "sidebar.input.cashier_pro",
            "Bezahldauer": "sidebar.input.payment_duration",
            "Bargeld (Bezahlung):": "sidebar.input.payment_cash_label",
            "Karte (Bezahlung):": "sidebar.input.payment_card_label",
            "Konfliktbewältigung": "sidebar.input.conflict_resolution",
            "Dauer:": "sidebar.input.conflict_duration",
            # Conflicts Tab
            "Kassenstörungen": "sidebar.input.checkout_failures",
            "Ausfall (Normal):": "sidebar.input.failure_normal",
            "Ausfall (SB):": "sidebar.input.failure_sb",
            "Verärgerung der Kunden": "sidebar.input.customer_annoyance",
            "Verärgerung:": "sidebar.input.annoyance_rate",
            # Stats Tab
            "Live Daten": "sidebar.stats.live_data",
            "Ereignis-Protokoll": "sidebar.stats.event_log",
            # Editor: Map Tab
            "Datei": "sidebar.editor.map_file",
            "Neue Karte": "sidebar.editor.new_map",
            "Karte Speichern": "sidebar.editor.save_map",
            "Karte Löschen": "sidebar.editor.delete_map",
            "Hintergrund": "sidebar.editor.background",
            "Bild laden...": "sidebar.editor.load_image",
            "Bild entfernen": "sidebar.editor.remove_image",
            "Zoom:": "sidebar.editor.zoom",
            "Optionen": "sidebar.editor.map_options",
            "Karte verschieben": "sidebar.editor.move_map",
            "Exit Richtung:": "sidebar.editor.exit_direction",
            # Editor: Areas Tab
            "Flächen zeichnen": "sidebar.editor.draw_areas",
            "Start-Bereich": "sidebar.editor.start_area",
            "Warte-Bereich": "sidebar.editor.waiting_area",
            "Ausgangs-Bereich": "sidebar.editor.exit_area",
            "Anzeige": "sidebar.editor.display",
            "Ebenen / Sichtbarkeit": "sidebar.editor.visibility",
            "Offsets Konfigurieren": "sidebar.editor.configure_offsets",
            "Größen Konfigurieren": "sidebar.editor.configure_sizes",
            # Editor: Routes Tab
            "Neue Route": "sidebar.editor.new_route",
            "Eingang -> Laden": "sidebar.editor.route_entrance_to_shop",
            "Laden (Shop Loop)": "sidebar.editor.route_shop_loop",
            "Kasse -> Ausgang": "sidebar.editor.route_checkout_to_exit",
            "✓ Fertig": "sidebar.editor.finish",
            "✕ Abbrechen": "sidebar.editor.cancel",
            "Vorhandene Routen": "sidebar.editor.existing_routes",
            "Route löschen": "sidebar.editor.delete_route",
            # Editor: Objects Tab
            "Regale": "sidebar.editor.shelves",
            "+ Regal platzieren": "sidebar.editor.place_shelf",
            "Kassen": "sidebar.editor.checkouts",
            "Normal (L)": "sidebar.editor.checkout_normal_left",
            "Normal (R)": "sidebar.editor.checkout_normal_right",
            "SB (L)": "sidebar.editor.checkout_sb_left",
            "SB (R)": "sidebar.editor.checkout_sb_right",
            "Objekt Liste": "sidebar.editor.object_list",
            "Bearbeiten": "sidebar.editor.edit",
            "Löschen": "sidebar.editor.delete",
        }

        # Look up text in mapping
        if text in text_mapping:
            trans_key = text_mapping[text]
            translated = translator.get(trans_key)
            if translated and translated != text:
                return translated

        # Return original if no translation found
        return text

    def _store_widget_ref(self, widget, trans_key):
        """Store widget reference for translation updates."""
        key = f"widget_{id(widget)}"
        self.widget_refs[key] = widget
        self.widget_refs[f"{key}_trans_key"] = trans_key
        return widget
