import random
from PyQt6.QtWidgets import (
    QGraphicsObject,
    QGraphicsRectItem,
    QGraphicsEllipseItem,
    QGraphicsPathItem,
    QStyle,
)
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import (
    QPen,
    QBrush,
    QPixmap,
    QPainter,
    QFont,
    QVector2D,
    QColor,
)

from config import *


class CheckoutItem(QGraphicsObject):
    _pixmap_normal_left = None
    _pixmap_normal_right = None
    _pixmap_sb_left = None
    _pixmap_sb_right = None

    def __init__(
        self,
        x,
        y,
        c_type="Normal",
        orientation="Right",
        is_open=True,
        show_light=True,
        data_id=None,
        light_offset=(0, 0),
    ):
        super().__init__()
        self.setPos(x, y)
        self.c_type = c_type
        self.orientation = orientation
        self.is_open = is_open
        self.show_light = show_light
        self.data_id = data_id
        self.light_offset = light_offset
        self.setZValue(6)
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsSelectable, True)

        if CheckoutItem._pixmap_normal_left is None:
            p_n_l = IMAGE_DIR / "checkout_left.png"
            p_n_r = IMAGE_DIR / "checkout_right.png"
            p_s_l = IMAGE_DIR / "sb_checkout_left.png"
            p_s_r = IMAGE_DIR / "sb_checkout_right.png"
            if p_n_l.exists():
                CheckoutItem._pixmap_normal_left = QPixmap(str(p_n_l))
            if p_n_r.exists():
                CheckoutItem._pixmap_normal_right = QPixmap(str(p_n_r))
            if p_s_l.exists():
                CheckoutItem._pixmap_sb_left = QPixmap(str(p_s_l))
            if p_s_r.exists():
                CheckoutItem._pixmap_sb_right = QPixmap(str(p_s_r))

    def boundingRect(self):
        return QRectF(0, 0, CHECKOUT_WIDTH, CHECKOUT_HEIGHT)

    def paint(self, painter: QPainter, option, widget=None):
        pixmap = None
        if self.c_type == "SB":
            pixmap = (
                CheckoutItem._pixmap_sb_left
                if self.orientation == "Left"
                else CheckoutItem._pixmap_sb_right
            )
        else:
            pixmap = (
                CheckoutItem._pixmap_normal_left
                if self.orientation == "Left"
                else CheckoutItem._pixmap_normal_right
            )

        if pixmap and not pixmap.isNull():
            painter.drawPixmap(self.boundingRect().toRect(), pixmap)
        else:
            color = (
                QColor("#607D8B")
                if self.c_type == "Normal"
                else QColor("#455A64")
            )
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.drawRect(0, 0, CHECKOUT_WIDTH, CHECKOUT_HEIGHT)
            painter.setBrush(QBrush(Qt.GlobalColor.darkGray))
            painter.setPen(Qt.PenStyle.NoPen)
            if self.orientation == "Left":
                painter.drawRect(0, 0, 5, CHECKOUT_HEIGHT)
            else:
                painter.drawRect(CHECKOUT_WIDTH - 5, 0, 5, CHECKOUT_HEIGHT)

        if option.state & QStyle.StateFlag.State_Selected:
            painter.setPen(QPen(COLOR_SELECTION, 3))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(-2, -2, CHECKOUT_WIDTH + 4, CHECKOUT_HEIGHT + 4)

        if self.show_light:
            status_color = (
                Qt.GlobalColor.green if self.is_open else Qt.GlobalColor.red
            )
            painter.setBrush(QBrush(status_color))
            painter.setPen(QPen(Qt.GlobalColor.black, 1))
            lx = self.light_offset[0]
            ly = self.light_offset[1]
            painter.drawEllipse(lx, ly, 8, 8)


class ShelfItem(QGraphicsRectItem):
    def __init__(self, x, y):
        super().__init__(
            x - SHELF_SIZE / 2, y - SHELF_SIZE / 2, SHELF_SIZE, SHELF_SIZE
        )
        self.setBrush(QBrush(COLOR_SHELF))
        self.setPen(QPen(Qt.GlobalColor.black))
        self.setZValue(5)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable, True)

    def paint(self, painter, option, widget=None):
        if option.state & QStyle.StateFlag.State_Selected:
            painter.setPen(QPen(COLOR_SELECTION, 2))
        else:
            painter.setPen(QPen(Qt.GlobalColor.black))
        painter.setBrush(self.brush())
        painter.drawRect(self.rect())


class WaitingAreaItem(QGraphicsRectItem):
    def __init__(self, rect):
        super().__init__(rect)
        self.setBrush(QBrush(COLOR_WAITING_AREA))
        self.setPen(QPen(COLOR_GREEN, 2, Qt.PenStyle.DashLine))
        self.setZValue(2)


class CashierItem(QGraphicsEllipseItem):
    def __init__(self, x, y, skill):
        super().__init__(0, 0, CASHIER_SIZE, CASHIER_SIZE)
        self.setPos(x, y)
        self.setBrush(QBrush(COLOR_CASHIER))
        self.setPen(QPen(Qt.GlobalColor.black))
        self.setZValue(25)
        self.skill = skill
        self.setAcceptHoverEvents(True)

    def hoverEnterEvent(self, e):
        self.setToolTip(f"Kassierer ({self.skill})")
        super().hoverEnterEvent(e)


class CustomerItem(QGraphicsEllipseItem):
    def __init__(self, rp, sp, wr):
        super().__init__(
            -CUSTOMER_SIZE / 2,
            -CUSTOMER_SIZE / 2,
            CUSTOMER_SIZE,
            CUSTOMER_SIZE,
        )
        self.setBrush(QBrush(COLOR_CUSTOMER))
        self.setPen(QPen(Qt.GlobalColor.white))
        self.setZValue(20)
        self.setAcceptHoverEvents(True)
        self.route = rp
        self.shelves = sp
        self.waiting_area = wr
        self.state = "WALKING_ROUTE"
        self.current_waypoint_idx = 0
        self.wait_ticks = 0
        self.return_pos = None
        self.target_pos = QPointF(0, 0)
        self.assigned_checkout_id = None
        self.inventory = 0
        self.items_scanned = 0
        self.scan_progress_ticks = 0
        self.scan_ticks_total = int(SCAN_TIME_PER_ITEM_MS / SIM_TICK_MS)
        if rp:
            self.setPos(rp[0])
            self.target_pos = rp[1] if len(rp) > 1 else self.pos()

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        remaining = max(0, self.inventory - self.items_scanned)
        painter.setPen(Qt.GlobalColor.white)
        font = QFont()
        font.setPixelSize(10)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(
            self.rect(), Qt.AlignmentFlag.AlignCenter, str(remaining)
        )
        if self.state == "SCANNING":
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(COLOR_SCAN_PROGRESS, 2))
            angle = (
                (self.scan_progress_ticks / self.scan_ticks_total) * 360 * 16
            )
            rect = self.rect().adjusted(-2, -2, 2, 2)
            painter.drawArc(rect, 90 * 16, -int(angle))

    def hoverEnterEvent(self, event):
        self.setToolTip(f"Kunde\nItems: {self.inventory}")
        super().hoverEnterEvent(event)

    def tick(self):
        if self.state == "SCANNING":
            self.process_scanning()
            return
        if self.state == "LEAVING":
            self.moveBy(0, -WALK_SPEED)
            if self.y() < -50:
                self.state = "GONE"
            return
        if self.state == "IN_QUEUE":
            dist = (
                QVector2D(self.target_pos) - QVector2D(self.pos())
            ).length()
            if dist > 1.0:
                self.move_towards_target()
            return
        if self.state == "FINISHED_SHOPPING":
            self.wait_ticks -= 1
            if self.wait_ticks <= 0:
                self.new_wait_target()
            self.move_towards_target()
            return
        if self.state == "WAITING_AT_SHELF":
            self.wait_ticks -= 1
            if self.wait_ticks <= 0:
                self.state = "RETURNING_TO_ROUTE"
                self.target_pos = self.return_pos
            return
        self.move_towards_target()

    def process_scanning(self):
        if self.items_scanned < self.inventory:
            self.scan_progress_ticks += 1
            if self.scan_progress_ticks >= self.scan_ticks_total:
                self.items_scanned += 1
                self.scan_progress_ticks = 0
                self.update()
        else:
            self.state = "LEAVING"
        self.update()

    def new_wait_target(self):
        if self.waiting_area:
            self.target_pos = QPointF(
                random.uniform(
                    self.waiting_area.left(), self.waiting_area.right()
                ),
                random.uniform(
                    self.waiting_area.top(), self.waiting_area.bottom()
                ),
            )
            self.wait_ticks = random.randint(50, 150)

    def move_towards_target(self):
        curr = QVector2D(self.pos())
        tgt = QVector2D(self.target_pos)
        dist = (tgt - curr).length()
        if dist < WALK_SPEED:
            self.setPos(self.target_pos)
            self.handle_target_reached()
        else:
            self.setPos(
                (curr + (tgt - curr).normalized() * WALK_SPEED).toPointF()
            )

    def handle_target_reached(self):
        if (
            self.state == "FINISHED_SHOPPING"
            or self.state == "IN_QUEUE"
            or self.state == "WALKING_TO_QUEUE"
        ):
            if self.state == "WALKING_TO_QUEUE":
                self.state = "IN_QUEUE"
            return
        if self.state == "WALKING_TO_SHELF":
            self.state = "WAITING_AT_SHELF"
            self.wait_ticks = 50
            if random.random() < ITEM_PICK_PROBABILITY:
                self.inventory += 1
                self.update()
        elif self.state == "RETURNING_TO_ROUTE":
            self.state = "WALKING_ROUTE"
            self.next_wp()
        elif self.state == "WALKING_ROUTE":
            if (
                self.current_waypoint_idx < len(self.route) - 1
                and self.shelves
                and random.random() < SHELF_PROBABILITY
            ):
                sh = self.find_nearest_shelf()
                if sh:
                    self.state = "WALKING_TO_SHELF"
                    self.return_pos = self.target_pos
                    self.target_pos = sh
                    return
            self.next_wp()

    def next_wp(self):
        self.current_waypoint_idx += 1
        if self.current_waypoint_idx >= len(self.route):
            self.enter_waiting_area()
        else:
            self.target_pos = self.route[self.current_waypoint_idx]

    def enter_waiting_area(self):
        self.state = "FINISHED_SHOPPING"
        self.wait_ticks = 0

    def find_nearest_shelf(self):
        if not self.shelves:
            return None
        return min(
            self.shelves,
            key=lambda s: (QVector2D(s) - QVector2D(self.pos())).length(),
            default=None,
        )

    def go_to_queue(self, target_pos, checkout_id):
        self.state = "WALKING_TO_QUEUE"
        self.target_pos = target_pos
        self.assigned_checkout_id = checkout_id
