import sys
import json
from pathlib import Path

import serial.tools.list_ports

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout,
    QInputDialog, QMessageBox, QFileDialog, QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox, QComboBox
)
from PySide6.QtGui import QAction

from canvas import Canvas
from palette import PaletteListWidget
from loconet_bridge import LocoNetBridge

from constants import ModuleKind, TurnoutVariant, Direction
from modules.base_module import BaseModule
from modules import (
    TrackModule,
    TurnoutModule,
    SignalModule,
    RMModule,
    ButtonModule,
    AccessoryModule,
)


LOCONET_CONFIG_FILE = "config_loconet.json"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Editor gráfico LocoNet")
        self.resize(1200, 800)

        # Config bridge C#
        self.bridge_host = "127.0.0.1"
        self.bridge_port = 5555

        # Config LocoNet físico
        self.loconet_mode = "tcp"  # "tcp" o "serial"
        self.loconet_ip = "192.168.25.1"
        self.loconet_port = 1234
        self.com_port = "COM3"

        self.current_project_path = None

        self.load_loconet_config()
        self.create_menu()
        self.build_ui()
        self.ln = None
        self.connect_loconet_on_startup()

    # ==========================================================
    # UI
    # ==========================================================
    def build_ui(self):
        central = QWidget()
        layout = QHBoxLayout(central)

        self.palette = PaletteListWidget()
        self.palette.addItems([
            "Vía",
            "Desvío",
            "Señal",
            "RM",
            "Botón",
            "Accesorio",
        ])
        self.palette.setDragEnabled(True)

        self.canvas = Canvas()

        layout.addWidget(self.palette, 1)
        layout.addWidget(self.canvas, 6)

        self.setCentralWidget(central)

    # ==========================================================
    # MENÚS
    # ==========================================================
    def create_menu(self):
        menu_bar = self.menuBar()

        planning_menu = menu_bar.addMenu("Planning")

        new_action = QAction("Nuevo", self)
        new_action.triggered.connect(self.new_project)
        planning_menu.addAction(new_action)

        open_action = QAction("Abrir...", self)
        open_action.triggered.connect(self.open_project)
        planning_menu.addAction(open_action)

        save_action = QAction("Guardar", self)
        save_action.triggered.connect(self.save_project)
        planning_menu.addAction(save_action)

        save_as_action = QAction("Guardar como...", self)
        save_as_action.triggered.connect(self.save_project_as)
        planning_menu.addAction(save_as_action)

        loconet_menu = menu_bar.addMenu("LocoNet")

        config_action = QAction("Configurar conexión", self)
        config_action.triggered.connect(self.configure_loconet)
        loconet_menu.addAction(config_action)

        test_action = QAction("Probar bridge", self)
        test_action.triggered.connect(self.test_bridge)
        loconet_menu.addAction(test_action)

    # ==========================================================
    # CONFIG LOCONET
    # ==========================================================
    def connect_loconet_on_startup(self):
        try:
            self.ln = LocoNetBridge(self.bridge_host, self.bridge_port)
            self.ln.connect_bridge()

            print(self.ln.ping())

            if self.loconet_mode == "tcp":
                print(self.ln.connect_loconet(self.loconet_ip, self.loconet_port))
            else:
                print(self.ln.connect_serial(self.com_port))

            print("LocoNet conectado al iniciar.")

        except Exception as e:
            self.ln = None
            QMessageBox.warning(
                self,
                "LocoNet",
                f"No se pudo conectar automáticamente al LocoNet:\n{e}"
            )

    def closeEvent(self, event):
        try:
            if self.ln:
                self.ln.disconnect_loconet()
                self.ln.close()
                self.ln = None
        except Exception:
            pass

        event.accept()
    def load_loconet_config(self):
        path = Path(LOCONET_CONFIG_FILE)
        if not path.exists():
            self.save_loconet_config()
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.bridge_host = data.get("bridge_host", self.bridge_host)
            self.bridge_port = data.get("bridge_port", self.bridge_port)
            self.loconet_mode = data.get("mode", self.loconet_mode)
            self.loconet_ip = data.get("tcp_ip", self.loconet_ip)
            self.loconet_port = data.get("tcp_port", self.loconet_port)
            self.com_port = data.get("com_port", self.com_port)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Config LocoNet",
                f"No se pudo cargar {LOCONET_CONFIG_FILE}:\n{e}"
            )

    def save_loconet_config(self):
        data = {
            "bridge_host": self.bridge_host,
            "bridge_port": self.bridge_port,

            "mode": self.loconet_mode,

            "tcp_ip": self.loconet_ip,
            "tcp_port": self.loconet_port,

            "com_port": self.com_port,
        }

        with open(LOCONET_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def configure_loconet(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Configuración LocoNet")
    
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        layout.addLayout(form)
    
        bridge_host_edit = QLineEdit(self.bridge_host)
        bridge_port_edit = QLineEdit(str(self.bridge_port))
    
        form.addRow("Host bridge:", bridge_host_edit)
        form.addRow("Puerto bridge:", bridge_port_edit)
    
        mode_combo = QComboBox()
        mode_combo.addItems(["tcp", "serial"])
        mode_combo.setCurrentText(self.loconet_mode)
        form.addRow("Modo:", mode_combo)
    
        tcp_ip_edit = QLineEdit(self.loconet_ip)
        tcp_port_edit = QLineEdit(str(self.loconet_port))
    
        form.addRow("IP LocoNet:", tcp_ip_edit)
        form.addRow("Puerto LocoNet:", tcp_port_edit)
    
        ports = [p.device for p in serial.tools.list_ports.comports()]
        if not ports:
            ports = [self.com_port]
    
        com_combo = QComboBox()
        com_combo.addItems(ports)
        com_combo.setCurrentText(self.com_port)
    
        form.addRow("Puerto COM:", com_combo)
    
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        layout.addWidget(buttons)
    
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
    
        def update_mode():
            is_tcp = mode_combo.currentText() == "tcp"
            tcp_ip_edit.setEnabled(is_tcp)
            tcp_port_edit.setEnabled(is_tcp)
            com_combo.setEnabled(not is_tcp)
    
        mode_combo.currentTextChanged.connect(update_mode)
        update_mode()
    
        if dialog.exec() != QDialog.Accepted:
            return
    
        self.bridge_host = bridge_host_edit.text()
        self.bridge_port = int(bridge_port_edit.text())
    
        self.loconet_mode = mode_combo.currentText()
    
        self.loconet_ip = tcp_ip_edit.text()
        self.loconet_port = int(tcp_port_edit.text())
    
        self.com_port = com_combo.currentText()
    
        self.save_loconet_config()
    
        QMessageBox.information(
            self,
            "LocoNet",
            "Configuración guardada correctamente"
        )

    # ---- Mostrar / ocultar según modo ----
    def update_mode():
        is_tcp = mode_combo.currentText() == "tcp"
        tcp_ip_edit.setEnabled(is_tcp)
        tcp_port_edit.setEnabled(is_tcp)
        com_combo.setEnabled(not is_tcp)

        mode_combo.currentTextChanged.connect(update_mode)
        update_mode()

        # ---- Ejecutar ----
        if dialog.exec() != QDialog.Accepted:
            return

        # ---- Guardar ----
        self.bridge_host = bridge_host_edit.text()
        self.bridge_port = int(bridge_port_edit.text())

        self.loconet_mode = mode_combo.currentText()

        self.loconet_ip = tcp_ip_edit.text()
        self.loconet_port = int(tcp_port_edit.text())

        self.com_port = com_combo.currentText()

        self.save_loconet_config()

        QMessageBox.information(
            self,
            "LocoNet",
            "Configuración guardada correctamente"
        )

    def test_bridge(self):
        try:
            ln = LocoNetBridge(self.bridge_host, self.bridge_port)
            ln.connect_bridge()

            r1 = ln.ping()

            if self.loconet_mode == "tcp":
                r2 = ln.connect_loconet(self.loconet_ip, self.loconet_port)
            else:
                r2 = ln.connect_serial(self.com_port)

            ln.close()

            QMessageBox.information(
                self,
                "Bridge LocoNet",
                f"{r1}\n{r2}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error LocoNet",
                str(e)
            )

    # ==========================================================
    # PLANNING JSON
    # ==========================================================
    def new_project(self):
        self.canvas.grid_scene.clear()
        self.canvas.grid_scene.occupied.clear()
        self.current_project_path = None
        self.setWindowTitle("Editor gráfico LocoNet - Nuevo planning")

    def open_project(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir planning",
            "",
            "Planning LocoNet (*.json)"
        )

        if not path:
            return

        self.load_project_from_path(path)

    def save_project(self):
        if not self.current_project_path:
            self.save_project_as()
            return

        self.save_project_to_path(self.current_project_path)

    def save_project_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar planning",
            "",
            "Planning LocoNet (*.json)"
        )

        if not path:
            return

        if not path.lower().endswith(".json"):
            path += ".json"

        self.current_project_path = path
        self.save_project_to_path(path)

    def save_project_to_path(self, path):
        modules = []

        for item in self.canvas.grid_scene.items():
            if isinstance(item, BaseModule):
                modules.append(self.module_to_dict(item))

        data = {
            "version": 1,
            "type": "loconet_planning",
            "modules": modules,
        }

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.setWindowTitle(f"Editor gráfico LocoNet - {path}")

            QMessageBox.information(
                self,
                "Planning",
                "Planning guardado correctamente."
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo guardar el planning:\n{e}"
            )

    def load_project_from_path(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.canvas.grid_scene.clear()
            self.canvas.grid_scene.occupied.clear()

            for module_data in data.get("modules", []):
                item = self.dict_to_module(module_data)

                if item:
                    self.canvas.grid_scene.add_module(item)

            self.current_project_path = path
            self.setWindowTitle(f"Editor gráfico LocoNet - {path}")

            QMessageBox.information(
                self,
                "Planning",
                "Planning cargado correctamente."
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo cargar el planning:\n{e}"
            )

    # ==========================================================
    # SERIALIZACIÓN DE MÓDULOS
    # ==========================================================
    def module_to_dict(self, item):
        data = {
            "kind": item.kind.name,
            "col": item.col,
            "row": item.row,
            "name": item.name,
            "direction": item.direction.name,
            "profile_key": item.profile_key,
            "lncv_values": item.lncv_values,
        }

        if hasattr(item, "variant"):
            data["variant"] = item.variant.name

        if isinstance(item, SignalModule):
            data["signal_name"] = item.signal_name
            data["signal_colors"] = item.signal_colors
            data["signal_style"] = item.signal_style

        return data

    def dict_to_module(self, data):
        kind = ModuleKind[data["kind"]]
        col = data.get("col", 0)
        row = data.get("row", 0)

        if kind == ModuleKind.TRACK:
            item = TrackModule(col, row)

        elif kind == ModuleKind.TURNOUT:
            item = TurnoutModule(col, row)

        elif kind == ModuleKind.SIGNAL:
            item = SignalModule(col, row)

        elif kind == ModuleKind.RM:
            item = RMModule(col, row)

        elif kind == ModuleKind.BUTTON:
            item = ButtonModule(col, row)

        elif kind == ModuleKind.ACCESSORY:
            item = AccessoryModule(col, row)

        else:
            return None

        item.name = data.get("name", item.name)

        direction_name = data.get("direction", "LEFT_TO_RIGHT")
        if direction_name in Direction.__members__:
            item.direction = Direction[direction_name]

        item.profile_key = data.get("profile_key", item.profile_key)
        item.lncv_values = data.get("lncv_values", item.lncv_values)

        if "variant" in data and hasattr(item, "variant"):
            variant_name = data["variant"]

            if variant_name in TurnoutVariant.__members__:
                item.variant = TurnoutVariant[variant_name]

        if isinstance(item, SignalModule):
            item.signal_name = data.get("signal_name", item.signal_name)
            item.signal_colors = data.get("signal_colors", item.signal_colors)
            item.signal_style = data.get("signal_style", item.signal_style)

        return item


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())