from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QBrush

from constants import MODULE_W, MODULE_H, ModuleKind
from modules.base_module import BaseModule
import math


class ButtonModule(BaseModule):
    def __init__(self, col, row):
        super().__init__(col, row, ModuleKind.BUTTON)
        self.name = "B"

    def draw_slot_on_line(self, painter, x1, y1, x2, y2, t=0.5, w=24, h=5):
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

    def draw_module(self, painter):
        y = MODULE_H / 2
        cx = MODULE_W / 2

        painter.setPen(Qt.NoPen)

        # vía
        painter.setBrush(QBrush(QColor("black")))
        painter.drawRect(QRectF(0, y - 5, MODULE_W, 10))

        # sensores (retroseñalización)
        self.draw_slot_on_line(painter, 0, y, MODULE_W, y, t=0.25)
        self.draw_slot_on_line(painter, 0, y, MODULE_W, y, t=0.75)

        # botón centrado
        painter.setBrush(QBrush(QColor("#555555")))
        painter.setPen(QPen(QColor("black"), 1))
        painter.drawEllipse(QPointF(cx, y), 10, 10)