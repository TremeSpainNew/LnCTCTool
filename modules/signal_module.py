# modules/signal_module.py

from PySide6.QtWidgets import QMenu
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPen, QColor, QBrush

from constants import (
    MODULE_W, MODULE_H, ModuleKind, Direction,
    SIGNAL_VARIANTS, color_from_name
)
from modules.base_module import BaseModule
from config_dialog import ModuleConfigDialog


class SignalModule(BaseModule):
    def __init__(self, col, row, shunt=False):
        super().__init__(col, row, ModuleKind.SIGNAL)

        self.name = "S"

        self.signal_name = "Verde/Rojo"
        self.signal_colors = ["green", "red"]
        self.signal_style = "normal"  # "normal" o "mono_bajo"

    # ==========================================================
    # DIBUJO PRINCIPAL
    # ==========================================================
    def draw_module(self, painter):
        if self.signal_style == "mono_bajo":
            self.draw_mono_bajo(painter)
        else:
            self.draw_normal_signal(painter)

    # ==========================================================
    # SEÑAL NORMAL
    # ==========================================================
    def draw_normal_signal(self, painter):
        y = MODULE_H / 2
        cx = MODULE_W / 2

        top_signal = self.direction == Direction.LEFT_TO_RIGHT

        painter.setPen(Qt.NoPen)

        # vía
        painter.setBrush(QBrush(QColor("black")))
        painter.drawRect(QRectF(0, y - 5, MODULE_W, 10))

        # botón central
        painter.setBrush(QBrush(QColor("#888888")))
        painter.setPen(QPen(QColor("black"), 1))
        painter.drawEllipse(QPointF(cx, y), 10, 10)

        count = len(self.signal_colors)
        box_w = 8 + count * 12
        box_h = 14

        if top_signal:
            box_x = 10
            box_y = 7
            tail_x = box_x + box_w - 1
            tail_y = box_y + 5
            draw_colors = self.signal_colors
        else:
            box_x = MODULE_W - 10 - box_w
            box_y = MODULE_H - 20
            tail_x = box_x - 10
            tail_y = box_y + 5
            draw_colors = list(reversed(self.signal_colors))

        # cabeza
        painter.setBrush(QBrush(QColor("black")))
        painter.drawRoundedRect(QRectF(box_x, box_y, box_w, box_h), 6, 6)

        # rabillo
        painter.drawRect(QRectF(tail_x, tail_y, 11, 4))

        # focos
        for i, color_name in enumerate(draw_colors):
            painter.setBrush(QBrush(color_from_name(color_name)))
            painter.drawEllipse(
                QPointF(box_x + 10 + i * 12, box_y + 6),
                5,
                5
            )

    # ==========================================================
    # MONO BAJO
    # ==========================================================
    def draw_mono_bajo(self, painter):
        y = MODULE_H / 2
        cx = MODULE_W / 2

        top_signal = self.direction == Direction.LEFT_TO_RIGHT

        painter.setPen(Qt.NoPen)

        # vía
        painter.setBrush(QBrush(QColor("black")))
        painter.drawRect(QRectF(0, y - 5, MODULE_W, 10))

        # botón central
        painter.setBrush(QBrush(QColor("#888888")))
        painter.setPen(QPen(QColor("black"), 1))
        painter.drawEllipse(QPointF(cx, y), 10, 10)

        lamp_radius = 5
        lamp_step = 12
        gap_to_track = 2
        row_h = 14
        row_gap = 2

        lamps = self.signal_colors  # ahora en mono bajo son tuplas: (color, col, row)

        rows_used = {row for _, _, row in lamps}
        double_row = len(rows_used) > 1

        if double_row:
            box_w = 8 + 2 * lamp_step
            total_h = row_h * 2 + row_gap
        else:
            box_w = 8 + len(lamps) * lamp_step
            total_h = row_h

        if top_signal:
            box_x = 10
            box_y = y - 5 - gap_to_track - total_h
        else:
            box_x = MODULE_W - 10 - box_w
            box_y = y + 5 + gap_to_track

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("black")))

        painter.drawRoundedRect(QRectF(box_x, box_y, box_w, row_h), 6, 6)

        if double_row:
            painter.drawRoundedRect(
                QRectF(box_x, box_y + row_h + row_gap, box_w, row_h),
                6,
                6
            )

        for color_name, col, row in lamps:
            if not top_signal:
                col = 1 - col
                row = 1 - row

            lamp_x = box_x + 10 + col * lamp_step

            if double_row:
                lamp_y = box_y + row * (row_h + row_gap) + row_h / 2
            else:
                lamp_y = box_y + row_h / 2

            painter.setBrush(QBrush(color_from_name(color_name)))
            painter.drawEllipse(
                QPointF(lamp_x, lamp_y),
                lamp_radius,
                lamp_radius
            )

    # ==========================================================
    # MENU
    # ==========================================================
    def contextMenuEvent(self, event):
        menu = QMenu()

        for group, items in SIGNAL_VARIANTS.items():
            sub = menu.addMenu(group)

            for name, colors, style in items:
                act = sub.addAction(name)
                act.triggered.connect(
                    lambda checked=False, n=name, c=colors, s=style:
                    self.set_signal_variant(n, c, s)
                )

        menu.addSeparator()

        direction_menu = menu.addMenu("Sentido")

        for direction in Direction:
            act = direction_menu.addAction(direction.value)
            act.triggered.connect(
                lambda checked=False, d=direction:
                self.set_direction(d)
            )

        menu.addSeparator()

        cfg = menu.addAction("Configurar")
        delete = menu.addAction("Eliminar")

        selected = menu.exec(event.screenPos())

        if selected == cfg:
            ModuleConfigDialog(self).exec()
        elif selected == delete and self.scene():
            self.scene().remove_module(self)

    # ==========================================================
    # SETTERS
    # ==========================================================
    def set_signal_variant(self, name, colors, style):
        self.signal_name = name
        self.signal_colors = colors
        self.signal_style = style
        self.update()