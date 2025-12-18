"""
Central configuration module for the supermarket simulation.
Includes a modern 'Flat Light' Color Palette and compatibility aliases.
"""

import sys
from pathlib import Path
from PyQt6.QtGui import QColor

# --- Paths ---
SCRIPT_FILE = Path(__file__).resolve()
SRC_DIR = SCRIPT_FILE.parent
BASE_DIR = SRC_DIR.parent
ASSETS_DIR = BASE_DIR / "assets"
IMAGE_DIR = ASSETS_DIR / "images"
MAPS_DIR = BASE_DIR / "maps"

# --- MODERN LIGHT PALETTE ---
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

# Simulation Objects
COLOR_SHELF = QColor("#64748B")
COLOR_CUSTOMER = QColor("#EC4899")
COLOR_CASHIER = QColor("#F59E0B")
COLOR_CHECKOUT = QColor("#3B82F6")
COLOR_WAITING_AREA = QColor(59, 130, 246, 40)
COLOR_SELECTION = QColor("#EF4444")
COLOR_QUEUE_HIGHLIGHT = QColor("#8B5CF6")
COLOR_SCAN_PROGRESS = QColor("#10B981")

# Map Colors
COLOR_WALL = QColor("#374151")
COLOR_FLOOR = QColor("#E5E7EB")
COLOR_GRID = QColor("#D1D5DB")

# --- COMPATIBILITY ALIASES ---
COLOR_GREEN = COLOR_SUCCESS
COLOR_RED = COLOR_ERROR
COLOR_BLUE = COLOR_ACCENT
COLOR_DARK_TEXT = COLOR_TEXT_MAIN
COLOR_LIGHT_BG = COLOR_BG_MAIN
COLOR_WHITE_BG = COLOR_BG_PANEL

# --- Constants ---
SHELF_SIZE = 20
CUSTOMER_SIZE = 14
CASHIER_SIZE = 14
CHECKOUT_WIDTH = 80
CHECKOUT_HEIGHT = 80

# Simulation Speeds (Timer Interval in ms)
# Lower = Faster
SPEED_1 = 100  # Normal
SPEED_2 = 50  # Fast
SPEED_3 = 20  # Turbo

DEFAULT_OPEN_TIME = (8, 0)  # 08:00
DEFAULT_CLOSE_TIME = (20, 0)  # 20:00

SIM_TICK_MS = SPEED_1  # Default start speed
SHELF_PROBABILITY = 0.4
ITEM_PICK_PROBABILITY = 0.7
WALK_SPEED = 3.0
QUEUE_SPACING = 18
SCAN_TIME_PER_ITEM_MS = 800

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
