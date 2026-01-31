"""
Customer Analysis Tab - Detailed customer metrics and breakdowns with subtabs.
Provides comprehensive customer statistics with visual distributions and time metrics.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractScrollArea,
    QSizePolicy,
    QFormLayout,
    QTabWidget,
)
from PyQt6.QtCore import Qt, QTime
from PyQt6.QtGui import QFont

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    HAS_MATPLOTLIB = True
except Exception:
    FigureCanvas = None
    Figure = None
    HAS_MATPLOTLIB = False


class CustomerAnalysisTab(QWidget):
    """
    Customer Analysis Tab with subtabs:
    - Übersicht: Summary and pie charts
    - Zeitmetriken: Detailed time analysis
    - Kundenliste: Full customer list table
    """
    
    def __init__(self, translator=None, parent=None):
        super().__init__(parent)
        self.translator = translator
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI layout with subtabs."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Create subtab widget
        self.subtabs = QTabWidget()
        self.subtabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                background-color: #FFFFFF;
            }
            QTabBar::tab {
                background-color: #F1F5F9;
                color: #475569;
                border: 1px solid #CBD5E1;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 16px;
                margin-right: 2px;
                font-weight: 600;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                color: #1E293B;
            }
            QTabBar::tab:hover {
                background-color: #E2E8F0;
            }
        """)
        
        # Create subtabs
        self.overview_tab = self._create_overview_tab()
        self.metrics_tab = self._create_metrics_tab()
        self.list_tab = self._create_list_tab()
        
        self.subtabs.addTab(self.overview_tab, self._t("stats.subtab_overview", "Übersicht"))
        self.subtabs.addTab(self.metrics_tab, self._t("stats.subtab_times", "Zeitmetriken"))
        self.subtabs.addTab(self.list_tab, self._t("stats.subtab_list", "Kundenliste"))
        
        layout.addWidget(self.subtabs)
    
    def _create_overview_tab(self):
        """Create overview subtab with summary and pie charts."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Summary box
        summary_box = self._create_summary_box()
        layout.addWidget(summary_box)
        
        # Pie charts in horizontal layout
        if HAS_MATPLOTLIB:
            charts_layout = QHBoxLayout()
            charts_layout.setSpacing(16)
            
            # Customer Types Chart
            customer_types_box = QGroupBox(self._t("stats.customer_types_chart_title", "Kundentypen"))
            customer_types_box.setStyleSheet("""
                QGroupBox {
                    font-size: 14px;
                    font-weight: 600;
                    color: #1E293B;
                    border: 2px solid #CBD5E1;
                    border-radius: 8px;
                    margin-top: 12px;
                    padding-top: 16px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 12px;
                    padding: 0 8px;
                }
            """)
            ct_layout = QVBoxLayout(customer_types_box)
            ct_layout.setContentsMargins(12, 12, 12, 12)
            
            self.dist_figure = Figure(figsize=(6, 5))
            self.dist_canvas = FigureCanvas(self.dist_figure)
            self.ax_customer_types = self.dist_figure.add_subplot(1, 1, 1)
            self.dist_figure.subplots_adjust(left=0.05, right=0.95, top=0.85, bottom=0.05)
            ct_layout.addWidget(self.dist_canvas)
            charts_layout.addWidget(customer_types_box, 1)
            
            # Payment Methods Chart
            payment_methods_box = QGroupBox(self._t("stats.payment_methods_chart_title", "Bezahlmethoden"))
            payment_methods_box.setStyleSheet("""
                QGroupBox {
                    font-size: 14px;
                    font-weight: 600;
                    color: #1E293B;
                    border: 2px solid #CBD5E1;
                    border-radius: 8px;
                    margin-top: 12px;
                    padding-top: 16px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 12px;
                    padding: 0 8px;
                }
            """)
            pm_layout = QVBoxLayout(payment_methods_box)
            pm_layout.setContentsMargins(12, 12, 12, 12)
            
            self.payment_figure = Figure(figsize=(6, 5))
            self.payment_canvas = FigureCanvas(self.payment_figure)
            self.ax_payment_methods = self.payment_figure.add_subplot(1, 1, 1)
            self.payment_figure.subplots_adjust(left=0.05, right=0.95, top=0.85, bottom=0.05)
            pm_layout.addWidget(self.payment_canvas)
            charts_layout.addWidget(payment_methods_box, 1)
            
            layout.addLayout(charts_layout)
        
        layout.addStretch()
        return tab
    
    def _create_summary_box(self):
        """Create summary metrics box."""
        gb = QGroupBox(self._t("stats.customer_summary_title", "Zusammenfassung"))
        gb.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: 600;
                color: #1E293B;
                border: 2px solid #CBD5E1;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """)
        
        layout = QFormLayout(gb)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        
        self.lbl_total_customers = QLabel("0")
        self.lbl_total_customers.setStyleSheet("font-size: 18px; font-weight: 700; color: #1E293B;")
        
        self.lbl_normal_customers = QLabel("0")
        self.lbl_normal_customers.setStyleSheet("font-size: 14px; font-weight: 600; color: #475569;")
        
        self.lbl_disabled_customers = QLabel("0")
        self.lbl_disabled_customers.setStyleSheet("font-size: 14px; font-weight: 600; color: #475569;")
        
        self.lbl_handheld_customers = QLabel("0")
        self.lbl_handheld_customers.setStyleSheet("font-size: 14px; font-weight: 600; color: #475569;")
        
        layout.addRow(self._styled_label(self._t("stats.total_customers", "Kunden Gesamt:")), self.lbl_total_customers)
        layout.addRow(self._styled_label(self._t("stats.normal_customers", "Normal:")), self.lbl_normal_customers)
        layout.addRow(self._styled_label(self._t("stats.disabled_customers", "Eingeschränkt:")), self.lbl_disabled_customers)
        layout.addRow(self._styled_label(self._t("stats.handheld_customers", "Mit Handscanner:")), self.lbl_handheld_customers)
        
        # Add without handheld label
        self.lbl_without_handheld = QLabel("0")
        self.lbl_without_handheld.setStyleSheet("font-size: 14px; font-weight: 600; color: #475569;")
        layout.addRow(self._styled_label(self._t("stats.without_handheld", "Ohne Scanner:")), self.lbl_without_handheld)
        
        return gb
    
    def _create_metrics_tab(self):
        """Create time metrics subtab with larger visualizations."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Three metric boxes in vertical layout, full width
        self.box_store_stay = self._create_metric_box(
            self._t("stats.store_stay_label", "Verweildauer im Laden")
        )
        layout.addWidget(self.box_store_stay)
        
        self.box_queue_wait = self._create_metric_box(
            self._t("stats.queue_wait_label", "Wartezeit in der Warteschlange")
        )
        layout.addWidget(self.box_queue_wait)
        
        self.box_service_time = self._create_metric_box(
            self._t("stats.service_time_label", "Servicezeit an der Kasse")
        )
        layout.addWidget(self.box_service_time)
        return tab
    
    def _create_list_tab(self):
        """Create customer list subtab with full-width table."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Info label
        info = QLabel(self._t(
            "stats.customer_list_desc",
            "Alle Kunden mit Zeiten, Zahlung und Kasse."
        ))
        info.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 500; padding: 4px 0;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Table
        self.customer_table = QTableWidget()
        self.customer_table.setColumnCount(10)
        self.customer_table.setHorizontalHeaderLabels([
            self._t("stats.customer_id", "ID"),
            self._t("stats.customer_type", "Typ"),
            self._t("stats.customer_handheld", "Scanner"),
            self._t("stats.customer_payment", "Zahlung"),
            self._t("stats.customer_items", "Artikel"),
            self._t("stats.customer_checkout", "Kasse"),
            self._t("stats.customer_entry", "Eintritt"),
            self._t("stats.customer_exit", "Verlassen"),
            self._t("stats.customer_total_time", "Gesamt (min)"),
            self._t("stats.customer_wait_time", "Warten (min)"),
        ])
        
        self._style_table(self.customer_table)
        layout.addWidget(self.customer_table)
        
        return tab
    
    def _create_metric_box(self, title):
        """Create a metric box with Min/Avg/Max display."""
        box = QGroupBox(title)
        box.setStyleSheet("""
            QGroupBox {
                font-size: 15px;
                font-weight: 600;
                color: #1E293B;
                border: 2px solid #CBD5E1;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
                background-color: #F8FAFC;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """)
        
        layout = QHBoxLayout(box)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(32)
        
        # Three columns: Min, Avg, Max with larger fonts
        for label_text in ["Min", "Ø", "Max"]:
            col_layout = QVBoxLayout()
            col_layout.setSpacing(8)
            
            label = QLabel(label_text)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-size: 14px; color: #64748B; font-weight: 700; text-transform: uppercase;")
            col_layout.addWidget(label)
            
            value = QLabel("0.0")
            value.setAlignment(Qt.AlignmentFlag.AlignCenter)
            value.setStyleSheet("font-size: 28px; color: #1E293B; font-weight: 700;")
            value.setObjectName(f"val_{label_text.replace('Ø', 'avg')}")
            col_layout.addWidget(value)
            
            unit = QLabel(self._t("stats.unit_minutes", "Minuten"))
            unit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            unit.setStyleSheet("font-size: 12px; color: #94A3B8; font-weight: 500;")
            col_layout.addWidget(unit)
            
            layout.addLayout(col_layout)
        
        return box
    
    def update_distributions(self, stats):
        """Update customer distribution charts and labels."""
        global_stats = stats.get("global", {})
        
        # Update labels
        total = global_stats.get("total_customers_spawned", 0)
        normal = global_stats.get("total_normal_customers", 0)
        disabled = global_stats.get("total_disabled_customers", 0)
        handheld = global_stats.get("total_handheld_customers", 0)
        
        self.lbl_total_customers.setText(str(total))
        self.lbl_normal_customers.setText(f"{normal} ({normal/total*100 if total > 0 else 0:.0f}%)")
        self.lbl_disabled_customers.setText(f"{disabled} ({disabled/total*100 if total > 0 else 0:.0f}%)")
        without_handheld = total - handheld
        self.lbl_handheld_customers.setText(f"{handheld} ({handheld/total*100 if total > 0 else 0:.0f}%)")
        self.lbl_without_handheld.setText(f"{without_handheld} ({without_handheld/total*100 if total > 0 else 0:.0f}%)")
        
        # Update pie charts
        if HAS_MATPLOTLIB:
            self._update_customer_types_pie(normal, disabled)
            self._update_payment_methods_pie(global_stats)
    
    def _update_customer_types_pie(self, normal, disabled):
        """Update customer types pie chart."""
        self.ax_customer_types.clear()
        
        if normal + disabled > 0:
            colors = ['#60A5FA', '#F97316']
            wedges, texts, autotexts = self.ax_customer_types.pie(
                [normal, disabled],
                labels=[
                    self._t("stats.chart_normal", "Normal"),
                    self._t("stats.chart_disabled", "Eingeschränkt")
                ],
                autopct='%1.1f%%',
                colors=colors,
                startangle=90,
                textprops={'fontsize': 11, 'weight': 'bold'}
            )
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(12)
                autotext.set_weight('bold')
        else:
            self._show_no_data(self.ax_customer_types)
        
        self.ax_customer_types.set_title(
            self._t("stats.customer_types_chart_title", "Kundentypen"),
            fontsize=14, fontweight='bold', color='#1E293B', pad=12
        )
        
        if hasattr(self, "dist_canvas"):
            self.dist_canvas.draw_idle()
    
    def _update_payment_methods_pie(self, global_stats):
        """Update payment methods pie chart."""
        self.ax_payment_methods.clear()
        
        payment = global_stats.get("payment", {})
        cash = payment.get("cash_count", 0)
        card = payment.get("card_count", 0)
        
        if cash + card > 0:
            colors = ['#10B981', '#3B82F6']
            wedges, texts, autotexts = self.ax_payment_methods.pie(
                [cash, card],
                labels=[
                    self._t("stats.chart_cash", "Bar"),
                    self._t("stats.chart_card", "Karte")
                ],
                autopct='%1.1f%%',
                colors=colors,
                startangle=90,
                textprops={'fontsize': 11, 'weight': 'bold'}
            )
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(12)
                autotext.set_weight('bold')
        else:
            self._show_no_data(self.ax_payment_methods)
        
        self.ax_payment_methods.set_title(
            self._t("stats.payment_methods_chart_title", "Bezahlmethoden"),
            fontsize=14, fontweight='bold', color='#1E293B', pad=12
        )
        
        if hasattr(self, "payment_canvas"):
            self.payment_canvas.draw_idle()
    
    def update_time_metrics(self, stats):
        """Update time metrics boxes."""
        global_stats = stats.get("global", {})
        times = global_stats.get("times", {})
        
        # Check if we have any data (customers served)
        total_customers = global_stats.get("total_customers_served", 0)
        if total_customers == 0:
            # No data yet - show "Keine Daten"
            self._update_metric_box_no_data(self.box_store_stay)
            self._update_metric_box_no_data(self.box_queue_wait)
            self._update_metric_box_no_data(self.box_service_time)
            return
        
        # Store Stay metrics
        self._update_metric_box(
            self.box_store_stay,
            times.get("store_stay_min", 0.0) / 60.0,
            times.get("store_stay_avg", 0.0) / 60.0,
            times.get("store_stay_max", 0.0) / 60.0
        )
        
        # Queue Wait metrics
        self._update_metric_box(
            self.box_queue_wait,
            times.get("queue_wait_min", 0.0) / 60.0,
            times.get("queue_wait_avg", 0.0) / 60.0,
            times.get("queue_wait_max", 0.0) / 60.0
        )
        
        # Service Time metrics
        self._update_metric_box(
            self.box_service_time,
            times.get("service_time_min", 0.0) / 60.0,
            times.get("service_time_avg", 0.0) / 60.0,
            times.get("service_time_max", 0.0) / 60.0
        )
    
    def _update_metric_box(self, box, min_val, avg_val, max_val):
        """Update a metric box with new values."""
        min_label = box.findChild(QLabel, "val_Min")
        avg_label = box.findChild(QLabel, "val_avg")
        max_label = box.findChild(QLabel, "val_Max")
        
        if min_label:
            min_label.setText(f"{min_val:.1f}")
        if avg_label:
            avg_label.setText(f"{avg_val:.1f}")
        if max_label:
            max_label.setText(f"{max_val:.1f}")
    
    def _update_metric_box_no_data(self, box):
        """Update a metric box to show 'Keine Daten'."""
        min_label = box.findChild(QLabel, "val_Min")
        avg_label = box.findChild(QLabel, "val_avg")
        max_label = box.findChild(QLabel, "val_Max")
        
        no_data_text = "–"
        if min_label:
            min_label.setText(no_data_text)
        if avg_label:
            avg_label.setText(no_data_text)
        if max_label:
            max_label.setText(no_data_text)
    
    def update_customer_list(self, stats):
        """Update the detailed customer list table."""
        customers = stats.get("customers", {}).get("list", [])
        open_time = stats.get("global", {}).get("open_time", "00:00")
        
        # Disable sorting while updating
        was_sorting = self.customer_table.isSortingEnabled()
        self.customer_table.setSortingEnabled(False)
        
        self.customer_table.setRowCount(len(customers))
        
        for row, cust in enumerate(customers):
            # ID
            self.customer_table.setItem(row, 0, self._make_item(cust.get("id", "-"), numeric=True))
            
            # Type
            cust_type = self._t("stats.type_disabled", "Eingeschränkt") if cust.get("type") == "disabled" else self._t("stats.type_normal", "Normal")
            self.customer_table.setItem(row, 1, self._make_item(cust_type))
            
            # Handheld Scanner
            has_scanner = self._t("stats.yes", "Ja") if cust.get("handheld") else self._t("stats.no", "Nein")
            self.customer_table.setItem(row, 2, self._make_item(has_scanner))
            
            # Payment Method
            payment = self._t("stats.cash", "Bar") if cust.get("payment_method") == "cash" else self._t("stats.card", "Karte")
            self.customer_table.setItem(row, 3, self._make_item(payment))
            
            # Items
            self.customer_table.setItem(row, 4, self._make_item(cust.get("items", 0), numeric=True))
            
            # Checkout ID
            self.customer_table.setItem(row, 5, self._make_item(cust.get("checkout_id", "-"), numeric=True))
            
            # Entry Time
            entry_time = self._format_time_from_open(cust.get("entry_time_sec"), open_time)
            self.customer_table.setItem(row, 6, self._make_item(entry_time))
            
            # Exit Time
            exit_time = self._format_time_from_open(cust.get("exit_time_sec"), open_time)
            self.customer_table.setItem(row, 7, self._make_item(exit_time))
            
            # Total Time (Store Stay)
            total_min = (cust.get("store_stay_sec") or 0.0) / 60.0
            self.customer_table.setItem(row, 8, self._make_item(f"{total_min:.2f}", numeric=True))
            
            # Wait Time (Queue)
            wait_min = (cust.get("queue_wait_sec") or 0.0) / 60.0
            self.customer_table.setItem(row, 9, self._make_item(f"{wait_min:.2f}", numeric=True))
        
        # Re-enable sorting
        self.customer_table.setSortingEnabled(was_sorting)
    
    def _style_table(self, table):
        """Apply consistent table styling."""
        table.setAlternatingRowColors(True)
        table.setStyleSheet("""
            QTableWidget {
                background-color: #F8FAFC;
                color: #1E293B;
                gridline-color: #CBD5E1;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #E2E8F0;
                color: #1E293B;
                padding: 8px;
                border: 1px solid #CBD5E1;
                font-weight: 600;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QTableWidget::item:alternate {
                background-color: #FFFFFF;
            }
            QTableWidget::item:selected {
                background-color: #DBEAFE;
                color: #1E293B;
            }
        """)
        
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSortIndicatorShown(False)
        table.setSortingEnabled(False)
        table.verticalHeader().setVisible(False)
        table.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    
    def _make_item(self, value, numeric=False):
        """Create a table widget item with proper data type for sorting."""
        item = QTableWidgetItem(str(value))
        if numeric:
            try:
                # Store numeric value for proper sorting
                numeric_value = float(value)
                item.setData(Qt.ItemDataRole.DisplayRole, str(value))
                item.setData(Qt.ItemDataRole.UserRole, numeric_value)
            except (ValueError, TypeError):
                pass
        item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        return item
    
    def _format_time_from_open(self, seconds, open_time_str):
        """Format seconds since opening as HH:MM time."""
        if seconds is None:
            return "-"
        base = QTime.fromString(open_time_str or "00:00", "HH:mm")
        if base.isValid():
            return base.addSecs(int(seconds)).toString("HH:mm")
        return "-"
    
    def _show_no_data(self, ax):
        """Show 'no data' message on axis."""
        ax.text(
            0.5, 0.5,
            self._t("stats.no_data", "Keine Daten"),
            transform=ax.transAxes,
            ha="center", va="center",
            fontsize=14, color="#64748B", weight='bold'
        )
        ax.set_axis_off()
    
    def _styled_label(self, text):
        """Create a styled form label."""
        label = QLabel(text)
        label.setStyleSheet("font-size: 14px; font-weight: 600; color: #475569;")
        return label
    
    def _t(self, key, fallback):
        """Translate a key or return fallback."""
        if not self.translator:
            return fallback
        return self.translator.get(key, fallback)
