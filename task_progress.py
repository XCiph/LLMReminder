import sys
import json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QSlider, QLabel, QHBoxLayout, QHeaderView
)
from PyQt6.QtCore import Qt

class TaskProgressWindow(QWidget):
    def __init__(self, schedule_file="today_schedule.json"):
        super().__init__()
        self.setWindowTitle("Task Progress Tracking")
        self.resize(600, 400)

        self.schedule_file = schedule_file
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.table = QTableWidget()
        self.layout.addWidget(self.table)

        self.load_schedule()
        self.setup_table()

    def load_schedule(self):
        with open(self.schedule_file, "r", encoding="utf-8") as f:
            self.schedule = json.load(f)

    def setup_table(self):
        self.table.setRowCount(len(self.schedule))
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Task", "Start Time", "End Time", "Progress"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        for row, item in enumerate(self.schedule):
            self.table.setItem(row, 0, QTableWidgetItem(item["task"]))
            self.table.setItem(row, 1, QTableWidgetItem(item["start"]))
            self.table.setItem(row, 2, QTableWidgetItem(item["end"]))

            slider_widget = QWidget()
            slider_layout = QHBoxLayout()
            slider_layout.setContentsMargins(0, 0, 0, 0)

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(item["progress"])
            label = QLabel(f"{item['progress']}%")

            def make_slider_callback(r, s=slider, l=label):
                def on_value_change(val):
                    l.setText(f"{val}%")
                    self.schedule[r]["progress"] = val
                    self.save_schedule()
                return on_value_change

            slider.valueChanged.connect(make_slider_callback(row, slider, label))

            slider_layout.addWidget(slider)
            slider_layout.addWidget(label)
            slider_widget.setLayout(slider_layout)

            self.table.setCellWidget(row, 3, slider_widget)

    def save_schedule(self):
        with open(self.schedule_file, "w", encoding="utf-8") as f:
            json.dump(self.schedule, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TaskProgressWindow()
    window.show()
    sys.exit(app.exec())
