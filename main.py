import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton
)

# 导入三个窗口类
from task_input import TaskInputWindow
from task_progress import TaskProgressWindow
from chat_dialog import ChatDialogWindow
from settings_window import SettingsWindow

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Task Manager")
        self.resize(300, 250)

        layout = QVBoxLayout()

        # 功能按钮
        self.input_button = QPushButton("1️⃣ Enter Tasks")
        self.chat_button = QPushButton("2️⃣ Start Task Coach (ChatGPT)")
        self.progress_button = QPushButton("3️⃣ Real-Time Progress Tracking")
        self.settings_button = QPushButton("⚙️ Settings")
        
        self.input_button.clicked.connect(self.open_input)
        self.chat_button.clicked.connect(self.open_chat)
        self.progress_button.clicked.connect(self.open_progress)
        self.settings_button.clicked.connect(self.open_settings)

        layout.addWidget(self.input_button)
        layout.addWidget(self.chat_button)
        layout.addWidget(self.progress_button)
        layout.addWidget(self.settings_button)

        self.setLayout(layout)

    def open_input(self):
        self.input_window = TaskInputWindow()
        self.input_window.show()

    def open_chat(self):
        self.chat_window = ChatDialogWindow()
        self.chat_window.show()

    def open_progress(self):
        self.progress_window = TaskProgressWindow()
        self.progress_window.show()

    def open_settings(self):
        self.settings_window = SettingsWindow()
        self.settings_window.show()

    def closeEvent(self, event):
        for filename in ["memory.json", "today_tasks.json","today_schedule.json"]:
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                    print(f"[Cleanup] Deleted: {filename}")
                except Exception as e:
                    print(f"[Failed] Unable to delete {filename}: {e}")
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
