from PySide6.QtWidgets import QGraphicsItem, QMenu
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPen, QColor, QBrush

from constants import GRID_SIZE, MODULE_W, MODULE_H, Direction
from config_dialog import ModuleConfigDialog


class BaseModule(QGraphicsItem):
    def __init__(self, col, row, kind):
        super().__init__()

        self.col = col
        self.row = row
        self.kind = kind
        self.name = kind.value
        self.address = 1
        self.article = 6020
        self.direction = Direction.LEFT_TO_RIGHT

        self.setPos(col * GRID_SIZE, row * GRID_SIZE)

        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges |
            QGraphicsItem.ItemIsFocusable
        )

    def boundingRect(self):
        return QRectF(0, 0, MODULE_W, MODULE_H)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(painter.RenderHint.Antialiasing)

        if self.isSelected():
            painter.setBrush(QBrush(QColor("#dff3ff")))
            painter.setPen(QPen(QColor("#0078d7"), 1))
            painter.drawRect(self.boundingRect())

        self.draw_module(painter)

        painter.setPen(QPen(QColor("#0033bb"), 1))
        painter.drawText(
            QRectF(0, MODULE_H - 18, MODULE_W, 16),
            Qt.AlignCenter,
            self.name
        )

    def draw_module(self, painter):
        pass

    def mouseDoubleClickEvent(self, event):
        ModuleConfigDialog(self).exec()
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu()

        dir_menu = menu.addMenu("Sentido")

        for direction in Direction:
            act = dir_menu.addAction(direction.value)
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

    def set_direction(self, direction):
        self.direction = direction
        self.update()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            scene = self.scene()

            new_col = max(0, int(value.x() // GRID_SIZE))
            new_row = max(0, int(value.y() // GRID_SIZE))

            snapped_pos = QPointF(
                new_col * GRID_SIZE,
                new_row * GRID_SIZE
            )

            if hasattr(scene, "can_move_item"):
                if scene.can_move_item(self, new_col, new_row):
                    return snapped_pos

                return QPointF(
                    self.col * GRID_SIZE,
                    self.row * GRID_SIZE
                )

        if change == QGraphicsItem.ItemPositionHasChanged and self.scene():
            scene = self.scene()

            new_col = max(0, int(self.pos().x() // GRID_SIZE))
            new_row = max(0, int(self.pos().y() // GRID_SIZE))

            if hasattr(scene, "move_item"):
                scene.move_item(self, new_col, new_row)

            self.setPos(
                self.col * GRID_SIZE,
                self.row * GRID_SIZE
            )

        return super().itemChange(change, value)