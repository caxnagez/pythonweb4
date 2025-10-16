import sys
import csv
import os
from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QComboBox
from PyQt6.QtGui import QColor


class OlympiadApp(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/olimp.ui", self)
        self.setWindowTitle("Результаты")
        self.resize(800, 600)
        self.data = []
        self.schools = set()
        self.classes = set()
        self.load_data("tables\olimp.csv")
        self.school_combo.addItem("Все")
        self.class_combo.addItem("Все")
        self.school_combo.addItems(sorted(self.schools))
        self.class_combo.addItems(sorted(self.classes))
        self.school_combo.currentTextChanged.connect(self.apply_filters)
        self.class_combo.currentTextChanged.connect(self.apply_filters)
        self.apply_filters()

    def load_data(self, filename):
        if not os.path.exists(filename):
            print(f"ФаЙЛ'{filename}' не найден.")
            return
        self.data.clear()
        self.schools.clear()
        self.classes.clear()
        try:
            with open(filename, newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader) 

                for row in reader:
                    if len(row) < 8:
                        continue
                    user_name = row[1]
                    login = row[2]
                    score_str = row[7]
                    if login.startswith("sh-kaluga16-"):
                        parts = login.split('-')
                        if len(parts) >= 5:
                            school = parts[2]
                            class_num = parts[3]
                            try:
                                score = int(score_str) if score_str.isdigit() else 0
                                self.schools.add(school)
                                self.classes.add(class_num)
                                self.data.append({
                                    'login': login,
                                    'name': user_name,
                                    'score': score,
                                    'school': school,
                                    'class': class_num
                                })
                            except ValueError:
                                continue
        except Exception as e:
            print(f"Ошибка при чтении файла: {e}")

    def apply_filters(self):
        selected_school = self.school_combo.currentText()
        selected_class = self.class_combo.currentText()
        filtered = []
        for entry in self.data:
            match_school = (selected_school == "Все") or (entry['school'] == selected_school)
            match_class = (selected_class == "Все") or (entry['class'] == selected_class)
            if match_school and match_class:
                filtered.append(entry)
        filtered.sort(key=lambda x: x['score'], reverse=True)
        places = {}
        if filtered:
            rank = 1
            prev_score = filtered[0]['score']
            for entry in filtered:
                if entry['score'] != prev_score:
                    rank += 1
                    prev_score = entry['score']
                places[entry['login']] = rank      
        self.table.setRowCount(len(filtered))
        for row_idx, entry in enumerate(filtered):
            self.table.setItem(row_idx, 0, QTableWidgetItem(entry['login']))
            self.table.setItem(row_idx, 1, QTableWidgetItem(entry['name']))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(entry['score'])))
            place = places[entry['login']]
            color = None
            if place == 1:
                color = QColor(255, 215, 0) 
            elif place == 2:
                color = QColor(192, 192, 192) 
            elif place == 3:
                color = QColor(205, 127, 50) 

            if color:
                for col in range(3):
                    self.table.item(row_idx, col).setBackground(color)

        self.table.resizeColumnsToContents()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OlympiadApp()
    window.show()
    sys.exit(app.exec())