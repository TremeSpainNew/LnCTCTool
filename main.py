import sys

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout

from canvas import Canvas
from palette import PaletteListWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Editor gráfico LocoNet")
        self.resize(1200, 800)

        central = QWidget()
        layout = QHBoxLayout(central)

        self.palette = PaletteListWidget()
        self.palette.addItems([
            "Vía",
            "Desvío",
            "Desvío cruzado",
            "Señal",
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