from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QPushButton,
    QVBoxLayout, QLabel, QMessageBox, QCheckBox
)

from loconet_bridge import LocoNetBridge


class ModuleConfigDialog(QDialog):
    def __init__(self, item, main_window=None):
        super().__init__()

        self.item = item
        self.main_window = main_window
        self.edits = {}

        self.setWindowTitle(f"Configurar {item.name}")

        main_layout = QVBoxLayout(self)

        title = QLabel(f"Tipo: {item.kind.value}")
        main_layout.addWidget(title)

        form = QFormLayout()
        main_layout.addLayout(form)

        self.name_edit = QLineEdit(item.name)
        form.addRow("Nombre:", self.name_edit)

        if getattr(item, "profile_key", None):
            article = item.get_article()
            article_edit = QLineEdit(str(article))
            article_edit.setReadOnly(True)
            form.addRow("Artículo:", article_edit)

        for field_name, value in item.lncv_values.items():
            edit = QLineEdit(str(value))
            self.edits[field_name] = edit
            form.addRow(field_name + ":", edit)

        self.write_lncv0_check = QCheckBox(
            "Escribir LNCV0 / cambiar dirección de módulo"
        )
        self.write_lncv0_check.setChecked(
            getattr(item, "write_lncv0", False)
        )
        main_layout.addWidget(self.write_lncv0_check)

        save_btn = QPushButton("Guardar")
        save_btn.clicked.connect(self.accept)
        main_layout.addWidget(save_btn)

        send_btn = QPushButton("Enviar configuración por LocoNet")
        send_btn.clicked.connect(self.send_config)
        main_layout.addWidget(send_btn)

    def save_values(self):
        self.item.name = self.name_edit.text()

        for field_name, edit in self.edits.items():
            text = edit.text().strip()

            try:
                value = int(text)
            except ValueError:
                QMessageBox.warning(
                    self,
                    "Valor inválido",
                    f"El campo '{field_name}' debe ser numérico."
                )
                return False

            self.item.lncv_values[field_name] = value

        self.item.write_lncv0 = self.write_lncv0_check.isChecked()

        if hasattr(self.item, "auto_update_lncv"):
            self.item.auto_update_lncv()

            for field_name, edit in self.edits.items():
                if field_name in self.item.lncv_values:
                    edit.setText(str(self.item.lncv_values[field_name]))

        self.item.update()
        return True

    def accept(self):
        if self.save_values():
            super().accept()

    def send_config(self):
        if not self.save_values():
            return

        if not getattr(self.item, "profile_key", None):
            QMessageBox.warning(
                self,
                "LocoNet",
                "Este elemento no tiene perfil LNCV asignado."
            )
            return

        if self.main_window is None:
            QMessageBox.warning(
                self,
                "LocoNet",
                "No se ha recibido la configuración principal de la aplicación."
            )
            return

        ln = getattr(self.main_window, "ln", None)

        if ln is None:
            QMessageBox.warning(
                self,
                "LocoNet",
                "No hay conexión LocoNet activa."
            )
            return

        article = self.item.get_article()
        module_addr = self.item.lncv_values.get("module_addr", 1)
        lncv_map = self.item.build_lncv_map()

        if not getattr(self.item, "write_lncv0", False):
            lncv_map.pop(0, None)

        try:
            responses = []

            responses.append(ln.lncv_start(article, module_addr))

            for cv, value in lncv_map.items():
                responses.append(
                    f"LNCV {cv}={value} -> {ln.lncv_write(cv, value)}"
                )

            responses.append(ln.lncv_stop())

            QMessageBox.information(
                self,
                "LocoNet",
                "Configuración enviada:\n\n" + "\n".join(responses)
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error LocoNet",
                str(e)
            )