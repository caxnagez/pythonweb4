import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QKeyEvent
from PyQt6 import uic
from pathlib import Path


class UFOGameWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        if getattr(sys, 'frozen', False):
            ui_path = os.path.join(sys._MEIPASS, 'ui', 'ufo.ui')
        else:
            ui_path = os.path.join(os.path.dirname(__file__), 'ui', 'ufo.ui')
        if not os.path.exists(ui_path):
            QMessageBox.critical(self, f"Файл не найден\n{ui_path}")
            sys.exit(1)
        uic.loadUi(ui_path, self)
        self.background_label = self.findChild(QLabel, "backgroundLabel")
        if not self.background_label:
            QMessageBox.critical(self, "Ошибка", "QLabel 'backgroundLabel' не найден в UI.")
            sys.exit(1)
        ufo_path = os.path.join(os.path.dirname(__file__), 'resources', 'ufo.png')
        if getattr(sys, 'frozen', False):
            ufo_path = os.path.join(sys._MEIPASS, 'resources', 'ufo.png')
        else:
            ufo_path = os.path.join(os.path.dirname(__file__), 'resources', 'ufo.png')

        if not os.path.exists(ufo_path):
            print(f"Изображение НЛО не найдено по пути: {ufo_path}, будет использован 🛸")
            self.ufo_label = QLabel("🛸", self.background_label)
            self.ufo_label.setStyleSheet("font-size: 40px;")
            self.ufo_label.resize(150, 150)
        else:
            self.ufo_label = QLabel(self.background_label)
            pixmap = QPixmap(ufo_path)
            if pixmap.isNull():
                print(f"Не удалось загрузить изображение: {ufo_path}, будет использован 🛸")
                self.ufo_label.setText("🛸")
                self.ufo_label.setStyleSheet("font-size: 40px;")
                self.ufo_label.resize(150, 150)
            else:
                scaled_pixmap = pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.ufo_label.setPixmap(scaled_pixmap)
                self.ufo_label.resize(scaled_pixmap.size())
        window_width = self.background_label.width()
        window_height = self.background_label.height()
        ufo_width = self.ufo_label.width()
        ufo_height = self.ufo_label.height()
        self.x_pos = (window_width - ufo_width) // 2
        self.y_pos = (window_height - ufo_height) // 2
        self.ufo_label.move(self.x_pos, self.y_pos)
        self.step_size = 20
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()

        print("Используйте стрелки для управления UFO")


    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        moved = False
        if key == Qt.Key.Key_Left:
            self.x_pos -= self.step_size
            moved = True
        elif key == Qt.Key.Key_Right:
            self.x_pos += self.step_size
            moved = True
        elif key == Qt.Key.Key_Up:
            self.y_pos -= self.step_size
            moved = True
        elif key == Qt.Key.Key_Down:
            self.y_pos += self.step_size
            moved = True
        if moved:
            bg_width = self.background_label.width()
            bg_height = self.background_label.height()
            ufo_width = self.ufo_label.width()
            ufo_height = self.ufo_label.height()
            if self.x_pos < -ufo_width:
                self.x_pos = bg_width  
            elif self.x_pos > bg_width:
                self.x_pos = -ufo_width  
            if self.y_pos < -ufo_height:
                self.y_pos = bg_height 
            elif self.y_pos > bg_height:
                self.y_pos = -ufo_height
            self.ufo_label.move(self.x_pos, self.y_pos)

def main():
    app = QApplication(sys.argv)
    window = UFOGameWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()