"""
Central configuration module for the supermarket simulation.
Includes a modern 'Flat Light' Color Palette and compatibility aliases.
Refactored for PyInstaller (EXE) Support.
Updated: INCREASED CASHIER_SIZE to 55.
"""

import sys
import os
from pathlib import Path
from PyQt6.QtGui import QColor

# --- PATH HANDLING FOR EXE VS SCRIPT ---
def get_paths():
    """
    Determines the correct paths for resources (read-only) and user data (read-write).
    """
    if getattr(sys, 'frozen', False):
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

# --- DIRECTORIES ---
ASSETS_DIR = INTERNAL_BASE / "assets"
IMAGE_DIR = ASSETS_DIR / "images"

MAPS_DIR = EXTERNAL_BASE / "maps"
SETTINGS_FILE = EXTERNAL_BASE / "settings.json"

if getattr(sys, 'frozen', False):
    if not MAPS_DIR.exists():
        try:
            MAPS_DIR.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

# --- HELPER: Auto-Load Images ---
def get_image_files(prefix):
    """Sucht automatisch nach PNG-Dateien, die mit dem prefix beginnen."""
    if not IMAGE_DIR.exists():
        return []
    files = list(IMAGE_DIR.glob(f"{prefix}*.png"))
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
COLOR_SUCCESS = QColor("#10B981")
COLOR_WARNING = QColor("#F59E0B")
COLOR_ERROR = QColor("#EF4444")
COLOR_ORANGE = QColor("#F97316")
COLOR_TEXT_MAIN = QColor("#1F2937")
COLOR_TEXT_MUTED = QColor("#6B7280")
COLOR_SHELF = QColor("#64748B")
COLOR_CUSTOMER = QColor("#EC4899")
COLOR_CASHIER = QColor("#F59E0B")
COLOR_CHECKOUT = QColor("#3B82F6")
COLOR_WAITING_AREA = QColor(59, 130, 246, 40)
COLOR_START_AREA = QColor(16, 185, 129, 40)
COLOR_EXIT_AREA = QColor(239, 68, 68, 40)
COLOR_SELECTION = QColor("#EF4444")
COLOR_QUEUE_HIGHLIGHT = QColor("#8B5CF6")
COLOR_SCAN_PROGRESS = QColor("#10B981")
COLOR_WALL = QColor("#374151")
COLOR_FLOOR = QColor("#E5E7EB")
COLOR_GRID = QColor("#D1D5DB")

# Aliases
COLOR_GREEN = COLOR_SUCCESS
COLOR_RED = COLOR_ERROR
COLOR_BLUE = COLOR_ACCENT
COLOR_DARK_TEXT = COLOR_TEXT_MAIN
COLOR_LIGHT_BG = COLOR_BG_MAIN
COLOR_WHITE_BG = COLOR_BG_PANEL

# --- Constants ---
SHELF_SIZE = 32
CUSTOMER_SIZE = 32
# HIER GEÄNDERT: Von 45 auf 55 für noch bessere Sichtbarkeit
CASHIER_SIZE = 55
CHECKOUT_WIDTH = 100
CHECKOUT_HEIGHT = 100

# --- TIME & PHYSICS ---
ANIMATION_TICK_MS = 33
FACTOR_1X = 60.0
FACTOR_2X = 120.0
FACTOR_6X = 360.0
WALK_SPEED_PPS = 2.5
WALK_SPEED_DISABLED_FACTOR = 0.6
DEFAULT_OPEN_TIME = (8, 0)
DEFAULT_CLOSE_TIME = (20, 0)
SHELF_PROBABILITY = 0.6
ITEM_PICK_PROBABILITY = 0.7
QUEUE_SPACING = 36
SCAN_TIME_PER_ITEM_MS = 15000

# --- DYNAMIC IMAGE LISTS ---
IMG_CUSTOMERS_NORMAL = get_image_files("kunde")
IMG_CUSTOMERS_DISABLED = get_image_files("behindert")
IMG_SHELVES = get_image_files("regal")
IMG_CASHIERS = get_image_files("verkäufer") 

# Pfade für spezifische Typen
PATH_AZUBI = ASSETS_DIR / "azubi.png"
if not PATH_AZUBI.exists():
    PATH_AZUBI = IMAGE_DIR / "azubi.png"

PATH_PRO = ASSETS_DIR / "festangestellter.png" 
if not PATH_PRO.exists():
    PATH_PRO = IMAGE_DIR / "festangestellter.png"

DEFAULT_SETTINGS = {
    "show_routes": False,
    "show_shelves": False,
    "show_checkouts": True,
    "show_cashiers": True,
    "show_waiting_area": True,
    "show_start_area": True,
    "customer_path_offset": 10,
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
    "size_customer": CUSTOMER_SIZE,
    "size_shelf": SHELF_SIZE,
    "size_cashier": CASHIER_SIZE,
    "size_checkout_width": CHECKOUT_WIDTH,
    "size_checkout_height": CHECKOUT_HEIGHT,
}