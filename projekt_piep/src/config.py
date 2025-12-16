import sys
from pathlib import Path
from PyQt6.QtGui import QColor

# --- Pfade ---
# Wir gehen davon aus, dass diese Datei in /src liegt
SCRIPT_FILE = Path(__file__).resolve()
SRC_DIR = SCRIPT_FILE.parent
BASE_DIR = SRC_DIR.parent
ASSETS_DIR = BASE_DIR / "assets"
IMAGE_DIR = ASSETS_DIR / "images"

# --- Farben ---
COLOR_ORANGE = QColor("#FF6A00")
COLOR_TURQUOISE = QColor("#00B0D0")
COLOR_GREEN = QColor("#50C878")
COLOR_DARK_TEXT = QColor("#333333")
COLOR_LIGHT_BG = QColor("#F8F8F8")
COLOR_WHITE_BG = QColor("#FFFFFF")
COLOR_SHELF = QColor("#3F51B5")
COLOR_CUSTOMER = QColor("#E91E63")
COLOR_CASHIER = QColor("#FFD700")
COLOR_CHECKOUT = QColor("#607D8B")
COLOR_WAITING_AREA = QColor(0, 255, 0, 30)
COLOR_SELECTION = QColor("#FF0000")
COLOR_QUEUE_HIGHLIGHT = QColor("#FF00FF")
COLOR_SCAN_PROGRESS = QColor("#00E676")

# --- KONSTANTEN ---
SHELF_SIZE = 20
CUSTOMER_SIZE = 14
CASHIER_SIZE = 14
CHECKOUT_WIDTH = 100
CHECKOUT_HEIGHT = 100
SIM_TICK_MS = 30
SHELF_PROBABILITY = 0.4
ITEM_PICK_PROBABILITY = 0.7
WALK_SPEED = 3.0
QUEUE_SPACING = 18
SCAN_TIME_PER_ITEM_MS = 800

# --- EINSTELLUNGEN (DEFAULTS) ---
DEFAULT_SETTINGS = {
    "show_routes": False,
    "show_shelves": False,
    "show_checkouts": True,
    "show_cashiers": True,
    "show_waiting_area": True,
    "offset_cashier_left": [-15, 8],
    "offset_cashier_right": [45, 8],
    "offset_light_normal_left": [36, 2],
    "offset_light_normal_right": [36, 2],
    "offset_light_sb_left": [36, 2],
    "offset_light_sb_right": [36, 2],
    "offset_queue_left": [5, -60],
    "offset_queue_right": [35, -60],
    "offset_queue_sb_left": [5, -60],
    "offset_queue_sb_right": [35, -60],
}
