import sys
import random
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QWidget, QMessageBox
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QPolygon, QCursor


class DrawingWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.shapes = []
        self.setMinimumSize(400, 300)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def add_shape(self, shape_info):
        self.shapes.append(shape_info)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        for shape_info in self.shapes:
            shape_type = shape_info['type']
            x, y = shape_info['pos']
            size = shape_info['size']
            color = shape_info['color']
            painter.setPen(QPen(color, 2))
            painter.setBrush(color)
            if shape_type == 'circle':
                painter.drawEllipse(x - size // 2, y - size // 2, size, size)
            elif shape_type == 'square':
                painter.drawRect(x - size // 2, y - size // 2, size, size)
            elif shape_type == 'triangle':
                height = int(size * 0.866)
                points = QPolygon([
                    QPoint(x, y - height // 2),
                    QPoint(x - size // 2, y + height // 2),
                    QPoint(x + size // 2, y + height // 2)
                ])
                painter.drawPolygon(points)

    def mousePressEvent(self, event):
        self.setFocus(Qt.FocusReason.MouseFocusReason)
        local_pos = event.position().toPoint()
        if event.button() == Qt.MouseButton.LeftButton:
            self.draw_shape('circle', local_pos)
        elif event.button() == Qt.MouseButton.RightButton:
            self.draw_shape('square', local_pos)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            global_pos = QCursor.pos()
            local_pos = self.mapFromGlobal(global_pos)
            self.draw_shape('triangle', local_pos)
        else:
            super().keyPressEvent(event)

    def draw_shape(self, shape_type, pos):
        size = random.randint(20, 100)  
        color = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        shape_info = {
            'type': shape_type,
            'pos': (pos.x(), pos.y()),
            'size': size,
            'color': color
        }
        self.add_shape(shape_info)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Рисовалка фигур")
        self.setGeometry(100, 100, 800, 600)
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        self.drawing_widget = DrawingWidget()
        layout.addWidget(self.drawing_widget)
        self.setCentralWidget(central_widget)
        print("Нажмите ЛКМ (круг), ПКМ (квадрат) или Пробел (треугольник). Фокус на рисующем поле устанавливается кликом.")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()