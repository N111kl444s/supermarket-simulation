# src/model/entities.py

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List, Tuple


class CashierType(Enum):
    NORMAL = "Normal"
    SELF_SERVICE = "SB"


class CustomerStatus(Enum):
    SPAWNING = auto()
    WALKING_TO_SHELF = auto()  # (Vorbereitung für Route)
    SHOPPING = auto()
    IN_QUEUE = auto()
    SCANNING = auto()  # Wichtig für die Animation
    DONE = auto()


@dataclass
class Customer:
    """
    Data model for a customer including precise state for visualization.
    """

    id: int
    arrival_time: float

    # Inventory Logic
    total_items: int
    scanned_items: int = 0

    # Position & Movement
    x: float = 0.0
    y: float = 0.0
    target_x: float = 0.0
    target_y: float = 0.0

    # State
    status: CustomerStatus = CustomerStatus.SPAWNING
    target_lane_id: Optional[int] = None

    # For Statistics
    start_service_time: Optional[float] = None
    end_service_time: Optional[float] = None

    @property
    def remaining_items(self) -> int:
        return max(0, self.total_items - self.scanned_items)

    @property
    def scan_progress_pct(self) -> float:
        """Returns progress 0.0 to 1.0"""
        if self.total_items == 0:
            return 1.0
        return self.scanned_items / self.total_items


@dataclass
class CheckoutLane:
    """
    Data model for a checkout counter.
    """

    id: int
    type: CashierType
    x: float
    y: float
    orientation: str = "Right"  # "Left" or "Right"
    is_open: bool = True
    items_per_minute: float = 30.0
