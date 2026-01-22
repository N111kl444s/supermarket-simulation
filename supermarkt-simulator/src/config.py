"""
Central configuration module.
Refactored:
- ADDED: Missing Speed Factors (FACTOR_4X, FACTOR_8X, FACTOR_16X, FACTOR_32X) to match Controller imports.
- ADDED: Specific screen colors (COLOR_SCREEN_OPEN, COLOR_SCREEN_CLOSED) - softer/modern.
- ADDED: COLOR_SCREEN_TEXT.
"""

import sys
import os
from pathlib import Path
from PyQt6.QtGui import QColor


# --- PATH HANDLING FOR EXE VS SCRIPT ---
def get_paths():
    if getattr(sys, "frozen", False):
        INTERNAL_DIR = Path(sys._MEIPASS)
        EXTERNAL_DIR = Path(sys.executable).parent
    else:
        SCRIPT_FILE = Path(__file__).resolve()
        SRC_DIR = SCRIPT_FILE.parent
        BASE_DIR = SRC_DIR.parent
        INTERNAL_DIR = BASE_DIR
        EXTERNAL_DIR = BASE_DIR
    return INTERNAL_DIR, EXTERNAL_DIR


INTERNAL_BASE, EXTERNAL_BASE = get_paths()

ASSETS_DIR = INTERNAL_BASE / "assets"
IMAGE_DIR = ASSETS_DIR / "images"
MAPS_DIR = EXTERNAL_BASE / "maps"
SETTINGS_FILE = EXTERNAL_BASE / "settings.json"

if getattr(sys, "frozen", False):
    if not MAPS_DIR.exists():
        try:
            MAPS_DIR.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass


def get_image_files(prefix):
    """
    Scans IMAGE_DIR for files starting with 'prefix'.
    Returns a SORTED list of filenames to ensure consistent indexing.
    """
    if not IMAGE_DIR.exists():
        return []
    # FIX: Sorted ensures that file order is OS-independent
    files = sorted(list(IMAGE_DIR.glob(f"{prefix}*.png")))
    if not files:
        generic = IMAGE_DIR / f"{prefix}.png"
        if generic.exists():
            return [generic.name]
    return [f.name for f in files]


# --- WINDOW ---
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800

# --- COLORS ---
COLOR_BG_MAIN = QColor("#F5F7FA")
COLOR_BG_PANEL = QColor("#FFFFFF")
COLOR_BG_INPUT = QColor("#FFFFFF")
COLOR_BORDER = QColor("#D1D5DB")
COLOR_ACCENT = QColor("#3B82F6")
COLOR_ACCENT_HOVER = QColor("#2563EB")

# Modern, less saturated status colors
COLOR_SUCCESS = QColor("#10B981")  # Emerald 500
COLOR_WARNING = QColor("#F59E0B")
COLOR_ERROR = QColor("#EF4444")  # Red 500

COLOR_ORANGE = QColor("#F97316")
COLOR_TEXT_MAIN = QColor("#1F2937")
COLOR_TEXT_MUTED = QColor("#6B7280")
COLOR_SHELF = QColor("#64748B")
COLOR_CUSTOMER = QColor("#EC4899")
COLOR_CASHIER = QColor("#F59E0B")
COLOR_CHECKOUT = QColor("#3B82F6")
COLOR_WAITING_AREA = QColor(59, 130, 246, 60)
COLOR_START_AREA = QColor(16, 185, 129, 60)
COLOR_EXIT_AREA = QColor(239, 68, 68, 60)
COLOR_SELECTION = QColor("#EF4444")
COLOR_QUEUE_HIGHLIGHT = QColor("#8B5CF6")
COLOR_SCAN_PROGRESS = QColor("#10B981")
COLOR_WALL = QColor("#374151")
COLOR_FLOOR = QColor("#E5E7EB")
COLOR_GRID = QColor("#D1D5DB")

COLOR_GREEN = COLOR_SUCCESS
COLOR_RED = COLOR_ERROR
COLOR_BLUE = COLOR_ACCENT
COLOR_DARK_TEXT = COLOR_TEXT_MAIN
COLOR_LIGHT_BG = COLOR_BG_MAIN
COLOR_WHITE_BG = COLOR_BG_PANEL

# --- SCREEN COLORS (NEW) ---
COLOR_SCREEN_OPEN = QColor(
    "#059669"
)  # Emerald 600 (etwas dunkler für guten Kontrast mit weißer Schrift)
COLOR_SCREEN_CLOSED = QColor("#DC2626")  # Red 600
COLOR_SCREEN_TEXT = QColor("#FFFFFF")  # White

# --- Constants ---
SHELF_SIZE = 50.0
CUSTOMER_SIZE = 32
CASHIER_SIZE = 10
CHECKOUT_WIDTH = 120
CHECKOUT_HEIGHT = 100

# --- TIME & PHYSICS ---
ANIMATION_TICK_MS = 33
FACTOR_1X = 60.0
FACTOR_2X = 120.0
FACTOR_4X = 240.0
FACTOR_6X = 360.0
FACTOR_8X = 480.0
FACTOR_16X = 960.0
FACTOR_32X = 1920.0

WALK_SPEED_PPS = 100.0
WALK_SPEED_DISABLED_FACTOR = 0.6
DEFAULT_OPEN_TIME = (8, 0)
DEFAULT_CLOSE_TIME = (20, 0)
SCAN_TIME_PER_ITEM_MS = 1000

# --- DYNAMIC IMAGE LISTS ---

# 1. Normal Customers
IMG_CUSTOMERS_NORMAL = get_image_files("kunde")
if not IMG_CUSTOMERS_NORMAL:
    IMG_CUSTOMERS_NORMAL = ["customer.png"]

# 2. Disabled Customers
IMG_CUSTOMERS_DISABLED = get_image_files("behindert")
if not IMG_CUSTOMERS_DISABLED:
    IMG_CUSTOMERS_DISABLED = ["customer_disabled.png"]

# 3. Handheld Customers (Normal)
IMG_CUSTOMERS_HANDHELD = get_image_files("handheld_kunde")
if not IMG_CUSTOMERS_HANDHELD:
    IMG_CUSTOMERS_HANDHELD = IMG_CUSTOMERS_NORMAL

# 4. Handheld Customers (Disabled)
IMG_CUSTOMERS_HANDHELD_DISABLED = get_image_files("handheld_behindert")
if not IMG_CUSTOMERS_HANDHELD_DISABLED:
    IMG_CUSTOMERS_HANDHELD_DISABLED = IMG_CUSTOMERS_DISABLED

# 5. Shelves
IMG_SHELVES = get_image_files("regal")
if not IMG_SHELVES:
    IMG_SHELVES = ["regal.png"]

# 6. Checkouts
IMG_CHECKOUTS = ["kasse.png", "sb.png"]

# 7. Cashiers
IMG_CASHIERS_AZUBI = get_image_files("azubi")
if not IMG_CASHIERS_AZUBI:
    IMG_CASHIERS_AZUBI = ["azubi.png"]

IMG_CASHIERS_PRO = get_image_files("festangestellter")
if not IMG_CASHIERS_PRO:
    IMG_CASHIERS_PRO = ["festangestellter.png"]

# --- DEFAULT SETTINGS DICT ---
DEFAULT_SETTINGS = {
    "show_routes": True,
    "show_shelves": True,
    "show_shelf_numbers": True,
    "show_checkouts": True,
    "show_checkout_numbers": True,
    "show_cashiers": True,
    "show_queues": False,
    "show_waiting_area": True,
    "show_start_area": True,
    "show_exit_area": True,
    "size_shelf": SHELF_SIZE,
    "size_cashier": CASHIER_SIZE,
    "size_customer": CUSTOMER_SIZE,
    "size_checkout_width": CHECKOUT_WIDTH,
    "size_checkout_height": CHECKOUT_HEIGHT,
    "size_queue_dot": 4,
    "dist_queue_spacing": 20,
    "size_screen_normal_width": 15,
    "size_screen_normal_height": 10,
    "size_screen_sb_width": 10,
    "size_screen_sb_height": 10,
    "customer_path_offset": 10,
    "offset_queue_left": [0, 0],
    "offset_queue_right": [0, 0],
    "offset_queue_sb_left": [0, 0],
    "offset_queue_sb_right": [0, 0],
    "offset_cashier_left": [0, 0],
    "offset_cashier_right": [0, 0],
    "offset_screen_normal_left": [0, 0],
    "offset_screen_normal_right": [0, 0],
    "offset_screen_sb_left": [0, 0],
    "offset_screen_sb_right": [0, 0],
}
