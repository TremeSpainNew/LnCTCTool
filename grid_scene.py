from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtGui import QPen, QColor

from constants import GRID_SIZE, MODULE_COLS, MODULE_ROWS
from modules.base_module import BaseModule


class GridScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        self.setSceneRect(0, 0, 1800, 1000)
        self.occupied = {}

    def occupied_cells_for(self, col, row):
        return [
            (col + dx, row + dy)
            for dx in range(MODULE_COLS)
            for dy in range(MODULE_ROWS)
        ]

    def add_module(self, item):
        cells = self.occupied_cells_for(item.col, item.row)

        for cell in cells:
            if cell in self.occupied:
                return False

        for cell in cells:
            self.occupied[cell] = item

        self.addItem(item)
        return True

    def remove_module(self, item):
        for cell in list(self.occupied.keys()):
            if self.occupied[cell] is item:
                del self.occupied[cell]

        self.removeItem(item)

    def can_move_item(self, item, col, row):
        if col < 0 or row < 0:
            return False

        for cell in self.occupied_cells_for(col, row):
            owner = self.occupied.get(cell)
            if owner is not None and owner is not item:
                return False

        return True

    def move_item(self, item, col, row):
        if not self.can_move_item(item, col, row):
            return

        for cell in list(self.occupied.keys()):
            if self.occupied[cell] is item:
                del self.occupied[cell]

        for cell in self.occupied_cells_for(col, row):
            self.occupied[cell] = item

        item.col = col
        item.row = row

    def delete_selected(self):
        for item in list(self.selectedItems()):
            if isinstance(item, BaseModule):
                self.remove_module(item)

    def drawBackground(self, painter, rect):
        painter.fillRect(rect, QColor("#eeeeee"))
        painter.setPen(QPen(QColor("#c8c8c8"), 1))

        left = int(rect.left()) - int(rect.left()) % GRID_SIZE
        top = int(rect.top()) - int(rect.top()) % GRID_SIZE

        x = left
        while x < rect.right():
            painter.drawLine(x, rect.top(), x, rect.bottom())
            x += GRID_SIZE

        y = top
        while y < rect.bottom():
            painter.drawLine(rect.left(), y, rect.right(), y)
            y += GRID_SIZE