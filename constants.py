import sys
from enum import Enum

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QGraphicsItem, QWidget, QListWidget, QHBoxLayout, QMenu,
    QDialog, QFormLayout, QLineEdit, QPushButton, QComboBox
)
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPen, QColor, QBrush, QPainterPath


GRID_SIZE = 40
MODULE_W = 120
MODULE_H = 80
MODULE_COLS = MODULE_W // GRID_SIZE
MODULE_ROWS = MODULE_H // GRID_SIZE


class ModuleKind(Enum):
    TRACK = "Vía"
    TURNOUT = "Desvío"
    CROSS_TURNOUT = "Desvío cruzado"
    SIGNAL = "Señal"
    RM = "RM"
    BUTTON = "Botón"
    ACCESSORY = "Accesorio"

class TurnoutVariant(Enum):
    LEFT_UP = "Izquierda arriba"
    LEFT_DOWN = "Izquierda abajo"
    RIGHT_UP = "Derecha arriba"
    RIGHT_DOWN = "Derecha abajo"

    LEFT_UP_LEFT_DOWN = "Izq. arriba + Izq. abajo"
    RIGHT_UP_RIGHT_DOWN = "Der. arriba + Der. abajo"

    LEFT_UP_RIGHT_DOWN = "Izq. arriba + Der. abajo"
    LEFT_DOWN_RIGHT_UP = "Izq. abajo + Der. arriba"

    DIAGONAL_UP = "Diagonal ascendente"
    DIAGONAL_DOWN = "Diagonal descendente"

    CROSS = "Cruzado"
    
class AccessoryVariant(Enum):
    BARRIER_TOP = "Barrera superior"
    BARRIER_BOTTOM = "Barrera inferior"
    CONTROL_MARK = "Control / marca"
    
class Direction(Enum):
    LEFT_TO_RIGHT = "Izquierda → Derecha"
    RIGHT_TO_LEFT = "Derecha → Izquierda"

SIGNAL_VARIANTS = {
    "Señales 2 focos": [
        ("Verde/Rojo", ["green", "red"], "normal"),
        ("Rojo/Verde", ["red", "green"], "normal"),
        ("Rojo/Amarillo", ["red", "yellow"], "normal"),
        ("Rojo/Blanco", ["red", "white"], "normal"),
        ("Verde/Amarillo", ["green", "yellow"], "normal"),
    ],

    "Señales 3 focos": [
        ("Verde/Rojo/Amarillo", ["green", "red", "yellow"], "normal"),
        ("Rojo/Verde/Amarillo", ["red", "green", "yellow"], "normal"),
    ],

    "Señales 4 focos": [
        ("Verde/Rojo/Amarillo/Blanco", ["green", "red", "yellow", "white"], "normal"),
    ],

    "Mono bajo / maniobra": [
        (
            "Mono bajo Rojo/Blanco/Verde/Amarillo",
            [
                ("red", 0, 0),
                ("white", 1, 0),
                ("green", 0, 1),
                ("yellow", 1, 1),
            ],
            "mono_bajo"
        ),
        (
            "Mono bajo Rojo/Verde/Amarillo",
            [
                ("red", 0, 0),
                ("green", 0, 1),
                ("yellow", 1, 1),
            ],
            "mono_bajo"
        ),
        (
            "Mono bajo Rojo/Blanco/Blanco/Blanco",
            [
                ("red", 0, 0),
                ("white", 1, 0),
                ("white", 0, 1),
                ("white", 1, 1),
            ],
            "mono_bajo"
        ),
    ],
}

def color_from_name(name):
    return {
        "red": QColor("#ff3030"),
        "green": QColor("#26c452"),
        "yellow": QColor("#ffd92e"),
        "white": QColor("#f8f8f8"),
    }.get(name, QColor("gray"))


class ModuleConfigDialog(QDialog):
    def __init__(self, item):
        super().__init__()
        self.item = item
        self.setWindowTitle(f"Configurar {item.name}")

        layout = QFormLayout(self)

        self.name_edit = QLineEdit(item.name)
        self.addr_edit = QLineEdit(str(item.address))
        self.article_edit = QLineEdit(str(item.article))

        layout.addRow("Nombre:", self.name_edit)
        layout.addRow("Dirección LocoNet:", self.addr_edit)
        layout.addRow("Artículo:", self.article_edit)

        send_btn = QPushButton("Enviar configuración por LocoNet")
        send_btn.clicked.connect(self.send_config)
        layout.addRow(send_btn)

        save_btn = QPushButton("Guardar")
        save_btn.clicked.connect(self.accept)
        layout.addRow(save_btn)

    def accept(self):
        self.item.name = self.name_edit.text()
        self.item.address = int(self.addr_edit.text())
        self.item.article = int(self.article_edit.text())
        self.item.update()
        super().accept()

    def send_config(self):
        print("Enviar configuración:")
        print("Nombre:", self.item.name)
        print("Tipo:", self.item.kind.value)
        print("Dirección:", self.item.address)
        print("Artículo:", self.item.article)


class ModuleItem(QGraphicsItem):
    def __init__(self, col, row, kind=ModuleKind.TRACK):
        super().__init__()

        self.col = col
        self.row = row
        self.kind = kind

        self.name = self.default_name()
        self.address = 1
        self.article = 6020

        self.turnout_variant = TurnoutVariant.LEFT
        self.signal_name = "Verde/Rojo"
        self.signal_colors = ["green", "red"]

        if kind == ModuleKind.SHUNT_SIGNAL:
            self.signal_name = "Rojo/Blanco"
            self.signal_colors = ["red", "white"]

        self.setPos(col * GRID_SIZE, row * GRID_SIZE)
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges |
            QGraphicsItem.ItemIsFocusable
        )

    def default_name(self):
        if self.kind == ModuleKind.TURNOUT:
            return "D"
        if self.kind == ModuleKind.CROSS_TURNOUT:
            return "D"
        if self.kind in (ModuleKind.SIGNAL, ModuleKind.SHUNT_SIGNAL):
            return "S"
        if self.kind == ModuleKind.RM:
            return "RM"
        if self.kind == ModuleKind.BUTTON:
            return "B"
        return "Vía"

    def boundingRect(self):
        return QRectF(0, 0, MODULE_W, MODULE_H)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(painter.RenderHint.Antialiasing)

        bg = QColor("#cfcfcf")
        border = QColor("#222222")

        if self.isSelected():
            bg = QColor("#dff3ff")
            border = QColor("#0078d7")

        painter.setBrush(QBrush(bg))
        painter.setPen(QPen(border, 2))
        painter.drawRect(self.boundingRect())

        if self.kind == ModuleKind.TRACK:
            self.draw_track(painter)
        elif self.kind == ModuleKind.TURNOUT:
            self.draw_turnout(painter)
        elif self.kind == ModuleKind.CROSS_TURNOUT:
            self.draw_cross_turnout(painter)
        elif self.kind == ModuleKind.SIGNAL:
            self.draw_signal(painter, shunt=False)
        elif self.kind == ModuleKind.SHUNT_SIGNAL:
            self.draw_signal(painter, shunt=True)
        elif self.kind == ModuleKind.RM:
            self.draw_rm(painter)
        elif self.kind == ModuleKind.BUTTON:
            self.draw_button(painter)

        painter.setPen(QPen(QColor("#0033bb"), 1))
        painter.drawText(QRectF(0, MODULE_H + 2, MODULE_W, 16), Qt.AlignCenter, self.name)

    def draw_track(self, painter):
        y = MODULE_H / 2
        painter.setPen(QPen(QColor("black"), 12, Qt.SolidLine, Qt.SquareCap))
        painter.drawLine(0, y, MODULE_W, y)

        painter.setBrush(QBrush(QColor("#999999")))
        painter.setPen(QPen(QColor("black"), 2))
        painter.drawEllipse(QPointF(MODULE_W / 2, y), 10, 10)

    def draw_turnout(self, painter):
        y = MODULE_H / 2
        cx = MODULE_W / 2
        cy = MODULE_H / 2

        painter.setPen(QPen(QColor("black"), 14, Qt.SolidLine, Qt.SquareCap))

        if self.turnout_variant == TurnoutVariant.LEFT:
            painter.drawLine(0, y, MODULE_W, y)
            painter.drawLine(0, 0, cx, cy)
            painter.drawLine(cx, cy, MODULE_W, MODULE_H)
            self.draw_white_slot(painter, 20, 18, 42, 30)
            self.draw_white_slot(painter, 78, 52, 100, 64)

        elif self.turnout_variant == TurnoutVariant.RIGHT:
            painter.drawLine(0, y, MODULE_W, y)
            painter.drawLine(0, MODULE_H, cx, cy)
            painter.drawLine(cx, cy, MODULE_W, 0)
            self.draw_white_slot(painter, 20, 52, 42, 64)
            self.draw_white_slot(painter, 78, 18, 100, 30)

        elif self.turnout_variant == TurnoutVariant.LEFT_REVERSE:
            painter.drawLine(0, y, MODULE_W, y)
            painter.drawLine(0, MODULE_H, cx, cy)
            painter.drawLine(cx, cy, MODULE_W, 0)
            self.draw_white_slot(painter, 20, 52, 42, 64)
            self.draw_white_slot(painter, 78, 18, 100, 30)

        elif self.turnout_variant == TurnoutVariant.RIGHT_REVERSE:
            painter.drawLine(0, y, MODULE_W, y)
            painter.drawLine(0, 0, cx, cy)
            painter.drawLine(cx, cy, MODULE_W, MODULE_H)
            self.draw_white_slot(painter, 20, 18, 42, 30)
            self.draw_white_slot(painter, 78, 52, 100, 64)

        painter.setBrush(QBrush(QColor("#999999")))
        painter.setPen(QPen(QColor("black"), 2))
        painter.drawEllipse(QPointF(cx, cy), 14, 14)

    def draw_cross_turnout(self, painter):
        cx = MODULE_W / 2
        cy = MODULE_H / 2

        painter.setPen(QPen(QColor("black"), 14, Qt.SolidLine, Qt.SquareCap))
        painter.drawLine(0, 0, MODULE_W, MODULE_H)
        painter.drawLine(0, MODULE_H, MODULE_W, 0)

        self.draw_white_slot(painter, 18, 15, 42, 28)
        self.draw_white_slot(painter, 78, 52, 102, 65)
        self.draw_white_slot(painter, 18, 52, 42, 65)
        self.draw_white_slot(painter, 78, 15, 102, 28)

        painter.setBrush(QBrush(QColor("#999999")))
        painter.setPen(QPen(QColor("black"), 2))
        painter.drawEllipse(QPointF(cx, cy), 14, 14)

    def draw_white_slot(self, painter, x1, y1, x2, y2):
        painter.setPen(QPen(QColor("white"), 5, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(x1, y1, x2, y2)

    def draw_signal(self, painter, shunt=False):
        y = MODULE_H / 2

        painter.setPen(QPen(QColor("black"), 12, Qt.SolidLine, Qt.SquareCap))
        painter.drawLine(0, y, MODULE_W, y)

        painter.setBrush(QBrush(QColor("#999999")))
        painter.setPen(QPen(QColor("black"), 2))
        painter.drawEllipse(QPointF(MODULE_W / 2, y + 16), 9, 9)

        painter.setPen(QPen(QColor("black"), 4))
        painter.drawLine(MODULE_W / 2, y + 8, MODULE_W / 2, y + 25)

        count = len(self.signal_colors)
        box_w = 18 + count * 18
        box_x = (MODULE_W - box_w) / 2
        box_y = 16

        painter.setBrush(QBrush(QColor("#111111")))
        painter.setPen(QPen(QColor("black"), 2))
        painter.drawRoundedRect(QRectF(box_x, box_y, box_w, 20), 8, 8)

        for i, c in enumerate(self.signal_colors):
            painter.setBrush(QBrush(color_from_name(c)))
            painter.setPen(QPen(QColor("black"), 1))
            painter.drawEllipse(QPointF(box_x + 14 + i * 18, box_y + 10), 7, 7)

        if shunt:
            painter.setPen(QPen(QColor("black"), 4))
            painter.drawLine(box_x + box_w, box_y + 10, box_x + box_w + 12, box_y + 10)

    def draw_rm(self, painter):
        y = MODULE_H / 2

        painter.setPen(QPen(QColor("black"), 12, Qt.SolidLine, Qt.SquareCap))
        painter.drawLine(0, y, 30, y)
        painter.drawLine(90, y, MODULE_W, y)

        painter.setPen(QPen(QColor("#0044cc"), 4))
        painter.drawText(QRectF(0, 0, MODULE_W, MODULE_H), Qt.AlignCenter, "RM")

    def draw_button(self, painter):
        y = MODULE_H / 2

        painter.setPen(QPen(QColor("black"), 12, Qt.SolidLine, Qt.SquareCap))
        painter.drawLine(0, y, MODULE_W, y)

        painter.setBrush(QBrush(QColor("#999999")))
        painter.setPen(QPen(QColor("black"), 2))
        painter.drawEllipse(QPointF(MODULE_W / 2, y), 18, 18)

        painter.setBrush(QBrush(QColor("#555555")))
        painter.drawEllipse(QPointF(MODULE_W / 2, y), 9, 9)

    def mouseDoubleClickEvent(self, event):
        ModuleConfigDialog(self).exec()
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu()

        if self.kind == ModuleKind.TURNOUT:
            for variant in TurnoutVariant:
                act = menu.addAction(variant.value)
                act.triggered.connect(lambda checked=False, v=variant: self.set_turnout_variant(v))

        elif self.kind == ModuleKind.SIGNAL:
            for group, variants in SIGNAL_VARIANTS.items():
                sub = menu.addMenu(group)
                for name, colors in variants:
                    act = sub.addAction(name)
                    act.triggered.connect(lambda checked=False, n=name, c=colors: self.set_signal_variant(n, c))

        elif self.kind == ModuleKind.SHUNT_SIGNAL:
            for group, variants in SHUNT_SIGNAL_VARIANTS.items():
                sub = menu.addMenu(group)
                for name, colors in variants:
                    act = sub.addAction(name)
                    act.triggered.connect(lambda checked=False, n=name, c=colors: self.set_signal_variant(n, c))

        menu.addSeparator()
        cfg = menu.addAction("Configurar")
        delete = menu.addAction("Eliminar")

        selected = menu.exec(event.screenPos())

        if selected == cfg:
            ModuleConfigDialog(self).exec()
        elif selected == delete and self.scene():
            self.scene().remove_module(self)

    def set_turnout_variant(self, variant):
        self.turnout_variant = variant
        self.update()

    def set_signal_variant(self, name, colors):
        self.signal_name = name
        self.signal_colors = colors
        self.update()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            scene = self.scene()
            new_col = round(value.x() / GRID_SIZE)
            new_row = round(value.y() / GRID_SIZE)

            if isinstance(scene, GridScene):
                if scene.can_move_item(self, new_col, new_row):
                    return QPointF(new_col * GRID_SIZE, new_row * GRID_SIZE)
                return QPointF(self.col * GRID_SIZE, self.row * GRID_SIZE)

        if change == QGraphicsItem.ItemPositionHasChanged and self.scene():
            scene = self.scene()
            new_col = round(self.pos().x() / GRID_SIZE)
            new_row = round(self.pos().y() / GRID_SIZE)

            if isinstance(scene, GridScene):
                scene.move_item(self, new_col, new_row)

        return super().itemChange(change, value)


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
            if isinstance(item, ModuleItem):
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


class Canvas(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.grid_scene = GridScene()
        self.setScene(self.grid_scene)

        self.setAcceptDrops(True)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setFocusPolicy(Qt.StrongFocus)

    def dragEnterEvent(self, event):
        event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        text = event.mimeData().text()
        pos = self.mapToScene(event.position().toPoint())

        col = round(pos.x() / GRID_SIZE)
        row = round(pos.y() / GRID_SIZE)

        kind = ModuleKind.TRACK

        if text == "Desvío":
            kind = ModuleKind.TURNOUT
        elif text == "Desvío cruzado":
            kind = ModuleKind.CROSS_TURNOUT
        elif text == "Señal":
            kind = ModuleKind.SIGNAL
        elif text == "Señal maniobra":
            kind = ModuleKind.SHUNT_SIGNAL
        elif text == "RM":
            kind = ModuleKind.RM
        elif text == "Botón":
            kind = ModuleKind.BUTTON

        item = ModuleItem(col, row, kind)

        if not self.grid_scene.add_module(item):
            print("Zona ocupada, no se puede colocar ahí.")

        event.acceptProposedAction()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self.grid_scene.delete_selected()
        else:
            super().keyPressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Editor gráfico LocoNet")
        self.resize(1200, 800)

        central = QWidget()
        layout = QHBoxLayout(central)

        self.palette = QListWidget()
        self.palette.addItems([
            "Vía",
            "Desvío",
            "Desvío cruzado",
            "Señal",
            "Señal maniobra",
            "RM",
            "Botón",
        ])
        self.palette.setDragEnabled(True)

        self.canvas = Canvas()

        layout.addWidget(self.palette, 1)
        layout.addWidget(self.canvas, 6)

        self.setCentralWidget(central)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())