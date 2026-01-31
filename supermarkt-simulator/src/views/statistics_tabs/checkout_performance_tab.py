"""
Checkout Performance Tab - Detailed checkout analysis with subtabs.
Provides checkout status, top/flop performers, performance metrics, and skill comparison.
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
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    HAS_MATPLOTLIB = True
except Exception:
    FigureCanvas = None
    Figure = None
    HAS_MATPLOTLIB = False


class CheckoutPerformanceTab(QWidget):
    """
    Checkout Performance Tab with subtabs:
    - Übersicht: Status and Top/Flop performers
    - Leistungstabelle: Full-width performance table
    - Fertigkeitsvergleich: Skill comparison chart
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
        self.table_tab = self._create_table_tab()
        self.skill_tab = self._create_skill_tab()
        
        self.subtabs.addTab(self.overview_tab, self._t("stats.subtab_overview", "Übersicht"))
        self.subtabs.addTab(self.table_tab, self._t("stats.subtab_performance_table", "Leistungstabelle"))
        if HAS_MATPLOTLIB:
            self.subtabs.addTab(self.skill_tab, self._t("stats.subtab_skill_comparison", "Fertigkeitsvergleich"))
        
        layout.addWidget(self.subtabs)
    
    def _create_overview_tab(self):
        """Create overview subtab with status and top/flop performers."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Header
        header = QLabel(self._t("stats.checkout_performance_header", "Kassen-Performance"))
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #1E293B; padding: 8px 0px;")
        layout.addWidget(header)
        
        # Status + Top/Flop row
        top_row = QHBoxLayout()
        top_row.setSpacing(16)
        
        status_box = self._create_status_box()
        top_row.addWidget(status_box, 1)
        
        topflop_box = self._create_topflop_box()
        top_row.addWidget(topflop_box, 1)
        
        layout.addLayout(top_row)
        layout.addStretch()
        
        return tab
    
    def _create_table_tab(self):
        """Create performance table subtab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # Info label (compact)
        info = QLabel(self._t(
            "stats.checkout_performance_desc",
            "Detaillierte Leistungsübersicht aller Kassen. Klicken Sie auf die Spaltenüberschriften zum Sortieren."
        ))
        info.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 500; padding: 4px; margin: 0px;")
        info.setWordWrap(True)
        info.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        layout.addWidget(info)
        
        # Performance table (expandiert um verfügbaren Platz zu füllen)
        self.checkout_table = QTableWidget()
        self.checkout_table.setColumnCount(10)
        self.checkout_table.setHorizontalHeaderLabels([
            self._t("stats.checkout_id", "ID"),
            self._t("stats.checkout_skill", "Skill"),
            self._t("stats.checkout_customers", "Kunden"),
            self._t("stats.checkout_items", "Artikel"),
            self._t("stats.checkout_queue", "Queue (min)"),
            self._t("stats.checkout_scan", "Scan (min)"),
            self._t("stats.checkout_payment", "Zahlung"),
            self._t("stats.checkout_uptime", "Uptime %"),
            self._t("stats.checkout_malfunctions", "Störungen"),
            self._t("stats.checkout_rating", "Bewertung"),
        ])
        
        self.checkout_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._style_table(self.checkout_table)
        layout.addWidget(self.checkout_table, 1)  # stretch factor 1 für expansion
        
        return tab
    
    def _create_skill_tab(self):
        """Create skill comparison subtab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 8, 16, 16)
        layout.setSpacing(8)
        
        # Header (smaller)
        header = QLabel(self._t("stats.skill_comparison_title", "Skill-Vergleich"))
        header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header.setStyleSheet("color: #1E293B; padding: 4px 0px;")
        layout.addWidget(header)
        
        self.skill_figure = Figure(figsize=(10, 4.5))
        self.skill_canvas = FigureCanvas(self.skill_figure)
        self.skill_ax = self.skill_figure.add_subplot(1, 1, 1)
        self.skill_figure.subplots_adjust(left=0.08, right=0.98, top=0.80, bottom=0.15)
        
        layout.addWidget(self.skill_canvas)
        
        self.lbl_skill_insight = QLabel()
        self.lbl_skill_insight.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 500; padding: 4px;")
        self.lbl_skill_insight.setWordWrap(True)
        layout.addWidget(self.lbl_skill_insight)
        
        layout.addStretch()
        
        return tab
    
    def _create_status_box(self):
        """Create checkout status overview box."""
        gb = QGroupBox(self._t("stats.checkout_status_title", "Kassen-Status"))
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
        
        self.lbl_status_open = QLabel("0")
        self.lbl_status_open.setStyleSheet("font-size: 16px; font-weight: 700; color: #10B981;")
        
        self.lbl_status_malfunction = QLabel("0")
        self.lbl_status_malfunction.setStyleSheet("font-size: 16px; font-weight: 700; color: #EF4444;")
        
        self.lbl_status_closed = QLabel("0")
        self.lbl_status_closed.setStyleSheet("font-size: 16px; font-weight: 700; color: #94A3B8;")
        
        self.lbl_status_total = QLabel("0")
        self.lbl_status_total.setStyleSheet("font-size: 16px; font-weight: 700; color: #1E293B;")
        
        layout.addRow(self._t("stats.checkouts_open", "Offen:"), self.lbl_status_open)
        layout.addRow(self._t("stats.checkouts_malfunction", "Störung:"), self.lbl_status_malfunction)
        layout.addRow(self._t("stats.checkouts_closed", "Geschlossen:"), self.lbl_status_closed)
        layout.addRow(self._t("stats.checkouts_total", "Gesamt:"), self.lbl_status_total)
        
        return gb
    
    def _create_topflop_box(self):
        """Create Top/Flop performer box."""
        gb = QGroupBox(self._t("stats.topflop_title", "Top / Flop Performer"))
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
        
        layout = QVBoxLayout(gb)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Top Performer
        top_label = QLabel(self._t("stats.top_performer", "TOP PERFORMER"))
        top_label.setStyleSheet("font-size: 13px; font-weight: 700; color: #10B981;")
        layout.addWidget(top_label)
        
        self.lbl_top_performer = QLabel(self._t("stats.loading", "Lade..."))
        self.lbl_top_performer.setWordWrap(True)
        self.lbl_top_performer.setStyleSheet("font-size: 12px; color: #475569; padding-left: 20px;")
        layout.addWidget(self.lbl_top_performer)
        
        # Flop Performer
        flop_label = QLabel(self._t("stats.flop_performer", "FLOP PERFORMER"))
        flop_label.setStyleSheet("font-size: 13px; font-weight: 700; color: #F59E0B;")
        layout.addWidget(flop_label)
        
        self.lbl_flop_performer = QLabel(self._t("stats.loading", "Lade..."))
        self.lbl_flop_performer.setWordWrap(True)
        self.lbl_flop_performer.setStyleSheet("font-size: 12px; color: #475569; padding-left: 20px;")
        layout.addWidget(self.lbl_flop_performer)
        
        layout.addStretch()
        
        return gb
    
    def update_status(self, stats):
        """Update checkout status counts."""
        checkouts = stats.get("checkouts", {})
        
        open_count = 0
        malfunction_count = 0
        closed_count = 0
        
        for checkout_stats in checkouts.values():
            status = checkout_stats.get("status", "closed")
            if status == "open":
                open_count += 1
            elif status in ["malfunction", "conflict"]:
                malfunction_count += 1
            else:
                closed_count += 1
        
        total = len(checkouts)
        
        self.lbl_status_open.setText(str(open_count))
        self.lbl_status_malfunction.setText(str(malfunction_count))
        self.lbl_status_closed.setText(str(closed_count))
        self.lbl_status_total.setText(str(total))
    
    def update_topflop(self, stats):
        """Update Top/Flop performer information."""
        checkouts = stats.get("checkouts", {})
        
        if not checkouts:
            self.lbl_top_performer.setText(self._t("stats.no_data", "Noch keine Daten"))
            self.lbl_flop_performer.setText(self._t("stats.no_data", "Noch keine Daten"))
            return
        
        # Calculate scores
        scores = []
        for cid, c_stats in checkouts.items():
            customers = c_stats.get("customers_served", 0)
            queue_avg = c_stats.get("queue_wait", {}).get("avg", 1.0) / 60.0
            skill = c_stats.get("skill", "-")
            malfunctions = c_stats.get("events", {}).get("malfunction_events", 0)
            
            score = (customers / max(queue_avg, 0.1)) - (malfunctions * 10)
            scores.append((cid, skill, customers, queue_avg, malfunctions, score))
        
        scores.sort(key=lambda x: x[5], reverse=True)
        
        # Top Performer
        if scores:
            top = scores[0]
            top_text = f"Kasse #{top[0]} ({top[1]})\n"
            top_text += f" {top[2]} Kunden bedient\n"
            top_text += f" Ø Queue: {top[3]:.1f} min\n"
            top_text += f" Störungen: {top[4]}"
            self.lbl_top_performer.setText(top_text)
        
        # Flop Performer
        if len(scores) > 1:
            flop = scores[-1]
            flop_text = f"Kasse #{flop[0]} ({flop[1]})\n"
            flop_text += f" {flop[2]} Kunden bedient\n"
            flop_text += f" Ø Queue: {flop[3]:.1f} min\n"
            flop_text += f" Störungen: {flop[4]}"
            self.lbl_flop_performer.setText(flop_text)
        else:
            self.lbl_flop_performer.setText(self._t("stats.only_one_checkout", "Nur eine Kasse aktiv"))
    
    def update_performance_table(self, stats):
        """Update the checkout performance table."""
        checkouts = stats.get("checkouts", {})
        
        was_sorting = self.checkout_table.isSortingEnabled()
        self.checkout_table.setSortingEnabled(False)
        
        self.checkout_table.setRowCount(len(checkouts))
        
        for row, (cid, c_stats) in enumerate(sorted(checkouts.items(), key=lambda x: x[0])):
            # ID
            self.checkout_table.setItem(row, 0, self._make_item(str(cid), numeric=True))
            
            # Skill
            skill = c_stats.get("skill", "-")
            self.checkout_table.setItem(row, 1, self._make_item(skill))
            
            # Customers
            customers = c_stats.get("customers_served", 0)
            self.checkout_table.setItem(row, 2, self._make_item(customers, numeric=True))
            
            # Items
            items = c_stats.get("total_items", 0)
            self.checkout_table.setItem(row, 3, self._make_item(items, numeric=True))
            
            # Queue time
            queue_avg = c_stats.get("queue_wait", {}).get("avg", 0.0) / 60.0
            item = self._make_item(f"{queue_avg:.1f}", numeric=True)
            if queue_avg <= 3:
                item.setBackground(QColor("#D1FAE5"))
            elif queue_avg <= 6:
                item.setBackground(QColor("#FEF3C7"))
            else:
                item.setBackground(QColor("#FEE2E2"))
            self.checkout_table.setItem(row, 4, item)
            
            # Scan time
            service_avg = c_stats.get("service_time", {}).get("avg", 0.0) / 60.0
            payment_avg = c_stats.get("payment", {}).get("total_time", {}).get("avg", 0.0) / 60.0
            scan_avg = max(0.0, service_avg - payment_avg)
            self.checkout_table.setItem(row, 5, self._make_item(f"{scan_avg:.1f}", numeric=True))
            
            # Payment methods
            cash = c_stats.get("payment", {}).get("cash_count", 0)
            card = c_stats.get("payment", {}).get("card_count", 0)
            payment_text = f"Bar: {cash} / Karte: {card}"
            self.checkout_table.setItem(row, 6, self._make_item(payment_text))
            
            # Uptime
            uptime = c_stats.get("availability", {}).get("uptime_percent", 100.0)
            item = self._make_item(f"{uptime:.0f}", numeric=True)
            if uptime >= 95:
                item.setBackground(QColor("#D1FAE5"))
            elif uptime >= 80:
                item.setBackground(QColor("#FEF3C7"))
            else:
                item.setBackground(QColor("#FEE2E2"))
            self.checkout_table.setItem(row, 7, item)
            
            # Malfunctions
            malfunctions = c_stats.get("events", {}).get("malfunction_events", 0)
            item = self._make_item(malfunctions, numeric=True)
            if malfunctions == 0:
                item.setBackground(QColor("#D1FAE5"))
            elif malfunctions <= 2:
                item.setBackground(QColor("#FEF3C7"))
            else:
                item.setBackground(QColor("#FEE2E2"))
            self.checkout_table.setItem(row, 8, item)
            
            # Rating
            rating = self._calculate_checkout_rating(c_stats)
            self.checkout_table.setItem(row, 9, self._make_item(rating))
        
        self.checkout_table.setSortingEnabled(was_sorting)
    
    def _calculate_checkout_rating(self, checkout_stats):
        """Calculate overall checkout rating."""
        customers = checkout_stats.get("customers_served", 0)
        queue_avg = checkout_stats.get("queue_wait", {}).get("avg", 999) / 60.0
        uptime = checkout_stats.get("availability", {}).get("uptime_percent", 0)
        malfunctions = checkout_stats.get("events", {}).get("malfunction_events", 0)
        
        score = 0
        if customers >= 40:
            score += 3
        elif customers >= 20:
            score += 2
        elif customers >= 10:
            score += 1
        
        if queue_avg <= 3:
            score += 3
        elif queue_avg <= 5:
            score += 2
        elif queue_avg <= 8:
            score += 1
        
        if uptime >= 95:
            score += 2
        elif uptime >= 85:
            score += 1
        
        if malfunctions == 0:
            score += 2
        elif malfunctions <= 1:
            score += 1
        
        if score >= 9:
            return ""
        elif score >= 7:
            return ""
        elif score >= 5:
            return ""
        elif score >= 3:
            return ""
        else:
            return ""
    
    def update_skill_comparison(self, stats):
        """Update skill comparison chart."""
        if not HAS_MATPLOTLIB:
            return
        
        self.skill_ax.clear()
        
        advanced = stats.get("advanced", {}).get("skill", {})
        
        newbie_scan = advanced.get("newbie", {}).get("scan_time", {}).get("avg", 0.0) / 60.0
        pro_scan = advanced.get("pro", {}).get("scan_time", {}).get("avg", 0.0) / 60.0
        
        if newbie_scan == 0 and pro_scan == 0:
            self._show_no_data(self.skill_ax)
            self.skill_canvas.draw_idle()
            return
        
        skills = ["Pro", "Azubi"]
        scan_times = [pro_scan, newbie_scan]
        colors = ['#10B981', '#F59E0B']
        
        bars = self.skill_ax.barh(skills, scan_times, color=colors, height=0.5)
        
        for bar in bars:
            width = bar.get_width()
            self.skill_ax.text(width, bar.get_y() + bar.get_height()/2,
                             f'{width:.2f} min',
                             ha='left', va='center',
                             fontweight='bold', fontsize=11, color='#1E293B')
        
        self.skill_ax.set_title(
            self._t("stats.skill_scan_times_title", "Durchschnittliche Scanzeit nach Skill"),
            fontsize=13, fontweight='bold', color='#1E293B', pad=10
        )
        self.skill_ax.set_xlabel(
            self._t("stats.minutes", "Minuten"),
            fontsize=11, color='#475569'
        )
        self.skill_ax.grid(True, axis='x', alpha=0.3, linestyle='--')
        self.skill_ax.spines['top'].set_visible(False)
        self.skill_ax.spines['right'].set_visible(False)
        
        self.skill_canvas.draw_idle()
        
        if newbie_scan > 0 and pro_scan > 0:
            ratio = newbie_scan / pro_scan if pro_scan > 0 else 0
            diff_percent = ((newbie_scan - pro_scan) / pro_scan * 100) if pro_scan > 0 else 0
            insight = f" Effizienz-Ratio: Azubi {ratio:.2f}x langsamer als Pro ({diff_percent:+.0f}%)\n"
            insight += f" Empfehlung: Mehr Schulungen für Azubis könnten Effizienz um bis zu {diff_percent:.0f}% steigern"
            self.lbl_skill_insight.setText(insight)
    
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
    
    def _show_no_data(self, ax):
        """Show 'no data' message on axis."""
        ax.text(
            0.5, 0.5,
            self._t("stats.no_data", "Keine Daten"),
            transform=ax.transAxes,
            ha="center", va="center",
            fontsize=12, color="#64748B"
        )
        ax.set_axis_off()
    
    def _t(self, key, fallback):
        """Translate a key or return fallback."""
        if not self.translator:
            return fallback
        return self.translator.get(key, fallback)
