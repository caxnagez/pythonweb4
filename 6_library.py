import sys, sqlite3, bcrypt, os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QFileDialog, QDialog, QComboBox, QStackedWidget, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QIcon, QIntValidator
from PyQt6.QtCore import Qt
from datetime import datetime
from PyQt6 import uic 

DB_NAME = "resources/dbase.db"

# --- Путь к дефолтной картинке — в папке resources в корне проекта ---
DEFAULT_IMAGE_PATH = os.path.join(os.path.dirname(__file__), 'resources', 'def.png')

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            year INTEGER NOT NULL,
            genre TEXT NOT NULL,
            image_path TEXT
        )
    """)
    conn.commit()
    conn.close()


def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


# === Окно просмотра книги ===
class BookViewDialog(QDialog):
    def __init__(self, book_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Просмотр книги")
        self.setGeometry(400, 200, 500, 400)

        layout = QVBoxLayout()

        # Извлекаем данные
        title, author, year, genre, img_path = book_data[1], book_data[2], book_data[3], book_data[4], book_data[5]

        # Текстовая информация
        info_layout = QVBoxLayout()
        info_layout.addWidget(QLabel(f"<h2>{title}</h2>"))
        info_layout.addWidget(QLabel(f"<b>Автор:</b> {author}"))
        info_layout.addWidget(QLabel(f"<b>Год:</b> {year}"))
        info_layout.addWidget(QLabel(f"<b>Жанр:</b> {genre}"))

        layout.addLayout(info_layout)

        # Изображение
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(img_path if img_path else DEFAULT_IMAGE_PATH).scaled(
            200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(pixmap)
        layout.addWidget(self.image_label)

        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        self.setLayout(layout)


# === Окно авторизации ===
class AuthWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Авторизация")
        self.setGeometry(300, 300, 300, 200)

        layout = QVBoxLayout()

        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Логин")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.login_btn = QPushButton("Войти")
        self.register_btn = QPushButton("Регистрация")

        layout.addWidget(QLabel("Логин:"))
        layout.addWidget(self.login_input)
        layout.addWidget(QLabel("Пароль:"))
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_btn)
        layout.addWidget(self.register_btn)

        self.setLayout(layout)

        self.login_btn.clicked.connect(self.login)
        self.register_btn.clicked.connect(self.register)

    def login(self):
        login = self.login_input.text()
        password = self.password_input.text()

        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE login = ?", (login,))
        result = cursor.fetchone()
        conn.close()

        if result and check_password(password, result[0]):
            self.accepted_login(login)
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")

    def register(self):
        login = self.login_input.text()
        password = self.password_input.text()

        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return

        try:
            hashed = hash_password(password)
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (login, password_hash) VALUES (?, ?)", (login, hashed))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Успех", "Пользователь зарегистрирован")
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Ошибка", "Логин уже существует")

    def accepted_login(self, login):
        self.main_window.show_main_window()


# === Главное окно ===
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Каталог библиотеки")
        self.setGeometry(100, 100, 1000, 600)
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)
        self.auth_window = AuthWindow(self)
        self.central_widget.addWidget(self.auth_window)
        self.library_window = LibraryWindow()
        self.central_widget.addWidget(self.library_window)
        self.central_widget.setCurrentWidget(self.auth_window)

    def show_main_window(self):
        self.central_widget.setCurrentWidget(self.library_window)


# === Окно библиотеки ===
class LibraryWindow(QWidget):  # <-- Важно: QWidget, а не QMainWindow
    def __init__(self):
        super().__init__()
        ui_path = os.path.join(os.path.dirname(__file__), 'ui/library.ui')
        uic.loadUi(ui_path, self)
        self.searchButton.clicked.connect(self.search_books)
        self.resetButton.clicked.connect(self.reset_search)
        self.addButton.clicked.connect(self.add_book)
        self.editButton.clicked.connect(self.edit_book)
        self.deleteButton.clicked.connect(self.delete_book)
        self.booksTable.cellDoubleClicked.connect(self.view_book)
        self.load_books()

    def load_books(self, filter_title="", filter_author=""):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        if filter_title or filter_author:
            query = "SELECT * FROM books WHERE title LIKE ? AND author LIKE ?"
            cursor.execute(query, (f"%{filter_title}%", f"%{filter_author}%"))
        else:
            cursor.execute("SELECT * FROM books")
        rows = cursor.fetchall()
        conn.close()

        self.booksTable.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.booksTable.setItem(i, 0, QTableWidgetItem(str(row[0])))
            self.booksTable.setItem(i, 1, QTableWidgetItem(row[1]))
            self.booksTable.setItem(i, 2, QTableWidgetItem(row[2]))
            self.booksTable.setItem(i, 3, QTableWidgetItem(str(row[3])))
            self.booksTable.setItem(i, 4, QTableWidgetItem(row[4]))

            # --- КАРТИНКА ---
            img_path = row[5] if row[5] else DEFAULT_IMAGE_PATH
            label = QLabel()
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pixmap = QPixmap(img_path)

            # Если изображение не загрузилось — используем дефолтное
            if pixmap.isNull():
                pixmap = QPixmap(DEFAULT_IMAGE_PATH)

            pixmap = pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            label.setPixmap(pixmap)
            self.booksTable.setCellWidget(i, 5, label)

    def search_books(self):
        title = self.searchTitleInput.text()
        author = self.searchAuthorInput.text()
        self.load_books(filter_title=title, filter_author=author)

    def reset_search(self):
        self.searchTitleInput.clear()
        self.searchAuthorInput.clear()
        self.load_books()

    def add_book(self):
        dialog = BookDialog(self, is_new=True)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_books()

    def edit_book(self):
        current_row = self.booksTable.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите книгу для редактирования")
            return

        book_id = int(self.booksTable.item(current_row, 0).text())
        dialog = BookDialog(self, book_id=book_id, is_new=False)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_books()

    def delete_book(self):
        current_row = self.booksTable.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите книгу для удаления")
            return

        book_id = int(self.booksTable.item(current_row, 0).text())
        reply = QMessageBox.question(self, "Подтверждение", "Удалить выбранную книгу?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
            conn.commit()
            conn.close()
            self.load_books()

    def view_book(self, row, col):
        book_id = int(self.booksTable.item(row, 0).text())
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        book = cursor.fetchone()
        conn.close()
        if book:
            dialog = BookViewDialog(book, self)
            dialog.exec()


# === Диалог добавления/редактирования книги ===
class BookDialog(QDialog):
    def __init__(self, parent=None, book_id=None, is_new=True):
        super().__init__(parent)
        self.book_id = book_id
        self.is_new = is_new
        self.setWindowTitle("Добавить/Редактировать книгу")
        self.setGeometry(400, 400, 400, 300)

        layout = QFormLayout()

        self.title_input = QLineEdit()
        self.author_input = QLineEdit()
        self.year_input = QLineEdit()
        # --- Ограничение ввода: только числа от 1000 до текущего года ---
        self.year_input.setValidator(QIntValidator(1000, datetime.now().year, self))

        self.genre_input = QComboBox()
        self.genre_input.addItems(["Фантастика", "Драма", "Фэнтези", "Детектив", "Роман", "Приключения", "Научная", "Другое"])
        self.image_input = QLineEdit()
        self.image_input.setReadOnly(True)
        self.browse_btn = QPushButton("Выбрать изображение")

        layout.addRow("Название:", self.title_input)
        layout.addRow("Автор:", self.author_input)
        layout.addRow("Год:", self.year_input)
        layout.addRow("Жанр:", self.genre_input)
        layout.addRow("Изображение:", self.image_input)
        layout.addRow("", self.browse_btn)

        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("ОК")
        self.cancel_btn = QPushButton("Отмена")
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)

        layout.addRow(btn_layout)

        self.setLayout(layout)

        if not is_new:
            self.load_book_data()

        self.browse_btn.clicked.connect(self.browse_image)
        self.ok_btn.clicked.connect(self.save_book)
        self.cancel_btn.clicked.connect(self.reject)

    def load_book_data(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM books WHERE id = ?", (self.book_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            self.title_input.setText(row[1])
            self.author_input.setText(row[2])
            self.year_input.setText(str(row[3]))  # Загрузка числа
            self.genre_input.setCurrentText(row[4])
            self.image_input.setText(row[5] or "")

    def browse_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", os.path.dirname(__file__), "Images (*.png *.jpg *.jpeg *.bmp)")
        if path:
            self.image_input.setText(path)

    def save_book(self):
        title = self.title_input.text()
        author = self.author_input.text()
        year_text = self.year_input.text()

        if not year_text:
            QMessageBox.warning(self, "Ошибка", "Поле 'Год' не может быть пустым")
            return

        if not year_text.isdigit():
            QMessageBox.warning(self, "Ошибка", "Год должен быть числом")
            return

        year = int(year_text)

        if year > datetime.now().year:
            QMessageBox.warning(self, "Ошибка", f"Год не может быть больше текущего ({datetime.now().year})")
            return

        genre = self.genre_input.currentText()
        image_path = self.image_input.text()

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        if self.is_new:
            cursor.execute("""
                INSERT INTO books (title, author, year, genre, image_path)
                VALUES (?, ?, ?, ?, ?)
            """, (title, author, year, genre, image_path))
        else:
            cursor.execute("""
                UPDATE books SET title=?, author=?, year=?, genre=?, image_path=?
                WHERE id=?
            """, (title, author, year, genre, image_path, self.book_id))
        conn.commit()
        conn.close()
        self.accept()


if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())