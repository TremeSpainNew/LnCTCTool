from PySide6.QtWidgets import QMenu
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QBrush

from constants import MODULE_W, MODULE_H, ModuleKind, TurnoutVariant
from modules.base_module import BaseModule
from config_dialog import ModuleConfigDialog
import math


class TurnoutModule(BaseModule):
    def __init__(self, col, row):
        super().__init__(col, row, ModuleKind.TURNOUT)

        self.name = "A"
        self.profile_key = "turnout"
        self.lncv_values = {
            "module_addr": 1,
        
            "turnout_addr_1": 10,
            "turnout_addr_2": 11,
        
            "type": 0,
            "invert_dir": 0,
            "invert_fb": 0,
            "has_feedback": 1,
        }
        self.variant = TurnoutVariant.LEFT_UP

    def draw_module(self, painter):
        if self.variant == TurnoutVariant.CROSS:
            self.draw_cross(painter)
        else:
            self.draw_turnout(painter)

    def get_branches(self):
        if self.variant == TurnoutVariant.LEFT_UP:
            return ["up"], []

        if self.variant == TurnoutVariant.LEFT_DOWN:
            return ["down"], []

        if self.variant == TurnoutVariant.RIGHT_UP:
            return [], ["up"]

        if self.variant == TurnoutVariant.RIGHT_DOWN:
            return [], ["down"]

        if self.variant == TurnoutVariant.LEFT_UP_LEFT_DOWN:
            return ["up", "down"], []

        if self.variant == TurnoutVariant.RIGHT_UP_RIGHT_DOWN:
            return [], ["up", "down"]

        if self.variant == TurnoutVariant.LEFT_UP_RIGHT_DOWN:
            return ["up"], ["down"]

        if self.variant == TurnoutVariant.LEFT_DOWN_RIGHT_UP:
            return ["down"], ["up"]

        if self.variant == TurnoutVariant.DIAGONAL_UP:
            return ["up", "down"], []

        if self.variant == TurnoutVariant.DIAGONAL_DOWN:
            return [], ["up", "down"]

        return ["up"], []

    def draw_turnout(self, painter):
        y = MODULE_H / 2
        cx = MODULE_W / 2
        cy = MODULE_H / 2

        left_branches, right_branches = self.get_branches()

        painter.setPen(Qt.NoPen)

        # vía recta
        painter.setBrush(QBrush(QColor("black")))
        left_count = len(left_branches)
        right_count = len(right_branches)

        if left_count == 2 and right_count == 0:
            painter.drawRect(QRectF(cx, y - 5, MODULE_W - cx, 10))

        elif right_count == 2 and left_count == 0:
            painter.drawRect(QRectF(0, y - 5, cx, 10))

        else:
            painter.drawRect(QRectF(0, y - 5, MODULE_W, 10))

        painter.setPen(QPen(QColor("black"), 10, Qt.SolidLine, Qt.SquareCap))

        # ramas izquierdas
        for branch in left_branches:
            if branch == "up":
                x1, y1, x2, y2 = 0, 0, cx, cy
                painter.drawLine(x1, y1, x2, y2)
                self.draw_slot_on_line(painter, x1, y1, x2, y2, t=0.38)

            elif branch == "down":
                x1, y1, x2, y2 = 0, MODULE_H, cx, cy
                painter.drawLine(x1, y1, x2, y2)
                self.draw_slot_on_line(painter, x1, y1, x2, y2, t=0.38)

        # ramas derechas
        for branch in right_branches:
            if branch == "up":
                x1, y1, x2, y2 = cx, cy, MODULE_W, 0
                painter.drawLine(x1, y1, x2, y2)
                self.draw_slot_on_line(painter, x1, y1, x2, y2, t=0.62)

            elif branch == "down":
                x1, y1, x2, y2 = cx, cy, MODULE_W, MODULE_H
                painter.drawLine(x1, y1, x2, y2)
                self.draw_slot_on_line(painter, x1, y1, x2, y2, t=0.62)

        # sensores vía recta
        #if left_branches and not right_branches:
            #self.draw_slot_on_line(painter, 0, y, MODULE_W, y, t=0.22)
        if left_count == 2 and right_count == 0:
            return
        elif right_count == 2 and left_count == 0:
            return

        #elif right_branches and not left_branches:
            #self.draw_slot_on_line(painter, 0, y, MODULE_W, y, t=0.78)

        else:
            self.draw_slot_on_line(painter, 0, y, MODULE_W, y, t=0.22)
            self.draw_slot_on_line(painter, 0, y, MODULE_W, y, t=0.78)

        self.draw_center(painter)

    def draw_cross(self, painter):
        painter.setPen(QPen(QColor("black"), 10, Qt.SolidLine, Qt.SquareCap))
        left_count = len(left_branches)
        right_count = len(right_branches)

        # diagonal 1
        x1, y1, x2, y2 = 0, 0, MODULE_W, MODULE_H
        painter.drawLine(x1, y1, x2, y2)
        self.draw_slot_on_line(painter, x1, y1, x2, y2, t=0.25)
        self.draw_slot_on_line(painter, x1, y1, x2, y2, t=0.75)

        # diagonal 2
        x1, y1, x2, y2 = 0, MODULE_H, MODULE_W, 0
        painter.drawLine(x1, y1, x2, y2)
        self.draw_slot_on_line(painter, x1, y1, x2, y2, t=0.25)
        self.draw_slot_on_line(painter, x1, y1, x2, y2, t=0.75)

        self.draw_center(painter)

    def draw_center(self, painter):
        painter.setBrush(QBrush(QColor("#666666")))
        painter.setPen(QPen(QColor("black"), 1))
        painter.drawEllipse(
            QPointF(MODULE_W / 2, MODULE_H / 2),
            10,
            10
        )

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

        variant_menu = menu.addMenu("Tipo de desvío")

        for variant in TurnoutVariant:
            act = variant_menu.addAction(variant.value)
            act.triggered.connect(
                lambda checked=False, v=variant: self.set_variant(v)
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
        
    