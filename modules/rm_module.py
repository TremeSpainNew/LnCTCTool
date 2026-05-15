from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPen, QColor

from constants import MODULE_W, MODULE_H, ModuleKind
from modules.base_module import BaseModule


class RMModule(BaseModule):
    def __init__(self, col, row):
        super().__init__(col, row, ModuleKind.RM)
        self.name = "RM"

    def draw_module(self, painter):
        y = MODULE_H / 2

        painter.setPen(QPen(QColor("black"), 12, Qt.SolidLine, Qt.SquareCap))
        painter.drawLine(0, y, 30, y)
        painter.drawLine(90, y, MODULE_W, y)

        painter.setPen(QPen(QColor("#0044cc"), 4))
        painter.drawText(QRectF(0, 0, MODULE_W, MODULE_H), Qt.AlignCenter, "RM")