import json
import os
import openai
from PyQt6.QtWidgets import (
    QApplication, QWidget, QTextEdit, QVBoxLayout, QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import QTimer
from datetime import datetime, timedelta
from config import get_config
from prompt_template import build_persona_prompt 
import subprocess


class ChatDialogWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Communication Interface")
        self.resize(600, 500)

        self.chat_history = []
        self.memory_file = "memory.json"
        self.schedule_file = "today_schedule.json"
        self.reminder_file = "reminder_config.json"

        # UI
        self.layout = QVBoxLayout()
        self.chat_box = QTextEdit()
        self.chat_box.setReadOnly(True)
        self.input_box = QLineEdit()
        self.send_button = QPushButton("Send")

        self.layout.addWidget(self.chat_box)
        self.layout.addWidget(self.input_box)
        self.layout.addWidget(self.send_button)
        self.setLayout(self.layout)

        # Actions
        self.send_button.clicked.connect(self.handle_send)
        self.input_box.returnPressed.connect(self.handle_send)
        self.auto_planner_proc = subprocess.Popen(["python", "auto_planner.py"])

        # System role & open message
        self.cfg = get_config()
        openai.api_key = self.cfg["OPENAI_API_KEY"]

        persona_prompt = build_persona_prompt(self.cfg)

        self.messages = [{"role": "system", "content": persona_prompt}]
        self.first_call()

    def first_call(self):
        try:
            with open("today_tasks.json", "r", encoding="utf-8") as f:
                tasks = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read task list: {e}")
            self.close()
            return

        now = datetime.now().strftime("%H:%M")
        task_lines = "\n".join([f"- {t['task']}, estimated {t['duration_min']} minutes" for t in tasks])
        prompt = f"""
        The current time is {now}.

        Here are today's tasks:
        {task_lines}

        Please start with a brief greeting, mention the current time, and then help me arrange these tasks into a reasonable schedule.

        For each task:
        - Specify the start time and end time
        - Include necessary breaks

        Also, help me decide on an appropriate reminder frequency (for example, how often I should be reminded), and clearly schedule the reminder times for each task.

        Finally, present the finalized schedule and reminder times in a single, unified, clear, and easy-to-read format with line breaks between items, so it is easy to read in plain text.

        End by reminding me to reply "Understood" to confirm the plan.
        """
        self.messages.append({"role": "user", "content": prompt})
        self.call_chatgpt(first_reply=True)

    def append_user(self, text):
        user_alias = self.cfg.get("user_alias", "You")
        self.chat_box.append(f"<b>{user_alias}：</b> {text}")
        self.messages.append({"role": "user", "content": text})

    def append_assistant(self, text, include_in_messages=True):
        assistant_alias = self.cfg.get("assistant_alias", "Planner")
        safe_text = text.replace("\n", "<br>")
        self.chat_box.append(f"<b>{assistant_alias}：</b> {safe_text}")
        if include_in_messages:
            self.messages.append({"role": "assistant", "content": text})
        self.extract_memory(text)

    def handle_send(self):
        user_text = self.input_box.text().strip()
        if not user_text:
            return
        self.input_box.clear()
        self.append_user(user_text)
        self.call_chatgpt()

        if "understood" in user_text.lower():
            print(f"[Triggered] Response detected, entering reminder setup process")
            QTimer.singleShot(30 * 1000, self.setup_reminder_triggers)

    def call_chatgpt(self, first_reply=False):
        try:
            response = openai.chat.completions.create(
                model="o4-mini",
                messages=self.messages,
            )
            reply = response.choices[0].message.content

            assistant_alias = self.cfg.get("assistant_alias", "Planner")
            safe_reply = reply.replace("\n", "<br>")
            self.chat_box.append(f"<b>{assistant_alias}：</b> {safe_reply}")
            self.messages.append({"role": "assistant", "content": reply})

            self.extract_memory(reply, skip_last_user=first_reply)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"LLM Request failed: {e}")

    def get_current_time(self):
        return datetime.now().strftime("%H:%M")

    def time_in_range(self, start_str, end_str, current_str):
        t_format = "%H:%M"
        start = datetime.strptime(start_str, t_format)
        end = datetime.strptime(end_str, t_format)
        now = datetime.strptime(current_str, t_format)
        return start <= now <= end

    def setup_reminder_triggers(self):
        try:
            with open(self.schedule_file, "r", encoding="utf-8") as f:
                schedule = json.load(f)
        except Exception as e:
            print(f"[Reminder Setup] Failed to read task schedule: {e}")
            return

        now = datetime.now()
        for item in schedule:
            task_name = item.get("task", "Unknown Task")
            for time_str in item.get("remind_at", []):
                try:
                    target = datetime.strptime(time_str, "%H:%M").replace(
                        year=now.year, month=now.month, day=now.day
                    )
                    if target < now:
                        target += timedelta(days=1)  # If the time has already passed today, move to tomorrow
                    delta_ms = int((target - now).total_seconds() * 1000)
                    QTimer.singleShot(delta_ms, lambda task=task_name: self.show_reminder(task))
                    print(f"[Reminder Setup] Reminder set: {task_name} -> {time_str}")
                except Exception as e:
                    print(f"[Reminder Setup Failed] {time_str} → {e}")

    def show_reminder(self, task_name):
        try:
            with open(self.schedule_file, "r", encoding="utf-8") as f:
                schedule = json.load(f)
            task = next((t for t in schedule if t["task"] == task_name), None)
        except Exception as e:
            print(f"[Reminder Failed] Unable to read task information: {e}")
            return

        if not task:
            print(f"[Reminder Failed] Task not found: {task_name}")
            return

        progress = task.get("progress", 0)
        now = datetime.now().strftime("%H:%M")

        prompt = (
            f"The current time is {now}. The current task is \"{task_name}\", "
            f"and the user's progress is {progress}%.\n"
            f"Please send a short, encouraging reminder message based on the task, time, and progress."
        )

        try:
            temp_messages = [self.messages[0]] + [{"role": "user", "content": prompt}]
            response = openai.chat.completions.create(
                model="o4-mini",
                messages=temp_messages,
            )
            reply = response.choices[0].message.content.strip()
            self.append_assistant(reply, include_in_messages=False)

        except Exception as e:
            print(f"[Reminder Failed] ChatGPT request failed: {e}")


    def extract_memory(self, assistant_reply, skip_last_user=False):
        memory_path = self.memory_file

        # Find last user message
        if skip_last_user:
            user_index = -3 if len(self.messages) >= 3 else None
        else:
            user_index = -2 if len(self.messages) >= 2 else None

        user_message = self.messages[user_index]["content"] if user_index is not None else ""

        new_pairs = []
        if user_message:
            new_pairs.append({"role": "user", "content": user_message})
        new_pairs.append({"role": "assistant", "content": assistant_reply})

        try:
            if os.path.exists(memory_path):
                with open(memory_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            else:
                existing = []

            existing.extend(new_pairs)

            with open(memory_path, "w", encoding="utf-8") as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"[Failed to write memory.json] {e}")

    def closeEvent(self, event):
        if hasattr(self, "auto_planner_proc"):
            try:
                self.auto_planner_proc.terminate()
                print("[Cleanup] auto_planner has been terminated")
            except Exception as e:
                print(f"[Warning] Unable to terminate auto_planner: {e}")
        event.accept()

