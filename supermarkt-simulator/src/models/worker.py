"""
Worker logic (Maintenance).
"""

import math
import random
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QVector2D

class WorkerModel:
    def __init__(self, spawn_pos, maintenance_routes):
        self.pos = QPointF(spawn_pos) if spawn_pos else QPointF(0,0)
        self.home_pos = QPointF(self.pos)
        self.routes = maintenance_routes # Dict of routes
        
        self.state = "IDLE" # IDLE, WALKING_TO_JOB, WORKING, RETURNING
        self.target_checkout_id = None
        self.target_pos = None
        self.path = []
        
        self.speed = 1.8 # etwas langsamer als Kunden
        self.work_timer = 0.0
        self.work_duration = 5.0
        self.angle = 0.0
        
    def assign_job(self, checkout_id, checkout_pos, duration_min, duration_max):
        """Weist dem Arbeiter eine Reparatur zu."""
        self.target_checkout_id = checkout_id
        self.work_duration = random.uniform(duration_min, duration_max)
        
        # 1. Pfad planen: Home -> Route -> Checkout
        self.path = self._calculate_path_to(checkout_pos)
        if self.path:
            self.target_pos = self.path.pop(0)
            self.state = "WALKING_TO_JOB"
        else:
            # Fallback: Direkt teleportieren/laufen wenn keine Route
            self.target_pos = checkout_pos
            self.state = "WALKING_TO_JOB"

    def tick(self, dt):
        if self.state == "IDLE":
            return
            
        elif self.state == "WALKING_TO_JOB":
            dist = self._move(dt)
            if dist < 5.0:
                if self.path:
                    self.target_pos = self.path.pop(0)
                else:
                    self.state = "WORKING"
                    self.work_timer = 0.0
                    
        elif self.state == "WORKING":
            self.work_timer += dt
            if self.work_timer >= self.work_duration:
                # Fertig
                self.state = "RETURNING"
                # Rückweg berechnen (einfach Home)
                # Man könnte Route rückwärts laufen, hier vereinfacht:
                self.path = [self.home_pos] 
                self.target_pos = self.path.pop(0)
                return True # Job finished signal
                
        elif self.state == "RETURNING":
            dist = self._move(dt)
            if dist < 5.0:
                if self.path:
                    self.target_pos = self.path.pop(0)
                else:
                    self.state = "IDLE"
                    self.target_checkout_id = None
                    
        return False

    def _move(self, dt):
        if not self.target_pos: return 0.0
        vec = QVector2D(self.target_pos - self.pos)
        dist = vec.length()
        if dist > 0:
            direction = vec.normalized()
            self.angle = math.degrees(math.atan2(direction.y(), direction.x()))
            move = self.speed * dt
            if move >= dist:
                self.pos = self.target_pos
                return 0.0
            else:
                self.pos = self.pos + (direction * move).toPointF()
                return dist - move
        return 0.0

    def _calculate_path_to(self, target):
        """Einfache Wegfindung: Finde nächste Route und biege dann ab."""
        # Vereinfachung: Nimm die erste Wartungsroute und lauf sie ab bis man nah am Ziel ist
        # Ideal wäre echter A*, aber für den Simulator reicht oft:
        # Start -> Route Start -> Route End -> Target
        
        path = []
        if self.routes:
            # Nimm erste verfügbare Route als "Hauptverkehrsader"
            route_pts = list(self.routes.values())[0]
            # Kopie der Punkte
            path.extend([QPointF(p) for p in route_pts])
            
        path.append(QPointF(target))
        return path