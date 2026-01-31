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
    QGridLayout,
    QProgressBar,
)
from PyQt6.QtCore import QTime, Qt, pyqtSignal
import random
from config import COLOR_ACCENT, COLOR_ERROR, COLOR_SUCCESS, COLOR_BG_PANEL
from .kpi_card import KPICard, LiveIndicator, MetricBox
from .stats_live_tab import StatsLiveTab
from .stats_details_tab import StatsDetailsTab
from .stats_log_tab import StatsLogTab
from .stats_updater import StatsUpdater


class Sidebar(QWidget):
    back_to_menu_requested = pyqtSignal()  # Signal to go back to main menu

    def __init__(self, parent=None, translator=None):
        super().__init__(parent)
        self.translator = translator
        self.widget_refs = {}  # Store references to all translatable widgets
        self.map_manager = None  # Will be set by controller
        self.visual_controller = None  # Will be set by controller
        self.controller = None  # Will be set by main_controller
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
        self.time_open = QTimeEdit(QTime(7, 0))
        self.time_close = QTimeEdit(QTime(20, 0))
        # Connect time changes to update displays immediately
        self.time_open.timeChanged.connect(self._on_time_changed)
        self.time_close.timeChanged.connect(self._on_time_changed)
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
        self.actor_count_input = self._create_spin(350, 1, 2000)
        self.disabled_prob_input = self._create_spin(8, 0, 100, " %")
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
            speed_walk, 1.8, 0.5, f_speed
        )
        self.speed_roll_mean, self.speed_roll_std = self._create_dist_row(
            speed_roll, 1.0, 0.3, f_speed
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
        self.items_mean = self._create_spin(12, 1, 100)
        self.items_std = self._create_spin(5, 0, 50)
        # Custom Row for Items
        h_it = QHBoxLayout()
        h_it.addWidget(QLabel("Ø:"))
        h_it.addWidget(self.items_mean)
        h_it.addWidget(QLabel("σ:"))
        h_it.addWidget(self.items_std)
        f_cart.addRow(cart_items, h_it)

        self.hand_scanner_prob = self._create_spin(35, 0, 100, " %")
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
            self._create_range_row(scan_normal, 1.8, 2.0, f_scan)
        )
        self.scan_speed_disabled_min, self.scan_speed_disabled_max = (
            self._create_range_row(scan_disabled, 2.5, 3.5, f_scan)
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
            self._create_range_row(cashier_newbie, 1.0, 2.5, f_cashier)
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
            self._create_range_row(conflict_duration, 5.0, 10.0, f_maint)
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
        self.checkout_fail_rate_normal = self._create_spin(10, 0, 100, " %")
        self.checkout_fail_rate_sb = self._create_spin(25, 0, 100, " %")
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
        self.customer_annoyance_rate = self._create_spin(30, 0, 100, " %")
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
    # TAB 2: STATISTIKEN (REDESIGNED WITH SUBTABS)
    # ==========================================
    def _init_tab_stats(self):
        """Initialize the statistics tab with modern card-based design and subtabs."""
        tab_stats_container = QWidget()
        l_stats_root = QVBoxLayout(tab_stats_container)
        l_stats_root.setContentsMargins(0, 5, 0, 0)
        
        # === HEADER: LIVE Indicator (always visible) ===
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 0, 10, 8)
        
        live_dashboard_title = (
            self.translator.get("sidebar.stats.live_dashboard")
            if self.translator
            else "LIVE-DASHBOARD"
        )
        
        title_label = QLabel(live_dashboard_title)
        title_label.setStyleSheet(
            "font-size: 13px; "
            "font-weight: 700; "
            "color: #374151; "
            "letter-spacing: 0.5px;"
        )
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        self.live_indicator = LiveIndicator()
        header_layout.addWidget(self.live_indicator)
        
        l_stats_root.addLayout(header_layout)
        
        # === SUBTABS ===
        self.stats_sub_tabs = QTabWidget()
        l_stats_root.addWidget(self.stats_sub_tabs)
        
        # Create statistics tab components
        self.stats_live_tab = StatsLiveTab(self, self.translator)
        self.stats_details_tab = StatsDetailsTab(self, self.translator)
        self.stats_log_tab = StatsLogTab(self, self.translator)
        
        # Create stats updater
        self.stats_updater = StatsUpdater(self.stats_live_tab, self.stats_details_tab, self.translator)
        
        # Add tabs
        live_tab_label = (
            self.translator.get("sidebar.stats.live_tab")
            if self.translator
            else "Live"
        )
        details_tab_label = (
            self.translator.get("sidebar.stats.details_tab")
            if self.translator
            else "Details"
        )
        log_tab_label = (
            self.translator.get("sidebar.stats.log_tab")
            if self.translator
            else "Protokoll"
        )
        
        self.stats_sub_tabs.addTab(self.stats_live_tab, live_tab_label)
        self.stats_sub_tabs.addTab(self.stats_details_tab, details_tab_label)
        self.stats_sub_tabs.addTab(self.stats_log_tab, log_tab_label)
        
        # Expose commonly accessed widgets for compatibility
        self._expose_stats_widgets()
        
        # Add main tab
        stats_tab = (
            self.translator.get("sidebar.tabs.stats")
            if self.translator
            else "Statistiken"
        )
        self.main_tabs.addTab(tab_stats_container, stats_tab)
    
    def _expose_stats_widgets(self):
        """Expose statistics widgets for backward compatibility."""
        # Live tab widgets
        self.lbl_customers_in_store = self.stats_live_tab.lbl_customers_in_store
        self.lbl_total_customers_served_live = self.stats_live_tab.lbl_total_customers_served_live
        self.lbl_throughput = self.stats_live_tab.lbl_throughput
        self.lbl_avg_wait = self.stats_live_tab.lbl_avg_wait
        self.lbl_wait_status = self.stats_live_tab.lbl_wait_status
        self.wait_progress = self.stats_live_tab.wait_progress
        self.lbl_queue_count = self.stats_live_tab.lbl_queue_count
        self.lbl_longest_queue = self.stats_live_tab.lbl_longest_queue
        self.lbl_checkouts_open = self.stats_live_tab.lbl_checkouts_open
        self.lbl_checkouts_malfunction = self.stats_live_tab.lbl_checkouts_malfunction
        self.lbl_checkouts_closed = self.stats_live_tab.lbl_checkouts_closed
        self.lbl_available_checkouts = self.stats_live_tab.lbl_available_checkouts
        self.lbl_satisfaction_score = self.stats_live_tab.lbl_satisfaction_score
        self.satisfaction_progress = self.stats_live_tab.satisfaction_progress
        self.lbl_satisfaction_status = self.stats_live_tab.lbl_satisfaction_status
        self.btn_open_report = self.stats_live_tab.btn_open_report
        
        # Details tab widgets
        self.lbl_total_items = self.stats_details_tab.lbl_total_items
        self.lbl_avg_items_per_customer = self.stats_details_tab.lbl_avg_items_per_customer
        self.lbl_total_customers = self.stats_details_tab.lbl_total_customers
        self.lbl_payment_cash = self.stats_details_tab.lbl_payment_cash
        self.lbl_payment_card = self.stats_details_tab.lbl_payment_card
        self.lbl_malfunctions = self.stats_details_tab.lbl_malfunctions
        self.lbl_annoyance = self.stats_details_tab.lbl_annoyance
        self.lbl_conflicts = self.stats_details_tab.lbl_conflicts
        self.lbl_elapsed_open = self.stats_details_tab.lbl_elapsed_open
        self.lbl_scheduled_open = self.stats_details_tab.lbl_scheduled_open
        self.lbl_overtime = self.stats_details_tab.lbl_overtime
        
        # Log tab widgets
        self.list_log = self.stats_log_tab.list_log
        self.plot_widget = self.stats_log_tab.plot_widget
        
        # Compatibility: Expose gb_stats (the first groupbox in live tab)
        if hasattr(self.stats_live_tab, 'gb_stats'):
            self.gb_stats = self.stats_live_tab.gb_stats
        else:
            # Create a dummy QGroupBox for compatibility
            self.gb_stats = QGroupBox("KUNDEN")
    
    def _setup_stats_live_tab(self):
        """Setup Live Overview subtab - most important metrics without scrolling."""
        tab_live = QWidget()
        l_live = QVBoxLayout(tab_live)
        l_live.setAlignment(Qt.AlignmentFlag.AlignTop)
        l_live.setSpacing(10)
        l_live.setContentsMargins(8, 8, 8, 8)

        # === KPI CARDS ===
        
        # Card style (reusable)
        card_style = """
            QGroupBox {
                font-size: 11px;
                font-weight: 700;
                color: #374151;
                border: 1px solid #D1D5DB;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 12px;
                background-color: #FFFFFF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 5px;
            }
        """
        
        # Card 1: KUNDEN
        card1_title = (
            self.translator.get("sidebar.stats.card_customers", "KUNDEN")
            if self.translator
            else "KUNDEN"
        )
        self.gb_stats = QGroupBox(card1_title)
        self.gb_stats.setStyleSheet(card_style)
        card1_layout = QVBoxLayout(self.gb_stats)
        card1_layout.setSpacing(10)
        
        # Im Laden
        store_row = QHBoxLayout()
        store_row.setSpacing(6)
        
        store_lbl = QLabel(
            self.translator.get("sidebar.stats.label_in_store", "Im Laden:")
            if self.translator
            else "Im Laden:"
        )
        store_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        store_row.addWidget(store_lbl)
        
        self.lbl_customers_in_store = QLabel("0")
        self.lbl_customers_in_store.setStyleSheet("font-size: 20px; color: #111827; font-weight: 700;")
        store_row.addWidget(self.lbl_customers_in_store)
        
        store_unit = QLabel(
            self.translator.get("sidebar.stats.unit_customers", "Kunden")
            if self.translator
            else "Kunden"
        )
        store_unit.setStyleSheet("font-size: 13px; color: #6B7280;")
        store_row.addWidget(store_unit)
        store_row.addStretch()
        card1_layout.addLayout(store_row)
        
        # Gesamt bedient
        total_row = QHBoxLayout()
        total_row.setSpacing(6)
        
        total_lbl = QLabel(
            self.translator.get("sidebar.stats.label_total_served", "Gesamt bedient:")
            if self.translator
            else "Gesamt bedient:"
        )
        total_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        total_row.addWidget(total_lbl)
        
        self.lbl_total_customers_served_live = QLabel("0")
        self.lbl_total_customers_served_live.setStyleSheet("font-size: 20px; color: #111827; font-weight: 700;")
        total_row.addWidget(self.lbl_total_customers_served_live)
        
        total_unit = QLabel(
            self.translator.get("sidebar.stats.unit_customers", "Kunden")
            if self.translator
            else "Kunden"
        )
        total_unit.setStyleSheet("font-size: 13px; color: #6B7280;")
        total_row.addWidget(total_unit)
        total_row.addStretch()
        card1_layout.addLayout(total_row)
        
        # Durchsatz
        throughput_row = QHBoxLayout()
        throughput_row.setSpacing(6)
        
        throughput_lbl = QLabel(
            self.translator.get("sidebar.stats.label_throughput", "Durchsatz:")
            if self.translator
            else "Durchsatz:"
        )
        throughput_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        throughput_row.addWidget(throughput_lbl)
        
        self.lbl_throughput = QLabel("0 K/h")
        self.lbl_throughput.setStyleSheet("font-size: 18px; color: #10B981; font-weight: 700;")
        throughput_row.addWidget(self.lbl_throughput)
        throughput_row.addStretch()
        card1_layout.addLayout(throughput_row)
        
        l_live.addWidget(self.gb_stats)
        
        # Card 2: Zufriedenheit
        card2_title = (
            self.translator.get("sidebar.stats.card_customer_satisfaction", "KUNDENZUFRIEDENHEIT")
            if self.translator
            else "KUNDENZUFRIEDENHEIT"
        )
        card2 = QGroupBox(card2_title)
        card2.setStyleSheet(card_style)
        card2_layout = QVBoxLayout(card2)
        card2_layout.setSpacing(10)
        
        wait_row = QHBoxLayout()
        wait_row.setSpacing(6)
        
        wait_lbl = QLabel(
            self.translator.get("sidebar.stats.label_avg_wait", "Ø Wartezeit:")
            if self.translator
            else "Ø Wartezeit:"
        )
        wait_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        wait_row.addWidget(wait_lbl)
        
        self.lbl_avg_wait = QLabel("0.0 min")
        self.lbl_avg_wait.setStyleSheet("font-size: 22px; color: #111827; font-weight: 700;")
        wait_row.addWidget(self.lbl_avg_wait)
        
        self.lbl_wait_status = QLabel("")
        self.lbl_wait_status.setStyleSheet("font-size: 22px;")
        wait_row.addWidget(self.lbl_wait_status)
        wait_row.addStretch()
        card2_layout.addLayout(wait_row)
        
        # Progress bar for wait time
        self.wait_progress = QProgressBar()
        self.wait_progress.setRange(0, 10)  # 0-10 minutes
        self.wait_progress.setValue(0)
        self.wait_progress.setTextVisible(False)
        self.wait_progress.setMaximumHeight(10)
        self.wait_progress.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 3px;
                background-color: #E5E7EB;
            }
            QProgressBar::chunk {
                background-color: #10B981;
                border-radius: 3px;
            }
        """)
        card2_layout.addWidget(self.wait_progress)
        
        # Warteschlange
        queue_row = QHBoxLayout()
        queue_row.setSpacing(6)
        
        queue_lbl = QLabel(
            self.translator.get("sidebar.stats.label_in_queue", "In Warteschlange:")
            if self.translator
            else "In Warteschlange:"
        )
        queue_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        queue_row.addWidget(queue_lbl)
        
        self.lbl_queue_count = QLabel("0")
        self.lbl_queue_count.setStyleSheet("font-size: 18px; color: #111827; font-weight: 700;")
        queue_row.addWidget(self.lbl_queue_count)
        
        queue_unit = QLabel("Kunden")
        queue_unit.setStyleSheet("font-size: 13px; color: #6B7280;")
        queue_row.addWidget(queue_unit)
        queue_row.addStretch()
        card2_layout.addLayout(queue_row)
        
        # Längste Queue
        longest_row = QHBoxLayout()
        longest_row.setSpacing(6)
        
        longest_lbl = QLabel(
            self.translator.get("sidebar.stats.label_longest_queue", "Längste Queue:")
            if self.translator
            else "Längste Queue:"
        )
        longest_lbl.setStyleSheet("font-size: 12px; color: #9CA3AF; font-weight: 600;")
        longest_row.addWidget(longest_lbl)
        
        self.lbl_longest_queue = QLabel("-")
        self.lbl_longest_queue.setStyleSheet("font-size: 12px; color: #6B7280; font-weight: 600;")
        longest_row.addWidget(self.lbl_longest_queue)
        longest_row.addStretch()
        card2_layout.addLayout(longest_row)
        
        l_live.addWidget(card2)
        
        # Card 3: Kassen-Status
        card3 = QGroupBox("� KASSEN-STATUS")
        card3.setStyleSheet(card_style)
        card3_layout = QVBoxLayout(card3)
        card3_layout.setSpacing(10)
        
        checkouts_grid = QGridLayout()
        checkouts_grid.setSpacing(8)
        
        open_lbl = QLabel(
            self.translator.get("sidebar.stats.label_open", "Offen:")
            if self.translator
            else "Offen:"
        )
        open_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        checkouts_grid.addWidget(open_lbl, 0, 0)
        
        self.lbl_checkouts_open = QLabel("0")
        self.lbl_checkouts_open.setStyleSheet("font-size: 18px; color: #10B981; font-weight: 700;")
        checkouts_grid.addWidget(self.lbl_checkouts_open, 0, 1)
        
        open_unit = QLabel(
            self.translator.get("sidebar.stats.unit_checkouts", "Kassen")
            if self.translator
            else "Kassen"
        )
        open_unit.setStyleSheet("font-size: 13px; color: #6B7280;")
        checkouts_grid.addWidget(open_unit, 0, 2)
        
        malfunction_lbl = QLabel(
            self.translator.get("sidebar.stats.label_malfunction", "Störung:")
            if self.translator
            else "Störung:"
        )
        malfunction_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        checkouts_grid.addWidget(malfunction_lbl, 1, 0)
        
        self.lbl_checkouts_malfunction = QLabel("0")
        self.lbl_checkouts_malfunction.setStyleSheet("font-size: 18px; color: #EF4444; font-weight: 700;")
        checkouts_grid.addWidget(self.lbl_checkouts_malfunction, 1, 1)
        
        malfunction_unit = QLabel(
            self.translator.get("sidebar.stats.unit_checkouts", "Kassen")
            if self.translator
            else "Kassen"
        )
        malfunction_unit.setStyleSheet("font-size: 13px; color: #6B7280;")
        checkouts_grid.addWidget(malfunction_unit, 1, 2)
        
        closed_lbl = QLabel(
            self.translator.get("sidebar.stats.label_closed", "Geschlossen:")
            if self.translator
            else "Geschlossen:"
        )
        closed_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        checkouts_grid.addWidget(closed_lbl, 2, 0)
        
        self.lbl_checkouts_closed = QLabel("0")
        self.lbl_checkouts_closed.setStyleSheet("font-size: 18px; color: #9CA3AF; font-weight: 700;")
        checkouts_grid.addWidget(self.lbl_checkouts_closed, 2, 1)
        
        closed_unit = QLabel(
            self.translator.get("sidebar.stats.unit_checkouts", "Kassen")
            if self.translator
            else "Kassen"
        )
        closed_unit.setStyleSheet("font-size: 13px; color: #6B7280;")
        checkouts_grid.addWidget(closed_unit, 2, 2)
        
        card3_layout.addLayout(checkouts_grid)
        
        # Store original label for compatibility
        self.lbl_available_checkouts = QLabel("0/0")
        
        l_live.addWidget(card3)
        
        # Card 4: Zufriedenheit (Satisfaction Score)
        card4_title = (
            self.translator.get("sidebar.stats.card_satisfaction_score", "ZUFRIEDENHEITSSCORE")
            if self.translator
            else "ZUFRIEDENHEITSSCORE"
        )
        card4 = QGroupBox(card4_title)
        card4.setStyleSheet(card_style)
        card4_layout = QVBoxLayout(card4)
        card4_layout.setSpacing(10)
        
        satisfaction_value_layout = QHBoxLayout()
        
        self.lbl_satisfaction_score = QLabel("0%")
        self.lbl_satisfaction_score.setStyleSheet("font-size: 32px; color: #111827; font-weight: 700;")
        satisfaction_value_layout.addWidget(self.lbl_satisfaction_score)
        satisfaction_value_layout.addStretch()
        
        card4_layout.addLayout(satisfaction_value_layout)
        
        # Progress bar for satisfaction
        self.satisfaction_progress = QProgressBar()
        self.satisfaction_progress.setRange(0, 100)
        self.satisfaction_progress.setValue(0)
        self.satisfaction_progress.setTextVisible(False)
        self.satisfaction_progress.setMaximumHeight(12)
        self.satisfaction_progress.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 5px;
                background-color: #E5E7EB;
            }
            QProgressBar::chunk {
                background-color: #10B981;
                border-radius: 5px;
            }
        """)
        card4_layout.addWidget(self.satisfaction_progress)
        
        status_text = (
            f"{self.translator.get('sidebar.stats.status_prefix', 'Status:')} {self.translator.get('sidebar.stats.status_good', 'GUT')}"
            if self.translator
            else "Status: GUT"
        )
        self.lbl_satisfaction_status = QLabel(status_text)
        self.lbl_satisfaction_status.setStyleSheet("font-size: 13px; color: #10B981; font-weight: 700; text-align: center;")
        self.lbl_satisfaction_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card4_layout.addWidget(self.lbl_satisfaction_status)
        
        l_live.addWidget(card4)
        
        l_live.addStretch()
        
        # === REPORT BUTTON (at bottom) ===
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
        
        self.btn_open_report = QPushButton(report_button_label)
        self.btn_open_report.setProperty("class", "HeaderBtn")
        self.btn_open_report.setToolTip(report_button_tooltip)
        self.btn_open_report.setFixedHeight(44)
        l_live.addWidget(self.btn_open_report)
        
        live_tab_label = (
            self.translator.get("sidebar.stats.live_tab")
            if self.translator
            else "Live"
        )
        self.stats_sub_tabs.addTab(tab_live, live_tab_label)
    
    # === OLD METHODS REMOVED - Now using separate component files ===
    # _setup_stats_live_tab, _setup_stats_details_tab, _setup_stats_log_tab
    # have been refactored into:
    # - stats_live_tab.py (StatsLiveTab)
    # - stats_details_tab.py (StatsDetailsTab)
    # - stats_log_tab.py (StatsLogTab)
    # - stats_updater.py (StatsUpdater)
    
    def _setup_stats_details_tab(self):
        """Setup Details subtab - additional metrics and insights."""
        tab_details = QWidget()
        l_details = QVBoxLayout(tab_details)
        l_details.setAlignment(Qt.AlignmentFlag.AlignTop)
        l_details.setSpacing(10)
        l_details.setContentsMargins(8, 8, 8, 8)
        
        card_style = """
            QGroupBox {
                font-size: 11px;
                font-weight: 700;
                color: #374151;
                border: 1px solid #D1D5DB;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 12px;
                background-color: #FFFFFF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 5px;
            }
        """
        
        # === KUNDEN-BEREICH ===
        
        # Card 1: Artikel-Statistiken
        card_items_title = (
            self.translator.get("sidebar.stats.card_item_stats", "ARTIKEL-STATISTIKEN")
            if self.translator
            else "ARTIKEL-STATISTIKEN"
        )
        card_items = QGroupBox(card_items_title)
        card_items.setStyleSheet(card_style)
        card_items_layout = QVBoxLayout(card_items)
        card_items_layout.setSpacing(10)
        
        items_grid = QFormLayout()
        items_grid.setSpacing(8)
        
        total_items_lbl = QLabel(
            self.translator.get("sidebar.stats.total_items")
            if self.translator
            else "Artikel Gesamt:"
        )
        total_items_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        self.lbl_total_items = QLabel("0")
        self.lbl_total_items.setStyleSheet("font-size: 18px; color: #374151; font-weight: 700;")
        items_grid.addRow(total_items_lbl, self.lbl_total_items)
        
        avg_items_lbl = QLabel(
            self.translator.get("sidebar.stats.avg_items_per_customer")
            if self.translator
            else "Ø Artikel/Kunde:"
        )
        avg_items_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        self.lbl_avg_items_per_customer = QLabel("0.0")
        self.lbl_avg_items_per_customer.setStyleSheet("font-size: 18px; color: #374151; font-weight: 700;")
        items_grid.addRow(avg_items_lbl, self.lbl_avg_items_per_customer)
        
        card_items_layout.addLayout(items_grid)
        l_details.addWidget(card_items)
        
        # Card 2: Heute Bedient
        card_customers_title = (
            self.translator.get("sidebar.stats.card_served_today", "HEUTE BEDIENT")
            if self.translator
            else "HEUTE BEDIENT"
        )
        card_customers = QGroupBox(card_customers_title)
        card_customers.setStyleSheet(card_style)
        card_customers_layout = QVBoxLayout(card_customers)
        card_customers_layout.setSpacing(8)
        
        self.lbl_total_customers = QLabel("0")
        self.lbl_total_customers.setStyleSheet("font-size: 36px; color: #111827; font-weight: 700; text-align: center;")
        self.lbl_total_customers.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_customers_layout.addWidget(self.lbl_total_customers)
        
        customers_label = QLabel(
            self.translator.get("sidebar.stats.unit_customers", "Kunden")
            if self.translator
            else "Kunden"
        )
        customers_label.setStyleSheet("font-size: 13px; color: #6B7280; text-align: center;")
        customers_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_customers_layout.addWidget(customers_label)
        
        l_details.addWidget(card_customers)
        
        # === KASSEN-BEREICH ===
        
        # Card 3: Zahlungsmethoden
        card_payment_title = (
            self.translator.get("sidebar.stats.card_payment_methods", "ZAHLUNGSMETHODEN")
            if self.translator
            else "ZAHLUNGSMETHODEN"
        )
        card_payment = QGroupBox(card_payment_title)
        card_payment.setStyleSheet(card_style)
        card_payment_layout = QVBoxLayout(card_payment)
        card_payment_layout.setSpacing(10)
        
        payment_grid = QFormLayout()
        payment_grid.setSpacing(8)
        
        cash_lbl = QLabel(
            self.translator.get("sidebar.stats.cash_percent")
            if self.translator
            else "Bar:"
        )
        cash_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        self.lbl_payment_cash = QLabel("0%")
        self.lbl_payment_cash.setStyleSheet("font-size: 18px; color: #374151; font-weight: 700;")
        payment_grid.addRow(cash_lbl, self.lbl_payment_cash)
        
        card_lbl = QLabel(
            self.translator.get("sidebar.stats.card_percent")
            if self.translator
            else "Karte:"
        )
        card_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        self.lbl_payment_card = QLabel("0%")
        self.lbl_payment_card.setStyleSheet("font-size: 18px; color: #374151; font-weight: 700;")
        payment_grid.addRow(card_lbl, self.lbl_payment_card)
        
        card_payment_layout.addLayout(payment_grid)
        l_details.addWidget(card_payment)
        
        # Card 4: Kassen-Probleme
        card_issues_title = (
            self.translator.get("sidebar.stats.card_checkout_issues", "KASSEN-PROBLEME")
            if self.translator
            else "KASSEN-PROBLEME"
        )
        card_issues = QGroupBox(card_issues_title)
        card_issues.setStyleSheet(card_style)
        card_issues_layout = QVBoxLayout(card_issues)
        card_issues_layout.setSpacing(10)
        
        issues_grid = QFormLayout()
        issues_grid.setSpacing(8)
        
        malfunctions_lbl = QLabel(
            self.translator.get("sidebar.stats.malfunctions_today")
            if self.translator
            else "Störungen:"
        )
        malfunctions_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        self.lbl_malfunctions = QLabel("0")
        self.lbl_malfunctions.setStyleSheet("font-size: 18px; color: #EF4444; font-weight: 700;")
        issues_grid.addRow(malfunctions_lbl, self.lbl_malfunctions)
        
        annoyance_lbl = QLabel(
            self.translator.get("sidebar.stats.label_annoyance", "Verärgerungen:")
            if self.translator
            else "Verärgerungen:"
        )
        annoyance_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        self.lbl_annoyance = QLabel("0")
        self.lbl_annoyance.setStyleSheet("font-size: 18px; color: #F59E0B; font-weight: 700;")
        issues_grid.addRow(annoyance_lbl, self.lbl_annoyance)
        
        conflicts_lbl = QLabel(
            self.translator.get("sidebar.stats.conflicts_today")
            if self.translator
            else "Konflikte:"
        )
        conflicts_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        self.lbl_conflicts = QLabel("0")
        self.lbl_conflicts.setStyleSheet("font-size: 18px; color: #DC2626; font-weight: 700;")
        issues_grid.addRow(conflicts_lbl, self.lbl_conflicts)
        
        card_issues_layout.addLayout(issues_grid)
        l_details.addWidget(card_issues)
        
        # === ALLGEMEIN ===
        
        # Card 5: Öffnungszeiten
        card_time_title = (
            self.translator.get("sidebar.stats.card_opening_hours", "ÖFFNUNGSZEITEN")
            if self.translator
            else "ÖFFNUNGSZEITEN"
        )
        card_time = QGroupBox(card_time_title)
        card_time.setStyleSheet(card_style)
        card_time_layout = QVBoxLayout(card_time)
        card_time_layout.setSpacing(10)
        
        time_grid = QFormLayout()
        time_grid.setSpacing(8)
        
        elapsed_lbl = QLabel(
            self.translator.get("sidebar.stats.label_elapsed", "Verstrichen:")
            if self.translator
            else "Verstrichen:"
        )
        elapsed_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        self.lbl_elapsed_open = QLabel("0:00")
        self.lbl_elapsed_open.setStyleSheet("font-size: 16px; color: #374151; font-weight: 600;")
        time_grid.addRow(elapsed_lbl, self.lbl_elapsed_open)
        
        scheduled_lbl = QLabel(
            self.translator.get("sidebar.stats.label_scheduled", "Geplant:")
            if self.translator
            else "Geplant:"
        )
        scheduled_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        self.lbl_scheduled_open = QLabel("0:00")
        self.lbl_scheduled_open.setStyleSheet("font-size: 16px; color: #374151; font-weight: 600;")
        time_grid.addRow(scheduled_lbl, self.lbl_scheduled_open)
        
        overtime_lbl = QLabel(
            self.translator.get("sidebar.stats.label_overtime", "Überzeit:")
            if self.translator
            else "Überzeit:"
        )
        overtime_lbl.setStyleSheet("font-size: 13px; color: #F59E0B; font-weight: 600;")
        self.lbl_overtime = QLabel("+0:00")
        self.lbl_overtime.setStyleSheet("font-size: 16px; color: #F59E0B; font-weight: 700;")
        time_grid.addRow(overtime_lbl, self.lbl_overtime)
        
        card_time_layout.addLayout(time_grid)
        l_details.addWidget(card_time)
        
        l_details.addStretch()
        
        details_tab_label = (
            self.translator.get("sidebar.stats.details_tab")
            if self.translator
            else "Details"
        )
        self.stats_sub_tabs.addTab(tab_details, details_tab_label)
    
    def _setup_stats_log_tab(self):
        """Setup Log subtab - event protocol."""
        tab_log = QWidget()
        l_log_root = QVBoxLayout(tab_log)
        l_log_root.setContentsMargins(8, 8, 8, 8)
        
        event_log_title = (
            self.translator.get("sidebar.stats.event_log")
            if self.translator
            else "Ereignis-Protokoll"
        )
        
        # === EVENT LOG ===
        gb_log = QGroupBox(event_log_title)
        gb_log.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: 700;
                color: #374151;
                border: 1px solid #D1D5DB;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 12px;
                background-color: #FFFFFF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 5px;
            }
        """)
        l_log_inner = QVBoxLayout(gb_log)
        self.list_log = QListWidget()
        self.list_log.setStyleSheet("""
            QListWidget {
                background-color: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                font-size: 10px;
                padding: 4px;
            }
        """)
        l_log_inner.addWidget(self.list_log)
        l_log_root.addWidget(gb_log)

        self.plot_widget = None
        
        log_tab_label = (
            self.translator.get("sidebar.stats.log_tab")
            if self.translator
            else "Protokoll"
        )
        self.stats_sub_tabs.addTab(tab_log, log_tab_label)

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

        # Checkouts - randomize configurations
        if self.map_manager is not None and hasattr(self.map_manager, "checkouts_data"):
            for checkout in self.map_manager.checkouts_data:
                # Randomize open/closed
                checkout["open"] = random.choice([True, False])
                # Randomize max queue length (1-5)
                checkout["max_queue"] = random.randint(1, 5)
                # Randomize skill only for Normal checkouts
                if checkout.get("type") == "Normal":
                    checkout["skill"] = random.choice(["Pro", "Azubi"])
            
            # Redraw map to reflect changes
            if self.visual_controller is not None:
                self.visual_controller.draw_map_elements(self.map_manager)

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
        
        # Also disable/enable the random button
        if hasattr(self, "btn_randomize"):
            self.btn_randomize.setEnabled(not blocked)

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

    def _on_time_changed(self):
        """Called when time_open or time_close is changed. Updates clock widget and statistics displays."""
        # Use direct controller reference
        if self.controller is None:
            return
            
        # Get current time values
        open_time = self.time_open.time()
        close_time = self.time_close.time()
        
        # Only update if simulation not initialized (to avoid conflicts with running sim)
        if self.controller.sim_manager.is_initialized:
            return
        
        # Update toolbar clock widget
        if hasattr(self.controller.view, "clock_widget"):
            # Show opening time in clock
            self.controller.view.clock_widget.setText(open_time.toString("HH:mm"))
        
        # Calculate new scheduled open time string
        open_secs = open_time.hour() * 3600 + open_time.minute() * 60
        close_secs = close_time.hour() * 3600 + close_time.minute() * 60
        scheduled_open_secs = close_secs - open_secs
        if scheduled_open_secs < 0:
            scheduled_open_secs += 24 * 3600  # Handle overnight
        
        scheduled_hours = int(scheduled_open_secs // 3600)
        scheduled_mins = int((scheduled_open_secs % 3600) // 60)
        scheduled_formatted = f"{scheduled_hours}:{scheduled_mins:02d}"
        
        # Update live stats display
        if hasattr(self, "stats_live_tab"):
            if hasattr(self.stats_live_tab, "lbl_elapsed_time"):
                self.stats_live_tab.lbl_elapsed_time.setText("0:00")
            if hasattr(self.stats_live_tab, "lbl_scheduled_time"):
                self.stats_live_tab.lbl_scheduled_time.setText(scheduled_formatted)
