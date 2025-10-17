import sys
import random
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox

from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QCursor
from PyQt6 import uic
import os
from pathlib import Path


class EscapingButtonWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/button.ui", self)
        self.escape_button = self.findChild(QPushButton, "escapeButton")
        self.original_enter_event = self.escape_button.enterEvent
        self.escape_button.enterEvent = self.on_button_hover

    def on_button_hover(self, event):
        self.move_button_randomly()

    def move_button_randomly(self):
        central_widget = self.centralWidget()
        if not central_widget:
            return

        window_rect = central_widget.rect()
        button_size = self.escape_button.size()
        max_x = window_rect.width() - button_size.width()
        max_y = window_rect.height() - button_size.height()

        if max_x > 0 and max_y > 0:
            new_x = random.randint(0, max_x)
            new_y = random.randint(0, max_y)
            self.escape_button.move(new_x, new_y)

def main():
    app = QApplication(sys.argv)
    window = EscapingButtonWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()