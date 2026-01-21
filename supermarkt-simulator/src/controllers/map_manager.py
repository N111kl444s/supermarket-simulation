"""
Map Manager.
Refactored:
- Manages shelves, routes, checkouts, and special areas.
- FIX: Fallback support for legacy JSON keys (routes vs routes_shop).
- FIX: JSON Key Mismatch fixed (background_image vs bg_image).
"""

import json
import shutil
from pathlib import Path
from PyQt6.QtCore import QPointF, QRectF
from config import MAPS_DIR


class MapManager:
    def __init__(self, scene, visual_ctrl):
        self.scene = scene
        self.visual_ctrl = visual_ctrl

        self.current_map_file = None

        self.map_pos_x = 0.0
        self.map_pos_y = 0.0

        self.bg_image_name = None
        self.background_image_path = None
        self.bg_scale = 1.0
        self.background_scale = 1.0

        self.all_shelves = []
        self.checkouts_data = []

        self.shop_routes = {}
        self.start_routes = {}
        self.exit_routes = {}
        self.maintenance_routes = {}

        self.start_area_rect = None
        self.exit_area_rect = None
        self.waiting_area_rect = None
        self.worker_spawn_pos = None

    # --- FILE OPERATIONS ---

    def get_available_maps(self):
        if not MAPS_DIR.exists():
            return []
        return [f.name for f in MAPS_DIR.glob("*.json")]

    def create_new_map(self, name):
        filename = name if name.lower().endswith(".json") else f"{name}.json"
        path = MAPS_DIR / filename
        self.new_map()
        self.current_map_file = path
        self.save_map("Right")
        return filename

    def delete_current_map(self):
        if self.current_map_file and self.current_map_file.exists():
            try:
                self.current_map_file.unlink()
                self.new_map()
                self.current_map_file = None
                return True
            except Exception as e:
                print(f"Error deleting map: {e}")
        return False

    def set_background(self, file_path):
        src = Path(file_path)
        if not src.exists():
            return False
        dest_name = src.name
        dest = MAPS_DIR / dest_name
        try:
            if src != dest:
                shutil.copy2(src, dest)
            self.bg_image_name = dest_name
            self.background_image_path = dest_name
            self.visual_ctrl.update_background(
                dest_name, self.bg_scale, MAPS_DIR
            )
            return True
        except Exception as e:
            print(f"Error setting background: {e}")
            return False

    # --- DATA MANAGEMENT ---

    def new_map(self):
        self.all_shelves.clear()
        self.checkouts_data.clear()
        self.shop_routes.clear()
        self.start_routes.clear()
        self.exit_routes.clear()
        self.maintenance_routes.clear()

        self.start_area_rect = None
        self.exit_area_rect = None
        self.waiting_area_rect = None
        self.worker_spawn_pos = None

        self.bg_image_name = None
        self.background_image_path = None
        self.bg_scale = 1.0
        self.background_scale = 1.0
        self.map_pos_x = 0.0
        self.map_pos_y = 0.0
        self.current_map_file = None

        self.visual_ctrl.update_background(None, 1.0, MAPS_DIR)
        self.refresh_visuals()

    def save_map(self, global_exit_dir="Right"):
        if not self.current_map_file:
            self.current_map_file = MAPS_DIR / "untitled.json"

        data = {
            "version": 1.3,
            "background_image": self.bg_image_name,
            "background_scale": self.bg_scale,
            "map_pos_x": self.map_pos_x,
            "map_pos_y": self.map_pos_y,
            "global_exit_direction": global_exit_dir,
            "shelves": self.all_shelves,
            "checkouts": self.checkouts_data,
            "start_area": (
                [
                    self.start_area_rect.x(),
                    self.start_area_rect.y(),
                    self.start_area_rect.width(),
                    self.start_area_rect.height(),
                ]
                if self.start_area_rect
                else None
            ),
            "exit_area": (
                [
                    self.exit_area_rect.x(),
                    self.exit_area_rect.y(),
                    self.exit_area_rect.width(),
                    self.exit_area_rect.height(),
                ]
                if self.exit_area_rect
                else None
            ),
            "waiting_area": (
                [
                    self.waiting_area_rect.x(),
                    self.waiting_area_rect.y(),
                    self.waiting_area_rect.width(),
                    self.waiting_area_rect.height(),
                ]
                if self.waiting_area_rect
                else None
            ),
            "routes_shop": self._serialize_routes(self.shop_routes),
            "routes_start": self._serialize_routes(self.start_routes),
            "routes_exit": self._serialize_routes(self.exit_routes),
            "routes_maintenance": self._serialize_routes(
                self.maintenance_routes
            ),
            "worker_spawn": (
                [self.worker_spawn_pos.x(), self.worker_spawn_pos.y()]
                if self.worker_spawn_pos
                else None
            ),
        }

        try:
            with open(self.current_map_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving map: {e}")
            return False

    def load_map(self, filename):
        path = MAPS_DIR / filename
        if not path.exists():
            return False, "Right"

        self.current_map_file = path

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.new_map()
            self.current_map_file = path

            self.bg_image_name = data.get("background_image") or data.get(
                "bg_image"
            )
            self.background_image_path = self.bg_image_name

            self.bg_scale = data.get("background_scale") or data.get(
                "bg_scale", 1.0
            )
            self.background_scale = self.bg_scale

            self.map_pos_x = data.get("map_pos_x", 0.0)
            self.map_pos_y = data.get("map_pos_y", 0.0)

            self.visual_ctrl.update_background(
                self.bg_image_name, self.bg_scale, MAPS_DIR
            )

            self.all_shelves = data.get("shelves", [])
            self.checkouts_data = data.get("checkouts", [])

            s = data.get("start_area")
            if s:
                self.start_area_rect = QRectF(*s)
            e = data.get("exit_area")
            if e:
                self.exit_area_rect = QRectF(*e)
            w = data.get("waiting_area")
            if w:
                self.waiting_area_rect = QRectF(*w)

            w_spawn = data.get("worker_spawn")
            if w_spawn:
                self.worker_spawn_pos = QPointF(w_spawn[0], w_spawn[1])

            # FIX: Fallback für 'routes' vs 'routes_shop'
            self.shop_routes = self._deserialize_routes(
                data.get("routes_shop") or data.get("routes", {})
            )
            self.start_routes = self._deserialize_routes(
                data.get("routes_start", {})
            )
            self.exit_routes = self._deserialize_routes(
                data.get("routes_exit", {})
            )
            self.maintenance_routes = self._deserialize_routes(
                data.get("routes_maintenance", {})
            )

            self.refresh_visuals()

            exit_dir = data.get("global_exit_direction") or data.get(
                "global_exit", "Right"
            )
            return True, exit_dir

        except Exception as e:
            print(f"Error loading map: {e}")
            return False, "Right"

    def refresh_visuals(self):
        self.visual_ctrl.draw_map_elements(self)

    def _serialize_routes(self, routes_dict):
        out = {}
        for name, pts in routes_dict.items():
            out[name] = [[p.x(), p.y()] for p in pts]
        return out

    def _deserialize_routes(self, raw_dict):
        out = {}
        for name, raw_pts in raw_dict.items():
            out[name] = [QPointF(p[0], p[1]) for p in raw_pts]
        return out
