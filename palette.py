from PySide6.QtWidgets import QListWidget
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QDrag


class PaletteListWidget(QListWidget):
    def startDrag(self, supportedActions):
        item = self.currentItem()
        if not item:
            return

        mime = QMimeData()
        mime.setText(item.text())

        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.CopyAction)