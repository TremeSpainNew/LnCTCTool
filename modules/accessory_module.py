from PySide6.QtWidgets import QMenu
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPen, QColor, QBrush

from constants import MODULE_W, MODULE_H, ModuleKind, AccessoryVariant
from modules.base_module import BaseModule
from config_dialog import ModuleConfigDialog


class AccessoryModule(BaseModule):
    def __init__(self, col, row):
        super().__init__(col, row, ModuleKind.ACCESSORY)
        self.name = "A"
        self.profile_key = "accessory"
        self.lncv_values = {
            "module_addr": 1,

            "accessory_type": 0,
            "linked_addr": 1,
        }
        self.variant = AccessoryVariant.BARRIER_TOP

    def draw_module(self, painter):
        if self.variant == AccessoryVariant.BARRIER_TOP:
            self.draw_barrier_top(painter)
        elif self.variant == AccessoryVariant.BARRIER_BOTTOM:
            self.draw_barrier_bottom(painter)
        elif self.variant == AccessoryVariant.CONTROL_MARK:
            self.draw_control_mark(painter)

    def draw_barrier_top(self, painter):
        painter.setPen(QPen(QColor("black"), 1))
        painter.setBrush(QBrush(QColor("white")))
        painter.drawRect(QRectF(12, 18, MODULE_W - 24, 8))

        painter.setBrush(QBrush(QColor("#888888")))
        painter.drawEllipse(QPointF(MODULE_W / 2, MODULE_H / 2), 9, 9)

        painter.drawRoundedRect(QRectF(78, 44, 22, 6), 3, 3)

    def draw_barrier_bottom(self, painter):
        painter.setPen(QPen(QColor("black"), 1))
        painter.setBrush(QBrush(QColor("white")))
        painter.drawRect(QRectF(12, MODULE_H - 26, MODULE_W - 24, 8))

        painter.setBrush(QBrush(QColor("#888888")))
        painter.drawEllipse(QPointF(MODULE_W / 2, MODULE_H / 2), 9, 9)

        painter.drawRoundedRect(QRectF(78, 30, 22, 6), 3, 3)

    def draw_control_mark(self, painter):
        painter.setPen(QPen(QColor("black"), 2))
        painter.drawLine(35, 24, 85, 24)

        painter.setPen(QPen(QColor("black"), 1))
        painter.drawLine(45, 18, 45, 24)
        painter.drawLine(55, 16, 55, 24)
        painter.drawLine(65, 18, 65, 24)

        painter.setBrush(QBrush(QColor("#888888")))
        painter.drawEllipse(QPointF(MODULE_W / 2, MODULE_H / 2), 9, 9)

    def contextMenuEvent(self, event):
        menu = QMenu()

        variant_menu = menu.addMenu("Tipo de accesorio")

        for variant in AccessoryVariant:
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