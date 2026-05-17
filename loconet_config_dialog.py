from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QLineEdit, QRadioButton, QGroupBox,
    QPushButton, QHBoxLayout
)


class LocoNetConfigDialog(QDialog):
    def __init__(self, main_window):
        super().__init__()

        self.main = main_window
        self.setWindowTitle("Configuración LocoNet")

        layout = QVBoxLayout(self)

        # =========================
        # Bridge
        # =========================
        bridge_group = QGroupBox("Bridge C#")
        bridge_layout = QFormLayout()

        self.host_edit = QLineEdit(self.main.bridge_host)
        self.port_edit = QLineEdit(str(self.main.bridge_port))

        bridge_layout.addRow("Host:", self.host_edit)
        bridge_layout.addRow("Puerto:", self.port_edit)

        bridge_group.setLayout(bridge_layout)
        layout.addWidget(bridge_group)

        # =========================
        # Modo
        # =========================
        mode_group = QGroupBox("Modo LocoNet")
        mode_layout = QVBoxLayout()

        self.tcp_radio = QRadioButton("TCP")
        self.serial_radio = QRadioButton("Serial")

        if self.main.loconet_mode == "tcp":
            self.tcp_radio.setChecked(True)
        else:
            self.serial_radio.setChecked(True)

        mode_layout.addWidget(self.tcp_radio)
        mode_layout.addWidget(self.serial_radio)

        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # =========================
        # TCP
        # =========================
        tcp_group = QGroupBox("TCP")
        tcp_layout = QFormLayout()

        self.ip_edit = QLineEdit(self.main.loconet_ip)
        self.tcp_port_edit = QLineEdit(str(self.main.loconet_port))

        tcp_layout.addRow("IP:", self.ip_edit)
        tcp_layout.addRow("Puerto:", self.tcp_port_edit)

        tcp_group.setLayout(tcp_layout)
        layout.addWidget(tcp_group)

        # =========================
        # Serial
        # =========================
        serial_group = QGroupBox("Serial")
        serial_layout = QFormLayout()

        self.com_edit = QLineEdit(self.main.com_port)

        serial_layout.addRow("COM:", self.com_edit)

        serial_group.setLayout(serial_layout)
        layout.addWidget(serial_group)

        # =========================
        # Botones
        # =========================
        btn_layout = QHBoxLayout()

        ok_btn = QPushButton("Guardar")
        ok_btn.clicked.connect(self.accept)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def apply(self):
        self.main.bridge_host = self.host_edit.text()
        self.main.bridge_port = int(self.port_edit.text())

        if self.tcp_radio.isChecked():
            self.main.loconet_mode = "tcp"
        else:
            self.main.loconet_mode = "serial"

        self.main.loconet_ip = self.ip_edit.text()
        self.main.loconet_port = int(self.tcp_port_edit.text())

        self.main.com_port = self.com_edit.text()