import sys
import json
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton,
    QSpinBox, QHeaderView
)

class TaskInputWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Task Input")
        self.resize(500, 300)
        self.layout = QVBoxLayout()

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Task Name", "Estimated Time (minutes)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Task")
        self.remove_button = QPushButton("Delete Selected Task")
        self.confirm_button = QPushButton("Confirm and Save Tasks")

        self.add_button.clicked.connect(self.add_task)
        self.remove_button.clicked.connect(self.remove_task)
        self.confirm_button.clicked.connect(self.confirm_tasks)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        button_layout.addWidget(self.confirm_button)

        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

        self.load_existing_tasks()

    def load_existing_tasks(self):
        if os.path.exists("today_tasks.json"):
            try:
                with open("today_tasks.json", "r", encoding="utf-8") as f:
                    tasks = json.load(f)
                for task in tasks:
                    self.add_task(task["task"], task["duration_min"])
            except Exception as e:
                print(f"⚠️ Unable to read today_tasks.json: {e}")

    def add_task(self, name="", duration=60):
        row = self.table.rowCount()
        self.table.insertRow(row)

        # 设置任务名
        name_item = QTableWidgetItem(name)
        self.table.setItem(row, 0, name_item)

        # 时间使用 SpinBox 设置
        duration_spin = QSpinBox()
        duration_spin.setRange(5, 600)
        duration_spin.setValue(duration)
        self.table.setCellWidget(row, 1, duration_spin)

    def remove_task(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            self.table.removeRow(selected_row)

    def confirm_tasks(self):
        tasks = []
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            duration_widget = self.table.cellWidget(row, 1)
            if name_item and name_item.text().strip():
                tasks.append({
                    "task": name_item.text(),
                    "duration_min": duration_widget.value()
                })
        with open("today_tasks.json", "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
        print("✅ Tasks have been saved to today_tasks.json")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TaskInputWindow()
    window.show()
    sys.exit(app.exec())

