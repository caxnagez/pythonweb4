import sys
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QMessageBox,QDialog, QFormLayout, QLineEdit, QSpinBox, QComboBox, QPushButton, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6 import uic


class FilmDatabaseManager:
    def __init__(self, db_path: str):
        if not os.path.exists(db_path):
            QMessageBox.critical(None, f"Файл базы данных не найден:\n{db_path}")
            sys.exit(1)
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def get_films_with_genres(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT f.id, f.title, f.year, f.duration, g.title AS genre
            FROM films f
            JOIN genres g ON f.genre = g.id
            ORDER BY f.title
        """)
        return cur.fetchall()

    def get_column_names(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT f.id, f.title, f.year, f.duration, g.title AS genre
            FROM films f
            JOIN genres g ON f.genre = g.id
            LIMIT 0
        """)
        return [desc[0] for desc in cur.description]

    def get_all_genres(self):
        cur = self.conn.cursor()
        cur.execute("SELECT id, title FROM genres ORDER BY title")
        return [(row[0], row[1]) for row in cur.fetchall()]

    def add_film(self, title, year, duration, genre_id):
        cur = self.conn.cursor()
        cur.execute("INSERT INTO films (title, year, duration, genre) VALUES (?, ?, ?, ?)",
                    (title, year, duration, genre_id))
        self.conn.commit()

    def update_film(self, film_id, title, year, duration, genre_id):
        cur = self.conn.cursor()
        cur.execute("UPDATE films SET title=?, year=?, duration=?, genre=? WHERE id=?",
                    (title, year, duration, genre_id, film_id))
        self.conn.commit()

    def delete_film(self, film_id):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM films WHERE id=?", (film_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()


class FilmFormDialog(QDialog):
    def __init__(self, genres, film_data=None, parent=None):
        super().__init__(parent)
        self.genres = genres
        self.film_data = film_data
        self.setWindowTitle("Изменить фильм" if film_data else "Добавить фильм")
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout(self)
        self.title_edit = QLineEdit()
        self.year_spin = QSpinBox()
        self.year_spin.setRange(1888, datetime.now().year + 1)
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 1000)
        self.genre_combo = QComboBox()
        for gid, gname in self.genres:
            self.genre_combo.addItem(gname, gid)
        layout.addRow("Название:", self.title_edit)
        layout.addRow("Год:", self.year_spin)
        layout.addRow("Длительность (мин):", self.duration_spin)
        layout.addRow("Жанр:", self.genre_combo)
        if self.film_data:
            self.title_edit.setText(self.film_data["title"])
            self.year_spin.setValue(self.film_data["year"])
            self.duration_spin.setValue(self.film_data["duration"])
            idx = self.genre_combo.findData(self.film_data["genre_id"])
            if idx != -1:
                self.genre_combo.setCurrentIndex(idx)
        btn_layout = QVBoxLayout()
        self.ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Отмена")
        self.ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)
        self.title_edit.textChanged.connect(self.validate)
        self.validate()

    def validate(self):
        self.ok_btn.setEnabled(len(self.title_edit.text().strip()) > 0)

    def get_data(self):
        return (
            self.title_edit.text().strip(),
            self.year_spin.value(),
            self.duration_spin.value(),
            self.genre_combo.currentData())

class MainWindow(QMainWindow):
    def __init__(self, db_path):
        super().__init__()
        uic.loadUi("ui/films.ui", self)
        self.db = FilmDatabaseManager(db_path)
        self.btnAdd.clicked.connect(self.add_film)
        self.btnEdit.clicked.connect(self.edit_film)
        self.btnDelete.clicked.connect(self.delete_film)
        self.tableWidget.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.load_data()

    def load_data(self):
        films = self.db.get_films_with_genres()
        columns = self.db.get_column_names()
        self.tableWidget.setRowCount(len(films))
        self.tableWidget.setColumnCount(len(columns))
        self.tableWidget.setHorizontalHeaderLabels(columns)
        for row_idx, film in enumerate(films):
            for col_idx, col_name in enumerate(columns):
                item = QTableWidgetItem(str(film[col_name]))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tableWidget.setItem(row_idx, col_idx, item)
        header = self.tableWidget.horizontalHeader()
        header.setStretchLastSection(True)
        for i in range(len(columns) - 1):
            header.setSectionResizeMode(i, header.ResizeMode.ResizeToContents)

    def on_selection_changed(self):
        has_sel = bool(self.tableWidget.selectionModel().selectedRows())
        self.btnEdit.setEnabled(has_sel)
        self.btnDelete.setEnabled(has_sel)

    def get_selected_film(self):
        rows = self.tableWidget.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        columns = self.db.get_column_names()
        film = {}
        for i, col in enumerate(columns):
            val = self.tableWidget.item(row, i).text()
            try:
                film[col] = int(val)
            except ValueError:
                film[col] = val
        cur = self.db.conn.cursor()
        cur.execute("SELECT genre FROM films WHERE id=?", (film["id"],))
        res = cur.fetchone()
        if res:
            film["genre_id"] = res[0]
        return film

    def add_film(self):
        genres = self.db.get_all_genres()
        if not genres:
            QMessageBox.warning(self, "Нет жанров в базе.")
            return

        dialog = FilmFormDialog(genres, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            title, year, duration, genre_id = dialog.get_data()
            if not title:
                QMessageBox.warning(self, "Название не может быть пустым.")
                return
            if year > datetime.now().year:
                QMessageBox.warning(self, "Год не может быть из будущего.")
                return
            if duration <= 0:
                QMessageBox.warning(self, "Длительность должна быть положительной.")
                return
            try:
                self.db.add_film(title, year, duration, genre_id)
                self.load_data()
                QMessageBox.information(self, "Фильм успешно добавлен.")
            except Exception as e:
                QMessageBox.critical(self, f"Не удалось добавить фильм:\n{e}")

    def edit_film(self):
        film = self.get_selected_film()
        if not film:
            QMessageBox.warning(self, "Выберите фильм для редактирования.")
            return

        genres = self.db.get_all_genres()
        if not genres:
            QMessageBox.warning(self, "Нет жанров в базе.")
            return

        dialog = FilmFormDialog(genres, film_data=film, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            title, year, duration, genre_id = dialog.get_data()
            if not title:
                QMessageBox.warning(self, "Название не может быть пустым.")
                return
            if year > datetime.now().year:
                QMessageBox.warning(self, "Год не может быть из будущего.")
                return
            if duration <= 0:
                QMessageBox.warning(self, "Длительность должна быть положительной.")
                return
            try:
                self.db.update_film(film["id"], title, year, duration, genre_id)
                self.load_data()
                QMessageBox.information(self, "Фильм успешно обновлён.")
            except Exception as e:
                QMessageBox.critical(self, f"Не удалось обновить фильм:\n{e}")

    def delete_film(self):
        film = self.get_selected_film()
        if not film:
            QMessageBox.warning(self, "Выберите фильм для удаления.")
            return
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить фильм «{film['title']}»?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_film(film["id"])
                self.load_data()
                QMessageBox.information(self, "Фильм успешно удалён.")
            except Exception as e:
                QMessageBox.critical(self, f"Не удалось удалить фильм:\n{e}")

    def closeEvent(self, event):
        self.db.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    db_file = "resources/films_db.sqlite"
    if not os.path.exists(db_file):
        QMessageBox.critical(None, "Файл базы данных '{db_file}' не найден в текущей папке.")
        sys.exit(1)

    window = MainWindow(db_file)
    window.show()
    sys.exit(app.exec())