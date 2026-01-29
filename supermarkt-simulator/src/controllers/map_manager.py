"""
Map Manager Module.
Handles loading, saving, and managing map data.
Updated: Defaults to 'Standard (Einfach).json'. Added worker_spawn_rect.
"""

import json
import os
import shutil
from pathlib import Path
from PyQt6.QtCore import QPointF, QRectF
from config import MAPS_DIR


class MapManager:
    def __init__(self, settings):
        self.settings = settings
        self.current_map_file = None

        self.shop_routes = {}
        self.start_routes = {}
        self.exit_routes = {}
        self.all_shelves = []
        self.checkouts_data = []

        self.waiting_area_rect = None
        self.start_area_rect = None
        self.exit_area_rect = None
        self.worker_spawn_rect = None  # NEU: Spawn-Bereich für Arbeiter

        self.background_image_path = None
        self.background_scale = 0.09
        self.default_background_image = self._get_default_background_image()

        self.map_pos_x = 0.0
        self.map_pos_y = 0.0

        self._ensure_maps_dir()

    def _ensure_maps_dir(self):
        if not MAPS_DIR.exists():
            os.makedirs(MAPS_DIR)

    def load_map(self, map_name):
        file_path = MAPS_DIR / map_name
        if not file_path.exists():
            return False, "Rechts"

        self.current_map_file = file_path
        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            def load_routes(key):
                res = {}
                if key in data:
                    raw = data[key]
                    if isinstance(raw, dict):
                        for name, pts in raw.items():
                            res[name] = [QPointF(p[0], p[1]) for p in pts]
                    elif isinstance(raw, list):
                        res["Route_Legacy"] = [
                            QPointF(p[0], p[1]) for p in raw
                        ]
                return res

            self.shop_routes = load_routes("routes")
            self.start_routes = load_routes("start_routes")
            self.exit_routes = load_routes("exit_routes")

            raw_shelves = data.get("shelves", [])
            self.all_shelves = []
            for s in raw_shelves:
                if isinstance(s, dict):
                    self.all_shelves.append(
                        {
                            "x": s.get("x", 0),
                            "y": s.get("y", 0),
                            "angle": s.get("angle", 0),
                            "variant": s.get("variant", 0),
                            "mirrored": s.get("mirrored", False),
                        }
                    )
                elif isinstance(s, list):
                    self.all_shelves.append(
                        {
                            "x": s[0],
                            "y": s[1],
                            "angle": 0,
                            "variant": 0,
                            "mirrored": False,
                        }
                    )

            self.checkouts_data = data.get("checkouts", [])

            # Areas
            self.waiting_area_rect = (
                QRectF(*data["waiting_area"])
                if data.get("waiting_area")
                else None
            )
            self.start_area_rect = (
                QRectF(*data["start_area"]) if data.get("start_area") else None
            )
            self.exit_area_rect = (
                QRectF(*data["exit_area"]) if data.get("exit_area") else None
            )
            # NEU: Worker Area laden
            self.worker_spawn_rect = (
                QRectF(*data["worker_area"])
                if data.get("worker_area")
                else None
            )

            self.background_image_path = data.get("background_image", None)
            self.background_scale = data.get("background_scale", 0.09)
            if not self.background_image_path:
                self._apply_default_background()

            self.map_pos_x = data.get("map_pos_x", 0.0)
            self.map_pos_y = data.get("map_pos_y", 0.0)

            return True, data.get("global_exit_direction", "Rechts")
        except Exception as e:
            print(f"Error loading map: {e}")
            return False, "Rechts"

    def save_map(self, global_exit_direction="Rechts"):
        if not self.current_map_file:
            return False

        def export_routes(routes_dict):
            return {
                name: [[p.x(), p.y()] for p in pts]
                for name, pts in routes_dict.items()
            }

        def rect_to_list(r):
            return [r.x(), r.y(), r.width(), r.height()] if r else None

        data = {
            "routes": export_routes(self.shop_routes),
            "start_routes": export_routes(self.start_routes),
            "exit_routes": export_routes(self.exit_routes),
            "shelves": self.all_shelves,
            "checkouts": self.checkouts_data,
            "waiting_area": rect_to_list(self.waiting_area_rect),
            "start_area": rect_to_list(self.start_area_rect),
            "exit_area": rect_to_list(self.exit_area_rect),
            "worker_area": rect_to_list(self.worker_spawn_rect),  # NEU
            "global_exit_direction": global_exit_direction,
            "background_image": self.background_image_path,
            "background_scale": self.background_scale,
            "map_pos_x": self.map_pos_x,
            "map_pos_y": self.map_pos_y,
        }
        try:
            with open(self.current_map_file, "w") as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            print(f"Fehler beim Speichern: {e}")
            return False

    def create_new_map(self, name):
        if not name.endswith(".json"):
            name += ".json"
        path = MAPS_DIR / name
        default_bg = self._get_default_background_image()
        default_data = {
            "routes": {},
            "shelves": [],
            "checkouts": [],
            "background_image": default_bg,
            "background_scale": 0.09,
        }
        try:
            with open(path, "w") as f:
                json.dump(default_data, f, indent=4)
            return name
        except Exception:
            return None

    def delete_current_map(self):
        if not self.current_map_file:
            return False
        try:
            os.remove(self.current_map_file)
            self.current_map_file = None
            return True
        except Exception:
            return False

    def get_available_maps(self):
        maps = sorted([f.name for f in MAPS_DIR.glob("*.json")])
        if not maps:
            self._create_default_map()
            maps = ["Standard 1.json"]
        return maps

    def _create_default_map(self):
        default_name = "Standard 1.json"
        default_data = {"routes": {}, "shelves": [], "checkouts": []}
        try:
            with open(MAPS_DIR / default_name, "w") as f:
                json.dump(default_data, f, indent=4)
        except:
            pass

    def reset_map(self):
        self.shop_routes = {}
        self.start_routes = {}
        self.exit_routes = {}
        self.all_shelves = []
        self.checkouts_data = []
        self.waiting_area_rect = None
        self.start_area_rect = None
        self.exit_area_rect = None
        self.worker_spawn_rect = None
        self.background_image_path = self._get_default_background_image()
        self.background_scale = 0.09

    def set_background(self, source_path):
        if not self.current_map_file:
            return False
        src = Path(source_path)
        dest_name = f"bg_{self.current_map_file.stem}{src.suffix}"
        dest_path = MAPS_DIR / dest_name
        try:
            shutil.copy(src, dest_path)
            self.background_image_path = dest_name
            self.background_scale = 0.09
            return True
        except Exception:
            return False

    def _get_default_background_image(self):
        preferred = MAPS_DIR / "bg_Standard 1.png"
        if preferred.exists():
            return preferred.name
        for p in MAPS_DIR.glob("bg_*.png"):
            return p.name
        return None

    def _apply_default_background(self):
        default_bg = self._get_default_background_image()
        if default_bg:
            self.background_image_path = default_bg
            self.background_scale = 0.09
