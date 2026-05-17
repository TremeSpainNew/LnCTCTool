from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import Qt

from constants import GRID_SIZE
from grid_scene import GridScene
from modules import TrackModule, TurnoutModule, SignalModule, RMModule, ButtonModule, AccessoryModule


class Canvas(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.grid_scene = GridScene()
        self.setScene(self.grid_scene)

        self.setAcceptDrops(True)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setFocusPolicy(Qt.StrongFocus)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        text = event.mimeData().text().strip()
        print("DROP:", text)

        pos = self.mapToScene(event.position().toPoint())

        col = round(pos.x() / GRID_SIZE)
        row = round(pos.y() / GRID_SIZE)

        item = None

        if text == "Vía":
            item = TrackModule(col, row)
        elif text == "Desvío":
            item = TurnoutModule(col, row)
        elif text == "Señal":
            item = SignalModule(col, row, shunt=False)
        elif text == "Señal maniobra":
            item = SignalModule(col, row, shunt=True)
        elif text == "RM":
            item = RMModule(col, row)
        elif text == "Botón":
            item = ButtonModule(col, row)
        elif text == "Accesorio":
            item = AccessoryModule(col, row)

        if item and not self.grid_scene.add_module(item):
            print("Zona ocupada, no se puede colocar ahí.")

        event.acceptProposedAction()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self.grid_scene.delete_selected()
        else:
            super().keyPressEvent(event)