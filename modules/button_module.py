from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QBrush

from constants import MODULE_W, MODULE_H, ModuleKind
from modules.base_module import BaseModule


class ButtonModule(BaseModule):
    def __init__(self, col, row):
        super().__init__(col, row, ModuleKind.BUTTON)
        self.name = "B"

    def draw_module(self, painter):
        y = MODULE_H / 2
        cx = MODULE_W / 2

        painter.setPen(Qt.NoPen)

        # vía
        painter.setBrush(QBrush(QColor("black")))
        painter.drawRect(QRectF(0, y - 5, MODULE_W, 10))

        # sensores ocupación amarillos
        painter.setBrush(QBrush(QColor("#ffff00")))
        painter.drawRoundedRect(QRectF(12, y + 13, 24, 5), 2, 2)
        painter.drawRoundedRect(QRectF(MODULE_W - 36, y + 13, 24, 5), 2, 2)

        # botón centrado
        painter.setBrush(QBrush(QColor("#555555")))
        painter.setPen(QPen(QColor("black"), 1))
        painter.drawEllipse(QPointF(cx, y), 10, 10)