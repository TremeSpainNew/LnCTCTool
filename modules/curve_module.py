# modules/curve_module.py

from PySide6.QtWidgets import QMenu
from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QColor, QPainterPath

from constants import MODULE_W, MODULE_H, ModuleKind
from modules.base_module import BaseModule
from config_dialog import ModuleConfigDialog


class CurveModule(BaseModule):
    def __init__(self, col, row):
        super().__init__(col, row, ModuleKind.CURVE)

        self.name = "C"
        self.profile_key = None
        self.lncv_values = {}

        self.flip_x = False
        self.flip_y = False

    def draw_module(self, painter):
        painter.setRenderHint(painter.RenderHint.Antialiasing)

        painter.save()

        if self.flip_x:
            painter.translate(MODULE_W, 0)
            painter.scale(-1, 1)

        if self.flip_y:
            painter.translate(0, MODULE_H)
            painter.scale(1, -1)

        pen = QPen(QColor("black"), 10, Qt.SolidLine, Qt.SquareCap, Qt.BevelJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        break_x = MODULE_W / 2
        break_y = MODULE_H / 2

        path = QPainterPath()
        path.moveTo(0, break_y)
        path.lineTo(break_x, break_y)
        path.lineTo(MODULE_W, MODULE_H)

        painter.drawPath(path)

        painter.restore()

    def contextMenuEvent(self, event):
        menu = QMenu()

        flip_x = menu.addAction("Invertir izquierda/derecha")
        flip_x.triggered.connect(self.toggle_flip_x)

        flip_y = menu.addAction("Invertir arriba/abajo")
        flip_y.triggered.connect(self.toggle_flip_y)

        menu.addSeparator()

        cfg = menu.addAction("Configurar")
        delete = menu.addAction("Eliminar")

        selected = menu.exec(event.screenPos())

        if selected == cfg:
            main_window = self.scene().views()[0].window() if self.scene() and self.scene().views() else None
            ModuleConfigDialog(self, main_window).exec()

        elif selected == delete and self.scene():
            self.scene().remove_module(self)

    def toggle_flip_x(self):
        self.flip_x = not self.flip_x
        self.update()

    def toggle_flip_y(self):
        self.flip_y = not self.flip_y
        self.update()