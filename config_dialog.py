from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton


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