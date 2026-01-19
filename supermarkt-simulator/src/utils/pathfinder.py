"""
Pathfinder Utility.
Implements A* Algorithm on a grid to avoid obstacles.
Updated: Added 'get_closest_walkable' to prevent walking INTO obstacles.
"""

import heapq
import math
from PyQt6.QtCore import QPointF, QRectF


class Pathfinder:
    def __init__(self, width=3000, height=3000, cell_size=25):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.cols = math.ceil(width / cell_size)
        self.rows = math.ceil(height / cell_size)
        self.grid = set()  # Set of blocked (col, row) tuples

    def clear(self):
        self.grid.clear()

    def add_obstacle(self, rect: QRectF):
        """Marks the grid cells covered by the rect as blocked."""
        # Buffer slightly reduced to allow walking near objects
        buffer = 5
        start_col = max(0, int((rect.left() - buffer) / self.cell_size))
        end_col = min(
            self.cols, int((rect.right() + buffer) / self.cell_size) + 1
        )
        start_row = max(0, int((rect.top() - buffer) / self.cell_size))
        end_row = min(
            self.rows, int((rect.bottom() + buffer) / self.cell_size) + 1
        )

        for c in range(start_col, end_col):
            for r in range(start_row, end_row):
                self.grid.add((c, r))

    def is_blocked(self, col, row):
        return (col, row) in self.grid

    def get_closest_walkable(self, target: QPointF):
        """
        If target is inside an obstacle, find the nearest free cell.
        Returns the original point if it's free.
        """
        tc = int(target.x() / self.cell_size)
        tr = int(target.y() / self.cell_size)

        if not self.is_blocked(tc, tr):
            return target

        # Spiral search for nearest free cell
        # Limit radius to avoid infinite loops in full blockages
        for r in range(1, 10):
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    # Only check the outer ring of the current radius
                    if abs(dx) != r and abs(dy) != r:
                        continue

                    nc, nr = tc + dx, tr + dy
                    if 0 <= nc < self.cols and 0 <= nr < self.rows:
                        if not self.is_blocked(nc, nr):
                            # Found a free cell!
                            return QPointF(
                                nc * self.cell_size + self.cell_size / 2,
                                nr * self.cell_size + self.cell_size / 2,
                            )

        # Fallback: Return original (customer might clip, but better than crash)
        return target

    def find_path(self, start_pos: QPointF, end_pos: QPointF):
        """
        Returns a list of QPointF waypoints from start to end avoiding obstacles.
        Uses A* Algorithm.
        """
        start_cell = (
            int(start_pos.x() / self.cell_size),
            int(start_pos.y() / self.cell_size),
        )
        end_cell = (
            int(end_pos.x() / self.cell_size),
            int(end_pos.y() / self.cell_size),
        )

        # A* Setup
        open_set = []
        heapq.heappush(open_set, (0, start_cell))
        came_from = {}
        g_score = {start_cell: 0}
        f_score = {start_cell: self._heuristic(start_cell, end_cell)}

        found = False
        iterations = 0
        max_iterations = 3000  # Limit to prevent lag

        while open_set:
            iterations += 1
            if iterations > max_iterations:
                break

            current = heapq.heappop(open_set)[1]

            if current == end_cell:
                found = True
                break

            for neighbor in self._get_neighbors(current):
                tentative_g = g_score[current] + self._dist(current, neighbor)

                if tentative_g < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f = tentative_g + self._heuristic(neighbor, end_cell)
                    f_score[neighbor] = f
                    heapq.heappush(open_set, (f, neighbor))

        if found:
            path = []
            curr = end_cell
            while curr in came_from:
                pt = QPointF(
                    curr[0] * self.cell_size + self.cell_size / 2,
                    curr[1] * self.cell_size + self.cell_size / 2,
                )
                path.append(pt)
                curr = came_from[curr]

            path.reverse()
            # Smooth: replace first grid point with actual start, append actual end
            final_path = [start_pos] + path
            # Note: We don't append end_pos strictly if we want to stay on grid,
            # but usually it's fine.
            return final_path
        else:
            return [start_pos, end_pos]

    def _heuristic(self, a, b):
        return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

    def _dist(self, a, b):
        return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

    def _get_neighbors(self, cell):
        c, r = cell
        neighbors = []
        dirs = [
            (0, 1),
            (0, -1),
            (1, 0),
            (-1, 0),
            (1, 1),
            (1, -1),
            (-1, 1),
            (-1, -1),
        ]

        for dc, dr in dirs:
            nc, nr = c + dc, r + dr
            if 0 <= nc < self.cols and 0 <= nr < self.rows:
                # SPECIAL: If current cell is blocked (stuck inside), allow moving OUT to any neighbor
                # Otherwise, normal check
                is_stuck = self.is_blocked(c, r)

                if is_stuck:
                    # If stuck, we can move anywhere (heuristic will guide us out)
                    neighbors.append((nc, nr))
                elif not self.is_blocked(nc, nr):
                    neighbors.append((nc, nr))
        return neighbors
