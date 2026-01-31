"""
Stats Updater.
Handles updating statistics labels with live data.
Splits large update methods into smaller, themed components.
"""


class StatsUpdater:
    """Manages updating statistics UI components with live data."""

    def __init__(self, live_tab, details_tab):
        """
        Initialize the stats updater.
        
        Args:
            live_tab: StatsLiveTab instance
            details_tab: StatsDetailsTab instance
        """
        self.live_tab = live_tab
        self.details_tab = details_tab

    def update_all(self, stats):
        """
        Update all statistics from live stats dictionary.
        
        Args:
            stats: Dictionary containing live statistics data
        """
        self.update_customers(stats)
        self.update_satisfaction(stats)
        self.update_checkouts(stats)
        self.update_items(stats)
        self.update_payments(stats)
        self.update_issues(stats)
        self.update_times(stats)

    def update_customers(self, stats):
        """Update customer-related metrics."""
        # Check if we have data
        total_served = stats.get('total_customers_served', 0)
        has_data = total_served > 0
        
        # Live tab - customers in store
        if hasattr(self.live_tab, 'lbl_customers_in_store'):
            customers_in_store = stats.get('customers_in_store', 0)
            self.live_tab.lbl_customers_in_store.setText(str(customers_in_store))

        # Live tab - total served
        if hasattr(self.live_tab, 'lbl_total_customers_served_live'):
            self.live_tab.lbl_total_customers_served_live.setText(
                str(total_served) if has_data else "–"
            )

        # Details tab - total served
        if hasattr(self.details_tab, 'lbl_total_customers'):
            self.details_tab.lbl_total_customers.setText(
                str(total_served) if has_data else "–"
            )

        # Live tab - throughput
        if hasattr(self.live_tab, 'lbl_throughput'):
            throughput = stats.get('throughput_per_hour', 0.0)
            self.live_tab.lbl_throughput.setText(
                f"{throughput:.0f} K/h" if has_data else "– K/h"
            )

    def update_satisfaction(self, stats):
        """Update satisfaction-related metrics."""
        # Average wait time
        if hasattr(self.live_tab, 'lbl_avg_wait'):
            avg_wait = stats.get('avg_wait_time_min', 0.0)
            self.live_tab.lbl_avg_wait.setText(f"{avg_wait:.1f} min")

            # Update wait status emoji and progress bar
            if hasattr(self.live_tab, 'lbl_wait_status'):
                if avg_wait < 3.0:
                    self.live_tab.lbl_wait_status.setText("")
                    color = "#10B981"
                elif avg_wait < 5.0:
                    self.live_tab.lbl_wait_status.setText("")
                    color = "#F59E0B"
                else:
                    self.live_tab.lbl_wait_status.setText("")
                    color = "#EF4444"

            # Update progress bar
            if hasattr(self.live_tab, 'wait_progress'):
                wait_value = min(int(avg_wait), 10)
                self.live_tab.wait_progress.setValue(wait_value)
                self.live_tab.wait_progress.setStyleSheet(f"""
                    QProgressBar {{
                        border: none;
                        border-radius: 3px;
                        background-color: #E5E7EB;
                    }}
                    QProgressBar::chunk {{
                        background-color: {color};
                        border-radius: 3px;
                    }}
                """)

        # Queue count
        if hasattr(self.live_tab, 'lbl_queue_count'):
            queue_count = stats.get('queue_count', 0)
            self.live_tab.lbl_queue_count.setText(str(queue_count))

        # Longest queue
        if hasattr(self.live_tab, 'lbl_longest_queue'):
            max_len = stats.get("longest_queue", 0)
            checkout_ids = stats.get("longest_queue_checkouts", [])
            if max_len > 0 and checkout_ids:
                ids_text = ", ".join(str(cid) for cid in checkout_ids)
                self.live_tab.lbl_longest_queue.setText(f"Kasse #{ids_text} ({max_len})")
            else:
                self.live_tab.lbl_longest_queue.setText(f"Kasse #0 ({max_len})")

        # Satisfaction score
        if hasattr(self.live_tab, 'lbl_satisfaction_score'):
            satisfaction = stats.get('satisfaction_score', 0.0)
            self.live_tab.lbl_satisfaction_score.setText(f"{int(satisfaction)}%")

            # Update progress bar
            if hasattr(self.live_tab, 'satisfaction_progress'):
                self.live_tab.satisfaction_progress.setValue(int(satisfaction))
                
                # Color based on score
                if satisfaction >= 80:
                    color = "#10B981"
                    status = "SEHR GUT"
                elif satisfaction >= 60:
                    color = "#F59E0B"
                    status = "GUT"
                else:
                    color = "#EF4444"
                    status = "KRITISCH"

                self.live_tab.satisfaction_progress.setStyleSheet(f"""
                    QProgressBar {{
                        border: none;
                        border-radius: 5px;
                        background-color: #E5E7EB;
                    }}
                    QProgressBar::chunk {{
                        background-color: {color};
                        border-radius: 5px;
                    }}
                """)

                # Update status label
                if hasattr(self.live_tab, 'lbl_satisfaction_status'):
                    self.live_tab.lbl_satisfaction_status.setText(f"Status: {status}")
                    self.live_tab.lbl_satisfaction_status.setStyleSheet(
                        f"font-size: 13px; color: {color}; font-weight: 700; text-align: center;"
                    )

    def update_checkouts(self, stats):
        """Update checkout-related metrics."""
        # Get checkout counts
        open_c = stats.get('checkouts_open', 0)
        avail_c = stats.get('checkouts_available', 0)
        total_c = stats.get('total_checkouts', open_c)
        malfunction_c = stats.get('checkouts_malfunction', 0)
        closed_c = total_c - open_c

        # Open checkouts (available, not malfunctioning)
        if hasattr(self.live_tab, 'lbl_checkouts_open'):
            self.live_tab.lbl_checkouts_open.setText(str(avail_c))

        # Malfunction checkouts
        if hasattr(self.live_tab, 'lbl_checkouts_malfunction'):
            self.live_tab.lbl_checkouts_malfunction.setText(str(malfunction_c))

        # Closed checkouts
        if hasattr(self.live_tab, 'lbl_checkouts_closed'):
            self.live_tab.lbl_checkouts_closed.setText(str(closed_c))

        # Compatibility label
        if hasattr(self.live_tab, 'lbl_available_checkouts'):
            self.live_tab.lbl_available_checkouts.setText(f"{avail_c}/{open_c}")

    def update_items(self, stats):
        """Update item-related metrics."""
        # Check if we have data
        total_served = stats.get('total_customers_served', 0)
        has_data = total_served > 0
        
        # Total items
        if hasattr(self.details_tab, 'lbl_total_items'):
            total_items = stats.get('total_items_processed', 0)
            self.details_tab.lbl_total_items.setText(
                str(total_items) if has_data else "–"
            )

        # Average items per customer
        if hasattr(self.details_tab, 'lbl_avg_items_per_customer'):
            avg_items = stats.get('avg_items_per_customer', 0.0)
            self.details_tab.lbl_avg_items_per_customer.setText(
                f"{avg_items:.1f}" if has_data else "–"
            )

    def update_payments(self, stats):
        """Update payment-related metrics."""
        # Cash percentage
        if hasattr(self.details_tab, 'lbl_payment_cash'):
            cash_percent = stats.get('payment_cash_percent', 0.0)
            self.details_tab.lbl_payment_cash.setText(f"{int(cash_percent)}%")

        # Card percentage
        if hasattr(self.details_tab, 'lbl_payment_card'):
            card_percent = stats.get('payment_card_percent', 0.0)
            self.details_tab.lbl_payment_card.setText(f"{int(card_percent)}%")

    def update_issues(self, stats):
        """Update issue-related metrics."""
        # Malfunctions
        if hasattr(self.details_tab, 'lbl_malfunctions'):
            malfunctions = stats.get('malfunctions_today', 0)
            self.details_tab.lbl_malfunctions.setText(str(malfunctions))

        # Annoyance
        if hasattr(self.details_tab, 'lbl_annoyance'):
            annoyance = stats.get('annoyance_today', 0)
            self.details_tab.lbl_annoyance.setText(str(annoyance))

        # Conflicts
        if hasattr(self.details_tab, 'lbl_conflicts'):
            conflicts = stats.get('conflicts_today', 0)
            self.details_tab.lbl_conflicts.setText(str(conflicts))

    def update_times(self, stats):
        """Update time-related metrics."""
        # Elapsed time
        if hasattr(self.details_tab, 'lbl_elapsed_open'):
            elapsed = stats.get('elapsed_time', "0:00")
            self.details_tab.lbl_elapsed_open.setText(elapsed)

        # Scheduled time
        if hasattr(self.details_tab, 'lbl_scheduled_open'):
            scheduled = stats.get('scheduled_time', "0:00")
            self.details_tab.lbl_scheduled_open.setText(scheduled)

        # Overtime
        if hasattr(self.details_tab, 'lbl_overtime'):
            overtime = stats.get('overtime', "+0:00")
            self.details_tab.lbl_overtime.setText(overtime)
