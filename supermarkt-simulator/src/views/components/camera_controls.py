"""
Camera Controls for TopToolbar.
Handles camera position switching and saving.
"""

import json
from pathlib import Path
from PyQt6.QtCore import QPoint, Qt

# Default camera positions file
CAMERA_POSITIONS_FILE = (
    Path(__file__).parent.parent.parent / "camera_positions.json"
)


def get_default_positions():
    """Get default camera positions for a map."""
    return {
        "full_store": {"x": 0, "y": 0, "zoom": 1.0},
        "entrance": {"x": 400, "y": 200, "zoom": 2.0},
        "sales_area": {"x": 800, "y": 400, "zoom": 2.5},
        "checkout_normal": {"x": 1200, "y": 600, "zoom": 3.0},
        "checkout_sb": {"x": 1200, "y": 800, "zoom": 3.0},
    }


def initialize_camera_positions():
    """Initialize camera positions file with default values."""
    default_positions = {"default": get_default_positions()}

    if not CAMERA_POSITIONS_FILE.exists():
        CAMERA_POSITIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CAMERA_POSITIONS_FILE, "w") as f:
            json.dump(default_positions, f, indent=2)

    return default_positions


def load_camera_positions(map_name="default"):
    """Load camera positions from JSON file."""
    try:
        if CAMERA_POSITIONS_FILE.exists():
            with open(CAMERA_POSITIONS_FILE, "r") as f:
                data = json.load(f)
                if map_name in data:
                    return data[map_name]
    except Exception as e:
        print(f"Error loading camera positions: {e}")

    # Return default positions if map not found
    return get_default_positions()


def save_camera_positions(positions, map_name="default"):
    """Save camera positions to JSON file."""
    try:
        data = {}
        if CAMERA_POSITIONS_FILE.exists():
            with open(CAMERA_POSITIONS_FILE, "r") as f:
                data = json.load(f)

        data[map_name] = positions

        with open(CAMERA_POSITIONS_FILE, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving camera positions: {e}")
        return False


# Add these methods to TopToolbar class
def setup_camera_controls(self):
    """Initialize camera control methods."""
    self.current_map = "default"


def show_camera_menu(self):
    """Show the camera position menu."""
    self.camera_menu.exec_(
        self.btn_reset_zoom.mapToGlobal(
            QPoint(0, self.btn_reset_zoom.height())
        )
    )


def set_camera_position(self, position_name):
    """Set camera to a predefined position."""
    canvas = self.get_canvas()
    if not canvas:
        return

    positions = load_camera_positions(self.current_map)
    position = positions.get(position_name)

    if position:
        canvas.zoom_level = position.get("zoom", 1.0)
        canvas.resetTransform()
        canvas.scale(canvas.zoom_level, canvas.zoom_level)

        center_x = position.get("x", 0)
        center_y = position.get("y", 0)
        canvas.centerOn(center_x, center_y)


def set_camera_full_store(self):
    """Set camera to full store view."""
    self.set_camera_position("full_store")


def set_camera_entrance(self):
    """Set camera to entrance area."""
    self.set_camera_position("entrance")


def set_camera_sales_area(self):
    """Set camera to sales area."""
    self.set_camera_position("sales_area")


def set_camera_checkout_normal(self):
    """Set camera to checkout area - normal."""
    self.set_camera_position("checkout_normal")


def set_camera_checkout_sb(self):
    """Set camera to checkout area - self service."""
    self.set_camera_position("checkout_sb")


def save_current_camera_position(self):
    """Save current camera position and zoom."""
    canvas = self.get_canvas()
    if not canvas:
        return

    # Get current center position
    scene_rect = canvas.sceneRect()
    viewport_rect = canvas.mapToScene(canvas.viewport().rect()).boundingRect()
    center_x = viewport_rect.center().x()
    center_y = viewport_rect.center().y()

    positions = load_camera_positions(self.current_map)

    # Find which position to update based on current closest match
    # For now, update a generic "custom" position
    positions["custom"] = {
        "x": center_x,
        "y": center_y,
        "zoom": canvas.zoom_level,
    }

    if save_camera_positions(positions, self.current_map):
        print(f"Camera position saved for map: {self.current_map}")
    else:
        print("Failed to save camera position")


def get_canvas(self):
    """Get the canvas from main window."""
    try:
        mw = self.window()
        if mw and hasattr(mw, "canvas_component"):
            return mw.canvas_component
    except:
        pass
    return None


def set_current_map(self, map_name):
    """Set the current map name for camera positions."""
    self.current_map = map_name
