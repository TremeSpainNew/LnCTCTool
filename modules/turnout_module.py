from PySide6.QtWidgets import QMenu
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QBrush

from constants import MODULE_W, MODULE_H, ModuleKind, TurnoutVariant, Direction
from modules.base_module import BaseModule
from config_dialog import ModuleConfigDialog
import math


class TurnoutModule(BaseModule):
    def __init__(self, col, row, crossed=False):
        kind = ModuleKind.CROSS_TURNOUT if crossed else ModuleKind.TURNOUT
        super().__init__(col, row, kind)

        self.name = "D"
        self.crossed = crossed
        self.variant = TurnoutVariant.L_UP

    def draw_module(self, painter):
        if self.crossed:
            self.draw_cross(painter)
        else:
            self.draw_turnout(painter)

    def get_branches(self):
        v = self.variant

        if v == TurnoutVariant.L_UP:
            return "up", None
        if v == TurnoutVariant.L_UP_R_DOWN:
            return "up", "down"
        if v == TurnoutVariant.L_DOWN:
            return "down", None
        if v == TurnoutVariant.L_DOWN_R_UP:
            return "down", "up"

        if v == TurnoutVariant.R_DOWN:
            return None, "down"
        if v == TurnoutVariant.L_UP_R_DOWN_FULL:
            return "up", "down"

        if v == TurnoutVariant.R_UP:
            return None, "up"
        if v == TurnoutVariant.L_DOWN_R_UP_FULL:
            return "down", "up"

        if v == TurnoutVariant.BOTH_UP_DOWN:
            return "up", "down"
        if v == TurnoutVariant.BOTH_DOWN_UP:
            return "down", "up"

        return "up", None

    def draw_turnout(self, painter):
        y = MODULE_H / 2
        cx = MODULE_W / 2
        cy = MODULE_H / 2

        left_branch, right_branch = self.get_branches()

        if self.direction == Direction.RIGHT_TO_LEFT:
            left_branch, right_branch = right_branch, left_branch

        painter.setPen(Qt.NoPen)

        # vía recta horizontal
        painter.setBrush(QBrush(QColor("black")))
        painter.drawRect(QRectF(0, y - 5, MODULE_W, 10))

        painter.setPen(QPen(QColor("black"), 10, Qt.SolidLine, Qt.SquareCap))

        margin = 0
        branch_offset = MODULE_H / 2

        # rama izquierda
        if left_branch == "up":
            x1, y1, x2, y2 = 0, 0, cx, cy
            painter.drawLine(x1, y1, x2, y2)
            self.draw_slot_on_line(painter, x1, y1, x2, y2, t=0.42)

        elif left_branch == "down":
            x1, y1, x2, y2 = 0, MODULE_H, cx, cy
            painter.drawLine(x1, y1, x2, y2)
            self.draw_slot_on_line(painter, x1, y1, x2, y2, t=0.42)

        # rama derecha
        if right_branch == "up":
            x1, y1, x2, y2 = cx, cy, MODULE_W, 0
            painter.drawLine(x1, y1, x2, y2)
            self.draw_slot_on_line(painter, x1, y1, x2, y2, t=0.58)

        elif right_branch == "down":
            x1, y1, x2, y2 = cx, cy, MODULE_W, MODULE_H
            painter.drawLine(x1, y1, x2, y2)
            self.draw_slot_on_line(painter, x1, y1, x2, y2, t=0.58)

        # sensor en vía recta
        self.draw_slot_on_line(painter, 0, y, MODULE_W, y, t=0.20)
        self.draw_slot_on_line(painter, 0, y, MODULE_W, y, t=0.80)

        # círculo central
        painter.setBrush(QBrush(QColor("#666666")))
        painter.setPen(QPen(QColor("black"), 1))
        painter.drawEllipse(QPointF(cx, cy), 10, 10)

    def draw_cross(self, painter):
        cx = MODULE_W / 2
        cy = MODULE_H / 2

        painter.setPen(QPen(QColor("black"), 10, Qt.SolidLine, Qt.SquareCap))

        margin = 6
        painter.drawLine(0, 0, MODULE_W, MODULE_H)
        painter.drawLine(0, MODULE_H, MODULE_W, 0)

        self.draw_slot(painter, 25, 18, 24, 5, 28)
        self.draw_slot(painter, MODULE_W - 25, MODULE_H - 18, 24, 5, 28)
        self.draw_slot(painter, 25, MODULE_H - 18, 24, 5, -28)
        self.draw_slot(painter, MODULE_W - 25, 18, 24, 5, -28)

        painter.setBrush(QBrush(QColor("#666666")))
        painter.setPen(QPen(QColor("black"), 1))
        painter.drawEllipse(QPointF(cx, cy), 11, 11)

    def draw_slot_on_line(self, painter, x1, y1, x2, y2, t=0.45, w=24, h=5):
        x = x1 + (x2 - x1) * t
        y = y1 + (y2 - y1) * t

        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))

        painter.save()
        painter.translate(x, y)
        painter.rotate(angle)

        painter.setPen(QPen(QColor("black"), 1))
        painter.setBrush(QBrush(QColor("white")))
        painter.drawRoundedRect(
            QRectF(-w / 2, -h / 2, w, h),
            2,
            2
        )

        painter.restore()

    def contextMenuEvent(self, event):
        menu = QMenu()

        if not self.crossed:
            variant_menu = menu.addMenu("Tipo de desvío")

            for variant in TurnoutVariant:
                act = variant_menu.addAction(variant.value)
                act.triggered.connect(
                    lambda checked=False, v=variant: self.set_variant(v)
                )

        direction_menu = menu.addMenu("Sentido")

        for direction in Direction:
            act = direction_menu.addAction(direction.value)
            act.triggered.connect(
                lambda checked=False, d=direction: self.set_direction(d)
            )

        menu.addSeparator()

        cfg = menu.addAction("Configurar")
        delete = menu.addAction("Eliminar")

        selected = menu.exec(event.screenPos())

        if selected == cfg:
            ModuleConfigDialog(self).exec()
        elif selected == delete and self.scene():
            self.scene().remove_module(self)

    def set_variant(self, variant):
        self.variant = variant
        self.update()