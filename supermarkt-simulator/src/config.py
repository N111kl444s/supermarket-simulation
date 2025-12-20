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

# --- WINDOW ---
# Added to prevent crashes if main.py references them
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800

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
COLOR_WAITING_AREA = QColor(59, 130, 246, 40)  # Blue-ish transparent
COLOR_START_AREA = QColor(16, 185, 129, 40)  # Green-ish transparent
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

# --- TIME & PHYSICS ---
# Animation Loop (Fixed 30 FPS)
ANIMATION_TICK_MS = 33

# Time Factors (1 Real-Sec = X Game-Seconds)
# 1x: 1 Real-Sek = 1 Game-Min (60s)
FACTOR_1X = 60.0
# 2x: 1 Real-Sek = 2 Game-Min (120s)
FACTOR_2X = 120.0
# 6x: 1 Real-Sek = 6 Game-Min (360s) -> 10 Real-Sek = 1 Game-Std
FACTOR_6X = 360.0

# Walking Speed in Pixels per Game-Second
# 2.5 px * 60 (1x) = 150px/sec (Realzeit) -> Angenehm
WALK_SPEED_PPS = 2.5

DEFAULT_OPEN_TIME = (8, 0)
DEFAULT_CLOSE_TIME = (20, 0)

# Initiale Geschwindigkeit
SPEED_1 = FACTOR_1X
SPEED_2 = FACTOR_2X
SPEED_3 = FACTOR_6X

SHELF_PROBABILITY = 0.6
ITEM_PICK_PROBABILITY = 0.7
QUEUE_SPACING = 18
# Scanning Duration: 15 Game-Seconds per Item
SCAN_TIME_PER_ITEM_MS = 15000

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
}
