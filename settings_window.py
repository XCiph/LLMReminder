from PyQt6.QtWidgets import (
    QWidget, QLineEdit, QVBoxLayout, QPushButton, QFormLayout, QMessageBox
)
from config import get_config, CONFIG_PATH
import json

def save_config(data):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Setting")
        self.resize(400, 300)

        self.config = get_config()

        layout = QVBoxLayout()
        form = QFormLayout()

        self.user_name_input = QLineEdit(self.config.get("user_alias", "Ciph"))
        self.assistant_name_input = QLineEdit(self.config.get("assistant_alias", "5am0y3d"))
        self.user_callout_input = QLineEdit(self.config.get("user_callout", "Ciph"))
        self.user_description_input = QLineEdit(self.config.get("user_self_description", ""))
        self.assistant_personality_input = QLineEdit(self.config.get("assistant_personality", ""))
        self.assistant_expectation_input = QLineEdit(self.config.get("assistant_expectation", ""))

        form.addRow("Your Name", self.user_name_input)
        form.addRow("How You Call Me", self.assistant_name_input)
        form.addRow("How I Call You", self.user_callout_input)
        form.addRow("Who You Are (Self Description)", self.user_description_input)
        form.addRow("Who I Am (Personality Description)", self.assistant_personality_input)
        form.addRow("How You Expect Me to Treat You", self.assistant_expectation_input)

        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.save_config)

        layout.addLayout(form)
        layout.addWidget(self.save_button)
        self.setLayout(layout)

    def save_config(self):
        updated = get_config()
        updated.update({
            "user_alias": self.user_name_input.text(),
            "assistant_alias": self.assistant_name_input.text(),
            "user_callout": self.user_callout_input.text(),
            "user_self_description": self.user_description_input.text(),
            "assistant_personality": self.assistant_personality_input.text(),
            "assistant_expectation": self.assistant_expectation_input.text()
        })
        save_config(updated)
        QMessageBox.information(self, "Successful", "✅ The setting has been saved")
        self.close()
