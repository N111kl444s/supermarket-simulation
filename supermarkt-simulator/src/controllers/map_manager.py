"""
Map Manager Module.
Handles loading, saving, and managing map data.
Updated:
- Integrates Pathfinder for collision avoidance.
- Helper to find shelves by variant.
"""

import json
import os
import shutil
from pathlib import Path
from PyQt6.QtCore import QPointF, QRectF
from config import MAPS_DIR, SHELF_SIZE, CHECKOUT_WIDTH, CHECKOUT_HEIGHT
from utils.pathfinder import Pathfinder


class MapManager:
    def __init__(self):
        self.current_map_file = None

        self.shop_routes = {}
        self.start_routes = {}
        self.exit_routes = {}
        self.all_shelves = []
        self.checkouts_data = []

        self.waiting_area_rect = None
        self.start_area_rect = None
        self.exit_area_rect = None

        self.background_image_path = None
        self.background_scale = 0.5

        self.map_pos_x = 0.0
        self.map_pos_y = 0.0

        # NEU: Pathfinder
        self.pathfinder = Pathfinder(width=4000, height=3000, cell_size=25)

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
                    self.all_shelves.append(s)
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

            self.background_image_path = data.get("background_image", None)
            self.background_scale = data.get("background_scale", 0.5)

            self.map_pos_x = data.get("map_pos_x", 0.0)
            self.map_pos_y = data.get("map_pos_y", 0.0)

            # NEU: Hindernisse für Pathfinder aufbauen
            self._rebuild_collision_map()

            return True, data.get("global_exit_direction", "Rechts")
        except Exception as e:
            print(f"Error loading map: {e}")
            return False, "Rechts"

    def _rebuild_collision_map(self):
        self.pathfinder.clear()

        # 1. Regale
        for s in self.all_shelves:
            # Annahme: x,y ist Center
            x, y = s.get("x", 0), s.get("y", 0)
            # Einfache Bounding Box (Rotation ignorieren wir für das Grid grob, nehmen max Ausdehnung)
            # SHELF_SIZE ist quadratisch, also passt das.
            rect = QRectF(
                x - SHELF_SIZE / 2, y - SHELF_SIZE / 2, SHELF_SIZE, SHELF_SIZE
            )
            self.pathfinder.add_obstacle(rect)

        # 2. Kassen
        for c in self.checkouts_data:
            x, y = c.get("x", 0), c.get("y", 0)
            w, h = CHECKOUT_WIDTH, CHECKOUT_HEIGHT
            # Rotation beachten? Wir nehmen einfach eine "Safe Box" an.
            # Wenn 90 Grad rotiert, tauschen sich W und H, aber das Grid ist grob genug.
            # Wir blockieren einfach das Zentrum großzügig.
            rect = QRectF(
                x - w / 2 + 10, y - h / 2 + 10, w - 20, h - 20
            )  # Etwas kleiner als Bild, damit man nah ran kann
            self.pathfinder.add_obstacle(rect)

    def get_shelves_by_variant(self):
        """Returns a dict {variant_id: [shelf_data, ...]}"""
        grouped = {}
        for s in self.all_shelves:
            v = s.get("variant", 1)
            if v not in grouped:
                grouped[v] = []
            grouped[v].append(s)
        return grouped

    def save_map(self, global_exit_direction="Rechts"):
        if not self.current_map_file:
            return False

        def export_routes(routes_dict):
            return {
                name: [[p.x(), p.y()] for p in pts]
                for name, pts in routes_dict.items()
            }

        data = {
            "routes": export_routes(self.shop_routes),
            "start_routes": export_routes(self.start_routes),
            "exit_routes": export_routes(self.exit_routes),
            "shelves": self.all_shelves,
            "checkouts": self.checkouts_data,
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
        default_data = {"routes": {}, "shelves": [], "checkouts": []}
        try:
            with open(path, "w") as f:
                json.dump(default_data, f, indent=4)
            return name
        except Exception:
            return None

    def delete_current_map(self):
        if (
            not self.current_map_file
            or self.current_map_file.name == "default.json"
        ):
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
            maps = ["default.json"]
        return maps

    def _create_default_map(self):
        default_data = {"routes": {}, "shelves": [], "checkouts": []}
        with open(MAPS_DIR / "default.json", "w") as f:
            json.dump(default_data, f, indent=4)

    def set_background(self, source_path):
        if not self.current_map_file:
            return False
        src = Path(source_path)
        dest_name = f"bg_{self.current_map_file.stem}{src.suffix}"
        dest_path = MAPS_DIR / dest_name
        try:
            shutil.copy(src, dest_path)
            self.background_image_path = dest_name
            self.background_scale = 0.5
            return True
        except Exception:
            return False
