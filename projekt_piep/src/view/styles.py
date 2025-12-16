# src/view/styles.py
from PyQt6.QtGui import QColor, QFont


class Dimensions:
    """Original dimensions from the legacy project."""

    SHELF_SIZE = 20
    CUSTOMER_SIZE = 14
    CASHIER_SIZE = 14
    CHECKOUT_WIDTH = 100
    CHECKOUT_HEIGHT = 100

    # Simulation Settings
    QUEUE_SPACING = 18

    # Layout Offsets (Standardwerte aus dem alten Code)
    DEFAULT_OFFSETS = {
        "offset_cashier_left": [-15, 8],
        "offset_cashier_right": [45, 8],
        "offset_queue_left": [5, -60],
        "offset_queue_right": [35, -60],
        "offset_queue_sb_left": [5, -60],
        "offset_queue_sb_right": [35, -60],
    }


class Colors:
    """Original color palette."""

    # Entities
    SHELF = QColor("#3F51B5")
    CUSTOMER = QColor("#E91E63")
    CASHIER = QColor("#FFD700")
    CHECKOUT_NORMAL = QColor("#607D8B")
    CHECKOUT_SB = QColor("#00B0D0")  # Türkis wie im Original

    # UI / Status
    WHITE = QColor("#FFFFFF")
    BLACK = QColor("#000000")
    LIGHT_GREY = QColor(
        "#F8F8F8"
    )  # <-- WIEDER HINZUGEFÜGT (Legacy: COLOR_LIGHT_BG)

    SCAN_PROGRESS = QColor("#00E676")  # Der grüne Ladebalken
    SELECTION = QColor("#FF0000")
    WAITING_AREA = QColor(0, 255, 0, 30)

    @staticmethod
    def get_checkout_color(type_str: str) -> QColor:
        if type_str == "SB":
            return Colors.CHECKOUT_SB
        return Colors.CHECKOUT_NORMAL


class Fonts:
    """Font definitions."""

    @staticmethod
    def customer_text():
        f = QFont()
        f.setPixelSize(10)
        f.setBold(True)
        return f

    @staticmethod
    def ui_label():
        return QFont("Segoe UI", 10)
