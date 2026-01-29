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
import random
from config import COLOR_ACCENT, COLOR_ERROR, COLOR_SUCCESS, COLOR_BG_PANEL


class Sidebar(QWidget):
    back_to_menu_requested = pyqtSignal()  # Signal to go back to main menu

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
            QPushButton.HeaderBtn:hover {{
                background-color: #F8FAFC;
                border-color: {accent};
                color: {accent};
            }}
            QPushButton.HeaderBtn:pressed {{
                background-color: {accent};
                color: white;
                border: 1px solid {accent};
            }}
            QPushButton.HeaderBtn:checked {{
                background-color: {accent};
                color: white;
                border: 1px solid {accent};
            }}
            QPushButton#BtnMainMenu {{
                font-size: 18px;
            }}
            QPushButton#BtnRandomize {{
                font-size: 18px;
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
            /* Form labels + inputs symmetry */
            QLabel {{
                font-size: 14px;
                color: #374151;
            }}
            QSpinBox, QDoubleSpinBox, QTimeEdit, QComboBox {{
                min-height: 32px;
                font-size: 14px;
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
        self.btn_mode_sim.setToolTip(
            self.translator.get("tooltips.button_mode_sim")
            if self.translator
            else "Simulationmodus"
        )
        self.btn_mode_sim.setStyleSheet(
            "border-top-right-radius: 0; border-bottom-right-radius: 0; border-right: none;"
        )

        self.btn_mode_edit = QPushButton(edit_text)
        self.btn_mode_edit.setProperty("class", "HeaderBtn")
        self.btn_mode_edit.setCheckable(True)
        self.btn_mode_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_edit.setToolTip(
            self.translator.get("tooltips.button_mode_edit")
            if self.translator
            else "Editormodus"
        )
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

        # Randomize Button (Shuffle)
        rand_tooltip = (
            self.translator.get("sidebar.input.randomize_tooltip")
            if self.translator
            else "Alle Eingabeparameter zufällig befüllen"
        )
        rand_tooltip = f"<span style=\"font-size:11px;\">{rand_tooltip}</span>"
        self.btn_randomize = QPushButton("🔀")
        self.btn_randomize.setObjectName("BtnRandomize")
        self.btn_randomize.setProperty("class", "HeaderBtn")
        self.btn_randomize.setCheckable(False)
        self.btn_randomize.setFixedWidth(60)
        self.btn_randomize.setToolTip(rand_tooltip)
        self.btn_randomize.clicked.connect(self._randomize_input_params)
        h_layout.addWidget(self.btn_randomize, 0)

        # Main Menu Button (Home)
        self.btn_main_menu = QPushButton("🏠")  # House emoji
        self.btn_main_menu.setObjectName("BtnMainMenu")
        self.btn_main_menu.setProperty("class", "HeaderBtn")
        self.btn_main_menu.setCheckable(False)
        self.btn_main_menu.setFixedWidth(60)
        tooltip_text = (
            self.translator.get("sidebar.main_menu_tooltip")
            if self.translator
            else "Zurück zum Hauptmenü"
        )
        tooltip_text = f"<span style=\"font-size:11px;\">{tooltip_text}</span>"
        self.btn_main_menu.setToolTip(tooltip_text)
        self.btn_main_menu.clicked.connect(self._go_to_main_menu)
        h_layout.addWidget(self.btn_main_menu, 0)

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

        # Blockierungs-Meldung (wird anfangs versteckt)
        self.input_blocked_warning = QLabel()
        self.input_blocked_warning.setStyleSheet(
            """
            QLabel {
                background-color: #FEE2E2;
                color: #991B1B;
                padding: 10px;
                border-radius: 4px;
                border-left: 4px solid #DC2626;
                font-weight: bold;
                font-size: 11px;
            }
            """
        )
        self.input_blocked_warning.setWordWrap(True)
        self.input_blocked_warning.setVisible(False)
        l_input_main.addWidget(self.input_blocked_warning)

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
        l_shop_root = QVBoxLayout(sub_shop)
        l_shop_root.setContentsMargins(0, 0, 0, 0)
        scroll_shop = QScrollArea()
        scroll_shop.setWidgetResizable(True)
        scroll_shop.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        content_shop = QWidget()
        l_shop = QVBoxLayout(content_shop)
        l_shop.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 1. Map
        map_select_text = (
            self.translator.get("sidebar.input.map_select")
            if self.translator
            else "Karte wählen"
        )
        gb_map = QGroupBox(map_select_text)
        v_map = QVBoxLayout(gb_map)
        dist_none = (
            self.translator.get("sidebar.input.dist_none")
            if self.translator
            else "(keine Verteilungsform)"
        )
        map_desc = (
            self.translator.get("tooltips.map_select")
            if self.translator
            else "Wechselt die Map (Layout, Routen, Bereiche)."
        )
        self._add_gb_header(v_map, dist_none, map_desc)
        self.map_combo = QComboBox()
        self.map_combo.setToolTip(map_desc)
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
        time_desc = (
            self.translator.get("tooltips.time_control")
            if self.translator
            else "Legt Öffnungs- und Schließzeit des Ladens fest."
        )
        self._add_gb_header(v_time, dist_none, time_desc)
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

        # 3. Customer Volume (moved from Customers tab)
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
            else "Zeitabstände zwischen Kunden folgen einer Exponentialverteilung."
        )
        dist_exponential = (
            self.translator.get("sidebar.input.dist_exponential")
            if self.translator
            else "(Exponentialverteilung)"
        )
        disabled_desc = (
            self.translator.get("tooltips.share_disabled")
            if self.translator
            else "Anteil an Kunden mit Beeinträchtigung (in %)."
        )
        gb_spawn = QGroupBox(cv_title)
        v_spawn = QVBoxLayout(gb_spawn)
        self._add_gb_header(v_spawn, dist_exponential, cv_desc)
        f_spawn = QFormLayout()
        self.actor_count_input = self._create_spin(50, 1, 10000)
        self.disabled_prob_input = self._create_spin(10, 0, 100, " %")
        self.disabled_prob_input.setToolTip(disabled_desc)
        f_spawn.addRow(cv_day, self.actor_count_input)
        f_spawn.addRow(cv_share, self.disabled_prob_input)
        v_spawn.addLayout(f_spawn)
        l_shop.addWidget(gb_spawn)

        checkout_hint = (
            self.translator.get("sidebar.input.checkout_hint")
            if self.translator
            else "Tipp: Kasse anklicken, um Öffnungsstatus, Warteschlange und Kassierertyp zu ändern."
        )
        lbl_hint = QLabel(checkout_hint)
        lbl_hint.setWordWrap(True)
        lbl_hint.setStyleSheet(
            "background-color: #EFF6FF; color: #1E40AF; padding: 8px; border-radius: 6px; font-size: 11px;"
        )
        l_shop.addWidget(lbl_hint)

        shop_tab_text = (
            self.translator.get("sidebar.input.shop_tab")
            if self.translator
            else "Laden"
        )
        scroll_shop.setWidget(content_shop)
        l_shop_root.addWidget(scroll_shop)
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

        # 1. Speed
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
        dist_normal = (
            self.translator.get("sidebar.input.dist_normal")
            if self.translator
            else "(Normalverteilung)"
        )
        gb_speed = QGroupBox(speed_title)
        v_speed = QVBoxLayout(gb_speed)
        self._add_gb_header(
            v_speed,
            dist_normal,
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
        handheld_desc = (
            self.translator.get("tooltips.hand_scanner")
            if self.translator
            else "Kunde scannt mit Handscanner und muss an der Kasse nur einmal scannen."
        )
        dist_normal = (
            self.translator.get("sidebar.input.dist_normal")
            if self.translator
            else "(Normalverteilung)"
        )
        gb_cart = QGroupBox(cart_title)
        v_cart = QVBoxLayout(gb_cart)
        self._add_gb_header(v_cart, dist_normal, cart_desc)
        f_cart = QFormLayout()
        self.items_mean = self._create_spin(15, 1, 100)
        self.items_std = self._create_spin(5, 0, 50)
        # Custom Row for Items
        h_it = QHBoxLayout()
        h_it.addWidget(QLabel("Ø:"))
        h_it.addWidget(self.items_mean)
        h_it.addWidget(QLabel("σ:"))
        h_it.addWidget(self.items_std)
        f_cart.addRow(cart_items, h_it)

        self.hand_scanner_prob = self._create_spin(20, 0, 100, " %")
        self.hand_scanner_prob.setToolTip(handheld_desc)
        f_cart.addRow(cart_scanner, self.hand_scanner_prob)
        v_cart.addLayout(f_cart)
        l_gb_cust.addWidget(gb_cart)

        # 4. Scan Speed (Customer side - SB)
        scan_title = (
            self.translator.get("sidebar.input.scan_duration")
            if self.translator
            else "Scan-Geschwindigkeit"
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
            else "Zeit pro Artikel (gleichverteilt zwischen Min und Max)."
        )
        dist_uniform = (
            self.translator.get("sidebar.input.dist_uniform")
            if self.translator
            else "(Gleichverteilung)"
        )
        gb_scan = QGroupBox(scan_title)
        v_scan = QVBoxLayout(gb_scan)
        self._add_gb_header(
            v_scan,
            dist_uniform,
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
            else "Legt die Wahrscheinlichkeit für Bargeld/Karte fest (Summe 100%)."
        )
        dist_percent = (
            self.translator.get("sidebar.input.dist_percent")
            if self.translator
            else "(Verteilung in %)"
        )
        gb_pay = QGroupBox(payment_title)
        v_pay = QVBoxLayout(gb_pay)
        self._add_gb_header(v_pay, dist_percent, payment_desc)
        f_pay = QFormLayout()
        self.payment_cash = self._create_spin(30, 0, 100, " %")
        self.payment_card = self._create_spin(70, 0, 100, " %")
        # Auto-Balance Logic
        self.payment_cash.valueChanged.connect(
            lambda v: self.payment_card.setValue(int(100 - v))
        )
        self.payment_card.valueChanged.connect(
            lambda v: self.payment_cash.setValue(int(100 - v))
        )
        f_pay.addRow(payment_cash, self.payment_cash)
        f_pay.addRow(payment_card, self.payment_card)
        v_pay.addLayout(f_pay)
        l_gb_cust.addWidget(gb_pay)

        # 6. Payment Duration (SB)
        sb_pay_title = (
            self.translator.get("sidebar.input.payment_duration_sb")
            if self.translator
            else "Bezahldauer (SB)"
        )
        sb_pay_label = (
            self.translator.get("sidebar.input.payment_duration_sb_label")
            if self.translator
            else "Dauer:"
        )
        sb_pay_desc = (
            self.translator.get("tooltips.paytime_sb")
            if self.translator
            else "Dauer des Bezahlvorgangs an SB-Kassen."
        )
        dist_uniform_seconds = (
            self.translator.get("sidebar.input.dist_uniform_seconds")
            if self.translator
            else "(Sekunden - Gleichverteilung)"
        )
        gb_pay_sb = QGroupBox(sb_pay_title)
        v_pay_sb = QVBoxLayout(gb_pay_sb)
        self._add_gb_header(v_pay_sb, dist_uniform_seconds, sb_pay_desc)
        f_pay_sb = QFormLayout()
        self.pay_duration_sb_min, self.pay_duration_sb_max = (
            self._create_range_row(sb_pay_label, 2.0, 6.0, f_pay_sb)
        )
        v_pay_sb.addLayout(f_pay_sb)
        l_gb_cust.addWidget(gb_pay_sb)

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
        l_staff_root = QVBoxLayout(tab_staff)
        l_staff_root.setContentsMargins(0, 0, 0, 0)
        scroll_staff = QScrollArea()
        scroll_staff.setWidgetResizable(True)
        scroll_staff.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        content_staff = QWidget()
        l_staff = QVBoxLayout(content_staff)
        l_staff.setAlignment(Qt.AlignmentFlag.AlignTop)
        l_staff.setSpacing(15)

        # Translations
        cashier_title = (
            self.translator.get("sidebar.input.cashier_speed")
            if self.translator
            else "Scan-Geschwindigkeit"
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
        dist_uniform_sec_item = (
            self.translator.get("sidebar.input.dist_uniform_sec_item")
            if self.translator
            else "(Sek/Artikel - Gleichverteilung)"
        )
        dist_uniform_seconds = (
            self.translator.get("sidebar.input.dist_uniform_seconds")
            if self.translator
            else "(Sekunden - Gleichverteilung)"
        )

        # 1. Cashier Scan
        gb_cashier = QGroupBox(cashier_title)
        v_cashier = QVBoxLayout(gb_cashier)
        self._add_gb_header(
            v_cashier,
            dist_uniform_sec_item,
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
            dist_uniform_seconds,
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
            dist_uniform_seconds,
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
        scroll_staff.setWidget(content_staff)
        l_staff_root.addWidget(scroll_staff)
        self.input_sub_tabs.addTab(tab_staff, staff_tab)

    def _setup_conflicts_tab(self):
        tab_conflicts = QWidget()
        l_conflicts_root = QVBoxLayout(tab_conflicts)
        l_conflicts_root.setContentsMargins(0, 0, 0, 0)
        scroll_conflicts = QScrollArea()
        scroll_conflicts.setWidgetResizable(True)
        scroll_conflicts.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        content_conflicts = QWidget()
        l_conflicts = QVBoxLayout(content_conflicts)
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
        dist_probability_percent = (
            self.translator.get("sidebar.input.dist_probability_percent")
            if self.translator
            else "(Wahrscheinlichkeit in %)"
        )

        # 1. Failures
        gb_co = QGroupBox(checkout_title)
        v_co = QVBoxLayout(gb_co)
        self._add_gb_header(
            v_co,
            dist_probability_percent,
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
            dist_probability_percent,
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
        scroll_conflicts.setWidget(content_conflicts)
        l_conflicts_root.addWidget(scroll_conflicts)
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
        overview_title = (
            self.translator.get("sidebar.stats.overview")
            if self.translator
            else "Überblick"
        )
        queue_title = (
            self.translator.get("sidebar.stats.queue_section")
            if self.translator
            else "Warteschlange"
        )
        performance_title = (
            self.translator.get("sidebar.stats.performance_section")
            if self.translator
            else "Leistung"
        )
        time_title = (
            self.translator.get("sidebar.stats.time_section")
            if self.translator
            else "Zeit"
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
        longest_queue_label = (
            self.translator.get("sidebar.stats.longest_queue")
            if self.translator
            else "Längste Queue:"
        )
        avg_wait_label = (
            self.translator.get("sidebar.stats.avg_wait")
            if self.translator
            else "Ø Wartezeit:"
        )
        throughput_label = (
            self.translator.get("sidebar.stats.throughput")
            if self.translator
            else "Durchsatz:"
        )
        available_checkouts_label = (
            self.translator.get("sidebar.stats.available_checkouts")
            if self.translator
            else "Kassen verfügbar:"
        )
        satisfaction_label = (
            self.translator.get("sidebar.stats.satisfaction")
            if self.translator
            else "Zufriedenheit:"
        )
        elapsed_open_label = (
            self.translator.get("sidebar.stats.elapsed_open")
            if self.translator
            else "Geöffnet (bisher):"
        )
        scheduled_open_label = (
            self.translator.get("sidebar.stats.scheduled_open")
            if self.translator
            else "Geplant geöffnet:"
        )
        overtime_label = (
            self.translator.get("sidebar.stats.overtime")
            if self.translator
            else "Überzeit:"
        )
        report_button_label = (
            self.translator.get("sidebar.stats.open_report")
            if self.translator
            else "Bericht öffnen"
        )
        report_button_tooltip = (
            self.translator.get("sidebar.stats.open_report_tooltip")
            if self.translator
            else "Öffnet die ausführliche Statistikübersicht"
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
        self.lbl_longest_queue = QLabel("0")
        self.lbl_avg_wait = QLabel("0.0 min")
        self.lbl_throughput = QLabel("0.0 /h")
        self.lbl_available_checkouts = QLabel("0/0")
        self.lbl_satisfaction_score = QLabel("0%")
        self.lbl_elapsed_open = QLabel("0:00")
        self.lbl_scheduled_open = QLabel("0:00")
        self.lbl_overtime = QLabel("0:00")

        f_stats_grid = QVBoxLayout(self.gb_stats)

        gb_overview = QGroupBox(overview_title)
        f_overview = QFormLayout(gb_overview)
        f_overview.addRow(store_label, self.lbl_customers_in_store)
        f_overview.addRow(total_label, self.lbl_total_customers)

        gb_queue = QGroupBox(queue_title)
        f_queue = QFormLayout(gb_queue)
        f_queue.addRow(queue_label, self.lbl_queue_count)
        f_queue.addRow(longest_queue_label, self.lbl_longest_queue)
        f_queue.addRow(avg_wait_label, self.lbl_avg_wait)

        gb_perf = QGroupBox(performance_title)
        f_perf = QFormLayout(gb_perf)
        f_perf.addRow(throughput_label, self.lbl_throughput)
        f_perf.addRow(available_checkouts_label, self.lbl_available_checkouts)
        f_perf.addRow(satisfaction_label, self.lbl_satisfaction_score)

        gb_time = QGroupBox(time_title)
        f_time = QFormLayout(gb_time)
        f_time.addRow(elapsed_open_label, self.lbl_elapsed_open)
        f_time.addRow(scheduled_open_label, self.lbl_scheduled_open)
        f_time.addRow(overtime_label, self.lbl_overtime)

        f_stats_grid.addWidget(gb_overview)
        f_stats_grid.addWidget(gb_queue)
        f_stats_grid.addWidget(gb_perf)
        f_stats_grid.addWidget(gb_time)
        self.btn_open_report = QPushButton(report_button_label)
        self.btn_open_report.setToolTip(report_button_tooltip)
        f_stats_grid.addWidget(self.btn_open_report)
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
            else "Grundriss"
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

        gb_map_file = QGroupBox(file_title)
        l_map_file = QVBoxLayout(gb_map_file)
        self.btn_new_map = QPushButton(new_map)
        self.btn_new_map.setToolTip(
            self.translator.get("tooltips.button_new_map")
            if self.translator
            else "Neue Karte anlegen"
        )
        self.btn_save_map = QPushButton(save_map)
        self.btn_save_map.setToolTip(
            self.translator.get("tooltips.button_save_map")
            if self.translator
            else "Karte speichern"
        )
        self.btn_delete_map = QPushButton(delete_map)
        self.btn_delete_map.setToolTip(
            self.translator.get("tooltips.button_delete_map")
            if self.translator
            else "Karte löschen"
        )
        l_map_file.addWidget(self.btn_new_map)
        l_map_file.addWidget(self.btn_save_map)
        l_map_file.addWidget(self.btn_delete_map)
        l_map.addWidget(gb_map_file)

        gb_map_bg = QGroupBox(bg_title)
        l_map_bg = QVBoxLayout(gb_map_bg)
        self.btn_set_background = QPushButton(load_image)
        self.btn_set_background.setToolTip(
            self.translator.get("tooltips.button_load_background")
            if self.translator
            else "Grundriss laden"
        )
        self.btn_remove_background = QPushButton(remove_image)
        self.btn_remove_background.setToolTip(
            self.translator.get("tooltips.button_remove_background")
            if self.translator
            else "Grundriss entfernen"
        )
        h_scale = QHBoxLayout()
        h_scale.addWidget(QLabel(zoom_label))
        self.spin_bg_scale = QDoubleSpinBox()
        self.spin_bg_scale.setRange(0.01, 5.0)
        self.spin_bg_scale.setSingleStep(0.01)
        self.spin_bg_scale.setDecimals(2)
        self.spin_bg_scale.setValue(0.09)
        h_scale.addWidget(self.spin_bg_scale)
        l_map_bg.addWidget(self.btn_set_background)
        l_map_bg.addWidget(self.btn_remove_background)
        l_map_bg.addLayout(h_scale)
        l_map.addWidget(gb_map_bg)

        gb_map_opts = QGroupBox(options_title)
        l_map_opts = QVBoxLayout(gb_map_opts)
        self.btn_move_map = QPushButton(move_map_btn)
        self.btn_move_map.setCheckable(True)
        self.btn_move_map.setToolTip(
            self.translator.get("tooltips.button_move_map")
            if self.translator
            else "Karte verschieben"
        )
        l_map_opts.addWidget(self.btn_move_map)
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
        self.start_area_button.setToolTip(
            self.translator.get("tooltips.button_start_area")
            if self.translator
            else "Startbereich zeichnen"
        )
        self.waiting_area_button = QPushButton(waiting_area)
        self.waiting_area_button.setCheckable(True)
        self.waiting_area_button.setToolTip(
            self.translator.get("tooltips.button_waiting_area")
            if self.translator
            else "Wartebereich zeichnen"
        )
        self.btn_exit_area = QPushButton(exit_area)
        self.btn_exit_area.setCheckable(True)
        self.btn_exit_area.setToolTip(
            self.translator.get("tooltips.button_exit_area")
            if self.translator
            else "Ausgangsbereich zeichnen"
        )
        l_areas_btn.addWidget(self.start_area_button)
        l_areas_btn.addWidget(self.waiting_area_button)
        l_areas_btn.addWidget(self.btn_exit_area)
        l_areas.addWidget(gb_areas)

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
        self.btn_start_route.setToolTip(
            self.translator.get("tooltips.button_route_start")
            if self.translator
            else "Route Eingang → Laden"
        )
        self.new_route_button = QPushButton(route_shop)
        self.new_route_button.setCheckable(True)
        self.new_route_button.setToolTip(
            self.translator.get("tooltips.button_route_shop")
            if self.translator
            else "Route Shop-Loop"
        )
        self.btn_exit_route = QPushButton(route_exit)
        self.btn_exit_route.setCheckable(True)
        self.btn_exit_route.setToolTip(
            self.translator.get("tooltips.button_route_exit")
            if self.translator
            else "Route Kasse → Ausgang"
        )
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
        self.btn_save_admin.setToolTip(
            self.translator.get("tooltips.button_route_finish")
            if self.translator
            else "Route speichern"
        )
        self.btn_cancel_route = QPushButton(cancel_btn)
        self.btn_cancel_route.setToolTip(
            self.translator.get("tooltips.button_route_cancel")
            if self.translator
            else "Routenmodus beenden"
        )
        l_atb.addWidget(self.btn_save_admin)
        l_atb.addWidget(self.btn_cancel_route)
        l_routes.addWidget(self.admin_toolbar)

        gb_route_list = QGroupBox(existing_routes)
        l_rl = QVBoxLayout(gb_route_list)
        self.route_list_widget = QListWidget()
        self.btn_del_route = QPushButton(delete_route)
        self.btn_del_route.setToolTip(
            self.translator.get("tooltips.button_route_delete")
            if self.translator
            else "Route löschen"
        )
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
        checkout_normal = (
            self.translator.get("sidebar.editor.checkout_normal")
            if self.translator
            else "Normal"
        )
        checkout_sb = (
            self.translator.get("sidebar.editor.checkout_sb")
            if self.translator
            else "SB"
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
        self.place_shelves_button.setToolTip(
            self.translator.get("tooltips.button_place_shelf")
            if self.translator
            else "Regal platzieren"
        )
        l_sh.addWidget(self.place_shelves_button)
        l_objs.addWidget(gb_shelves)

        gb_checkouts = QGroupBox(checkouts_title)
        l_ch = QVBoxLayout(gb_checkouts)
        r1 = QHBoxLayout()
        self.btn_checkout_normal = QPushButton(checkout_normal)
        self.btn_checkout_normal.setCheckable(True)
        self.btn_checkout_normal.setToolTip(
            self.translator.get("tooltips.button_place_checkout_normal")
            if self.translator
            else "Normalkasse platzieren"
        )
        self.btn_checkout_sb = QPushButton(checkout_sb)
        self.btn_checkout_sb.setCheckable(True)
        self.btn_checkout_sb.setToolTip(
            self.translator.get("tooltips.button_place_checkout_sb")
            if self.translator
            else "SB-Kasse platzieren"
        )
        r1.addWidget(self.btn_checkout_normal)
        r1.addWidget(self.btn_checkout_sb)
        l_ch.addLayout(r1)
        l_objs.addWidget(gb_checkouts)

        gb_obj_list = QGroupBox(obj_list_title)
        l_ol = QVBoxLayout(gb_obj_list)
        self.object_list_widget = QListWidget()
        h_act = QHBoxLayout()
        self.btn_edit_obj = QPushButton(edit_btn)
        self.btn_del_obj = QPushButton(delete_btn)
        self.btn_edit_obj.setToolTip(
            self.translator.get("tooltips.button_edit_object")
            if self.translator
            else "Objekt bearbeiten"
        )
        self.btn_del_obj.setToolTip(
            self.translator.get("tooltips.button_delete_object")
            if self.translator
            else "Objekt löschen"
        )
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

        # Sub ANZEIGE (nach Objekte)
        sub_display = QWidget()
        l_display = QVBoxLayout(sub_display)
        l_display.setAlignment(Qt.AlignmentFlag.AlignTop)

        gb_view = QGroupBox(display_title)
        l_view = QVBoxLayout(gb_view)
        self.btn_visibility = QPushButton(visibility_btn)
        self.btn_visibility.setToolTip(
            self.translator.get("tooltips.button_visibility")
            if self.translator
            else "Sichtbarkeit einstellen"
        )
        self.btn_offsets = QPushButton(offsets_btn)
        self.btn_offsets.setToolTip(
            self.translator.get("tooltips.button_offsets")
            if self.translator
            else "Offsets einstellen"
        )
        self.btn_config_sizes = QPushButton(sizes_btn)
        self.btn_config_sizes.setToolTip(
            self.translator.get("tooltips.button_sizes")
            if self.translator
            else "Größen einstellen"
        )
        l_view.addWidget(self.btn_visibility)
        l_view.addWidget(self.btn_offsets)
        l_view.addWidget(self.btn_config_sizes)
        l_display.addWidget(gb_view)

        display_tab = display_title
        self.editor_subtabs.addTab(sub_display, display_tab)

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

    def _randomize_input_params(self):
        def rand_spin(sb: QSpinBox):
            sb.setValue(random.randint(sb.minimum(), sb.maximum()))

        def rand_double(dsb: QDoubleSpinBox):
            min_v = dsb.minimum()
            max_v = dsb.maximum()
            val = random.uniform(min_v, max_v)
            step = dsb.singleStep() or 0.1
            decimals = dsb.decimals()
            val = round(round(val / step) * step, decimals)
            dsb.setValue(val)

        def rand_time(te: QTimeEdit):
            h = random.randint(0, 23)
            m = random.randint(0, 59)
            te.setTime(QTime(h, m))

        # Shop
        if hasattr(self, "time_open"):
            rand_time(self.time_open)
        if hasattr(self, "time_close"):
            rand_time(self.time_close)
        if hasattr(self, "actor_count_input"):
            rand_spin(self.actor_count_input)
        if hasattr(self, "disabled_prob_input"):
            rand_spin(self.disabled_prob_input)

        # Customer
        if hasattr(self, "speed_walk_mean"):
            rand_double(self.speed_walk_mean)
        if hasattr(self, "speed_walk_std"):
            rand_double(self.speed_walk_std)
        if hasattr(self, "speed_roll_mean"):
            rand_double(self.speed_roll_mean)
        if hasattr(self, "speed_roll_std"):
            rand_double(self.speed_roll_std)
        if hasattr(self, "items_mean"):
            rand_spin(self.items_mean)
        if hasattr(self, "items_std"):
            rand_spin(self.items_std)
        if hasattr(self, "hand_scanner_prob"):
            rand_spin(self.hand_scanner_prob)
        if hasattr(self, "scan_speed_normal_min"):
            rand_double(self.scan_speed_normal_min)
        if hasattr(self, "scan_speed_normal_max"):
            rand_double(self.scan_speed_normal_max)
        if hasattr(self, "scan_speed_disabled_min"):
            rand_double(self.scan_speed_disabled_min)
        if hasattr(self, "scan_speed_disabled_max"):
            rand_double(self.scan_speed_disabled_max)
        if hasattr(self, "payment_cash") and hasattr(self, "payment_card"):
            cash = random.randint(0, 100)
            self.payment_cash.setValue(cash)
            self.payment_card.setValue(100 - cash)
        if hasattr(self, "pay_duration_sb_min"):
            rand_double(self.pay_duration_sb_min)
        if hasattr(self, "pay_duration_sb_max"):
            rand_double(self.pay_duration_sb_max)

        # Staff
        if hasattr(self, "scan_speed_newbie_min"):
            rand_double(self.scan_speed_newbie_min)
        if hasattr(self, "scan_speed_newbie_max"):
            rand_double(self.scan_speed_newbie_max)
        if hasattr(self, "scan_speed_pro_min"):
            rand_double(self.scan_speed_pro_min)
        if hasattr(self, "scan_speed_pro_max"):
            rand_double(self.scan_speed_pro_max)
        if hasattr(self, "pay_duration_cash_min"):
            rand_double(self.pay_duration_cash_min)
        if hasattr(self, "pay_duration_cash_max"):
            rand_double(self.pay_duration_cash_max)
        if hasattr(self, "pay_duration_card_min"):
            rand_double(self.pay_duration_card_min)
        if hasattr(self, "pay_duration_card_max"):
            rand_double(self.pay_duration_card_max)
        if hasattr(self, "worker_repair_min"):
            rand_double(self.worker_repair_min)
        if hasattr(self, "worker_repair_max"):
            rand_double(self.worker_repair_max)

        # Conflicts
        if hasattr(self, "checkout_fail_rate_normal"):
            rand_spin(self.checkout_fail_rate_normal)
        if hasattr(self, "checkout_fail_rate_sb"):
            rand_spin(self.checkout_fail_rate_sb)
        if hasattr(self, "customer_annoyance_rate"):
            rand_spin(self.customer_annoyance_rate)

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

    def _go_to_main_menu(self):
        """Emit signal to return to main menu."""
        self.back_to_menu_requested.emit()

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
            "Scan-Geschwindigkeit": "sidebar.input.scan_duration",
            "Normal:": "sidebar.input.scan_normal",
            "Einges.:": "sidebar.input.scan_disabled",
            "Zahlungsmethoden": "sidebar.input.payment_methods",
            "Bargeld:": "sidebar.input.payment_cash",
            "Karte:": "sidebar.input.payment_card",
            # Staff Tab
            "Kassierer Geschwindigkeit": "sidebar.input.cashier_speed",
            "Scan-Geschwindigkeit": "sidebar.input.cashier_speed",
            "Azubi:": "sidebar.input.cashier_newbie",
            "Profi:": "sidebar.input.cashier_pro",
            "Bezahldauer": "sidebar.input.payment_duration",
            "Bezahldauer (SB)": "sidebar.input.payment_duration_sb",
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
            "Grundriss": "sidebar.editor.background",
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
            "Normal": "sidebar.editor.checkout_normal",
            "SB": "sidebar.editor.checkout_sb",
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

    # ==========================================
    # INPUT BLOCKING METHODS
    # ==========================================
    def set_input_blocked(self, blocked, translator=None):
        """Enable/disable all input controls and show/hide warning message."""
        # If we are about to block input, ensure all input tabs are preloaded so
        # their layouts (spacing, group boxes) are properly initialized. This
        # prevents missing spacing for tabs that haven't been shown yet.
        if blocked and hasattr(self, "input_sub_tabs"):
            try:
                self.preload_all_input_tabs()
            except Exception:
                pass

        if blocked:
            # Show warning message
            if translator:
                title = translator.get(
                    "sidebar.input.input_blocked_title", "⚠️ Eingabe gesperrt"
                )
                message = translator.get(
                    "sidebar.input.input_blocked_message",
                    "Während der Simulation können die Eingabeparameter nicht geändert werden. Bitte setzen Sie die Simulation zurück.",
                )
                self.input_blocked_warning.setText(f"{title}\n{message}")
            else:
                self.input_blocked_warning.setText(
                    "⚠️ Eingabe gesperrt\nWährend der Simulation können die Eingabeparameter nicht geändert werden."
                )
            self.input_blocked_warning.setVisible(True)
        else:
            self.input_blocked_warning.setVisible(False)

        # Disable/enable all input widgets recursively
        self._set_widgets_enabled(self.input_sub_tabs, not blocked)

    def _set_widgets_enabled(self, widget, enabled):
        """Recursively enable/disable input widgets, but keep tabs clickable."""
        from PyQt6.QtWidgets import QTabWidget, QTabBar

        # Special handling for QTabWidget: only enable/disable the pages
        # (tab content widgets). Do NOT recurse into the QTabBar or its
        # internal children (scroll buttons) because toggling those can
        # cause the tab bar to show scroll arrows incorrectly.
        if isinstance(widget, QTabWidget):
            try:
                for i in range(widget.count()):
                    page = widget.widget(i)
                    if page:
                        self._set_widgets_enabled(page, enabled)
            except Exception:
                pass
            return

        # For the QTabBar itself, don't change anything — leave it alone.
        if isinstance(widget, QTabBar):
            return

        # Only call setEnabled if it's a QWidget
        if hasattr(widget, "setEnabled"):
            try:
                widget.setEnabled(enabled)
            except AttributeError:
                pass

        if hasattr(widget, "children"):
            for child in widget.children():
                if child:
                    self._set_widgets_enabled(child, enabled)

    def preload_all_input_tabs(self):
        """Preload all input tabs to ensure they are rendered and visible."""
        if hasattr(self, "input_sub_tabs"):
            current_index = self.input_sub_tabs.currentIndex()
            # Cycle through all tabs to force them to load
            for i in range(self.input_sub_tabs.count()):
                self.input_sub_tabs.setCurrentIndex(i)
            # Return to the original tab
            self.input_sub_tabs.setCurrentIndex(current_index)
