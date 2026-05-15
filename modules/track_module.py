from PySide6.QtCore import QPointF
from PySide6.QtGui import QPen, QColor, QBrush
from PySide6.QtCore import Qt

from constants import MODULE_W, MODULE_H, ModuleKind
from modules.base_module import BaseModule


class TrackModule(BaseModule):
    def __init__(self, col, row):
        super().__init__(col, row, ModuleKind.TRACK)

    def draw_module(self, painter):
        y = MODULE_H / 2

        painter.setBrush(QBrush(QColor("black")))
        painter.drawRect(QRectF(0, y - 5, MODULE_W, 10))

        painter.setPen(QPen(QColor("black"), 10, Qt.SolidLine, Qt.SquareCap))