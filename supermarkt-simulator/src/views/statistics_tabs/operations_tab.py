"""
Operations Tab - Operating hours, overtime, and peak analysis.
Provides insights into operational efficiency and peak times.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QGroupBox,
    QFormLayout,
)
from PyQt6.QtCore import QTime
from PyQt6.QtGui import QFont

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    HAS_MATPLOTLIB = True
except Exception:
    FigureCanvas = None
    Figure = None
    HAS_MATPLOTLIB = False


class OperationsTab(QWidget):
    """
    Operations Tab with:
    - Operating hours and overtime
    - Peak analysis
    - Hourly customer distribution chart
    """
    
    def __init__(self, translator=None, parent=None):
        super().__init__(parent)
        self.translator = translator
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Header
        header = QLabel(self._t("stats.operations_header", "Betrieb & Peak-Analyse"))
        header.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        header.setStyleSheet("color: #1E293B; padding: 8px 0px;")
        layout.addWidget(header)
        
        # Operating hours section
        hours_box = self._create_hours_box()
        layout.addWidget(hours_box)
        
        # Peak analysis chart
        if HAS_MATPLOTLIB:
            peak_box = self._create_peak_chart()
            layout.addWidget(peak_box)
        
        layout.addStretch()
    
    def _create_hours_box(self):
        """Create operating hours box."""
        gb = QGroupBox(self._t("stats.operating_hours_title", "Betriebszeiten"))
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
        
        self.lbl_open_time = QLabel("-")
        self.lbl_close_time = QLabel("-")
        self.lbl_scheduled = QLabel("-")
        self.lbl_actual = QLabel("-")
        self.lbl_overtime = QLabel("-")
        self.lbl_peak_time = QLabel("-")
        self.lbl_peak_queue = QLabel("-")
        
        for lbl in [self.lbl_open_time, self.lbl_close_time, self.lbl_scheduled, 
                    self.lbl_actual, self.lbl_overtime, self.lbl_peak_time, self.lbl_peak_queue]:
            lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #1E293B;")
        
        layout.addRow(self._styled_label(self._t("stats.open_time", "Öffnet:")), self.lbl_open_time)
        layout.addRow(self._styled_label(self._t("stats.close_time", "Schließt:")), self.lbl_close_time)
        layout.addRow(self._styled_label(self._t("stats.scheduled_time", "Geplant geöffnet:")), self.lbl_scheduled)
        layout.addRow(self._styled_label(self._t("stats.actual_time", "Tatsächlich geöffnet:")), self.lbl_actual)
        layout.addRow(self._styled_label(self._t("stats.overtime", "Überzeit:")), self.lbl_overtime)
        layout.addRow(self._styled_label(self._t("stats.peak_time", "Spitzenstunde:")), self.lbl_peak_time)
        layout.addRow(self._styled_label(self._t("stats.peak_queue", "Max. Warteschlange:")), self.lbl_peak_queue)
        
        return gb
    
    def _create_peak_chart(self):
        """Create peak analysis chart."""
        gb = QGroupBox(self._t("stats.hourly_distribution_title", "Stundenweise Kundenverteilung"))
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
        layout.setContentsMargins(12, 12, 12, 12)
        
        self.peak_figure = Figure(figsize=(10, 4))
        self.peak_canvas = FigureCanvas(self.peak_figure)
        self.peak_ax = self.peak_figure.add_subplot(1, 1, 1)
        self.peak_figure.subplots_adjust(left=0.08, right=0.98, top=0.80, bottom=0.20)
        
        layout.addWidget(self.peak_canvas)
        
        return gb
    
    def update_hours(self, stats):
        """Update operating hours information."""
        global_stats = stats.get("global", {})
        peak = global_stats.get("peak", {})
        
        self.lbl_open_time.setText(global_stats.get("open_time", "-"))
        self.lbl_close_time.setText(global_stats.get("close_time", "-"))
        
        scheduled_sec = global_stats.get("scheduled_open_seconds", 0.0)
        self.lbl_scheduled.setText(self._format_duration(scheduled_sec))
        
        actual_sec = global_stats.get("actual_open_seconds", 0.0)
        self.lbl_actual.setText(self._format_duration(actual_sec))
        
        overtime_sec = global_stats.get("overtime_seconds", 0.0)
        overtime_text = self._format_duration(overtime_sec)
        if overtime_sec > 900:  # > 15 min
            overtime_text = f"⚠️ {overtime_text}"
        self.lbl_overtime.setText(overtime_text)
        
        # Peak time
        peak_hour = peak.get("busiest_hour")
        if peak_hour is not None:
            peak_time = self._format_hour(peak_hour, global_stats.get("open_time", "08:00"))
            self.lbl_peak_time.setText(peak_time)
        else:
            self.lbl_peak_time.setText("-")
        
        # Peak queue
        max_queue = peak.get("max_queue_len", 0)
        max_ids = peak.get("max_queue_checkouts", [])
        if max_queue > 0 and max_ids:
            ids_text = ", ".join(str(cid) for cid in max_ids)
            self.lbl_peak_queue.setText(f"{max_queue} (Kasse {ids_text})")
        else:
            self.lbl_peak_queue.setText(str(max_queue))
    
    def update_peak_chart(self, stats):
        """Update hourly distribution chart."""
        if not HAS_MATPLOTLIB:
            return
        
        self.peak_ax.clear()
        
        global_stats = stats.get("global", {})
        peak = global_stats.get("peak", {})
        hourly_data = peak.get("avg_customers_by_hour", {})
        
        if not hourly_data:
            self._show_no_data(self.peak_ax)
            self.peak_canvas.draw_idle()
            return
        
        hours = sorted(hourly_data.keys())
        customers = [hourly_data[h] for h in hours]
        
        # Bar chart
        bars = self.peak_ax.bar(hours, customers, color='#3B82F6', width=0.8, alpha=0.8)
        
        # Highlight peak hour
        if customers:
            peak_idx = customers.index(max(customers))
            bars[peak_idx].set_color('#EF4444')
        
        self.peak_ax.set_title(
            self._t("stats.hourly_customers_title", "Durchschnittliche Kunden pro Stunde"),
            fontsize=13, fontweight='bold', color='#1E293B', pad=10
        )
        
        # Format x-axis with simulation time
        global_stats = stats.get("global", {})
        open_time = global_stats.get("open_time", "08:00")
        time_labels = [self._format_hour(h, open_time) for h in hours]
        self.peak_ax.set_xticks(hours)
        self.peak_ax.set_xticklabels(time_labels, rotation=45, ha='right')
        
        self.peak_ax.set_xlabel(
            self._t("stats.simulation_time", "Simulationszeit"),
            fontsize=11, color='#475569'
        )
        self.peak_ax.set_ylabel(
            self._t("stats.customers", "Kunden"),
            fontsize=11, color='#475569'
        )
        self.peak_ax.grid(True, axis='y', alpha=0.3, linestyle='--')
        self.peak_ax.spines['top'].set_visible(False)
        self.peak_ax.spines['right'].set_visible(False)
        
        self.peak_canvas.draw_idle()
    
    def _format_duration(self, seconds):
        """Format seconds as HH:MM."""
        total = int(round(seconds))
        h = total // 3600
        m = (total % 3600) // 60
        return f"{h}:{m:02d}"
    
    def _format_hour(self, hour, open_time_str):
        """Format hour as time string."""
        base = QTime.fromString(open_time_str, "HH:mm")
        if base.isValid():
            t = base.addSecs(int(hour) * 3600)
            return t.toString("HH:mm")
        return f"{int(hour):02d}:00"
    
    def _show_no_data(self, ax):
        """Show 'no data' message."""
        ax.text(
            0.5, 0.5,
            self._t("stats.no_data", "Keine Daten"),
            transform=ax.transAxes,
            ha="center", va="center",
            fontsize=12, color="#64748B"
        )
        ax.set_axis_off()
    
    def _styled_label(self, text):
        """Create a styled form label."""
        label = QLabel(text)
        label.setStyleSheet("font-size: 13px; font-weight: 600; color: #475569;")
        return label
    
    def _t(self, key, fallback):
        """Translate a key or return fallback."""
        if not self.translator:
            return fallback
        return self.translator.get(key, fallback)
