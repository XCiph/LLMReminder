import time
import json
import openai
import re
from datetime import datetime
from config import get_config

cfg = get_config()
openai.api_key = cfg["OPENAI_API_KEY"]

MEMORY_PATH = "memory.json"
SCHEDULE_PATH = "today_schedule.json"

CHECK_INTERVAL_SEC = 10
last_memory_hash = None

def file_hash(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return hash(f.read())
    except:
        return None

def should_trigger(memory):
    if len(memory) < 2:
        return False

    last_entry = memory[-2]
    if last_entry.get("role") != "user":
        return False

    content = last_entry.get("content", "").strip().lower()

    content = re.sub(r"[,.!?:-=\s]+$", "", content)
    
    return content == "understood"


def call_chatgpt(memory):
    prompt = """
You are a structured data extraction assistant. Please extract a task schedule from the conversation according to the following requirements:

Output the extracted result as a strict JSON array inside a Markdown code block, with the following format:

Each array element must be an object containing ALL of the following fields (none can be omitted):
- task (string): The task name
- start (string, format HH:MM): Start time
- end (string, format HH:MM): End time
- progress (integer): Task completion progress, initial value is 0
- remind_at (array of strings): List of reminder times, each in HH:MM format; can be an empty array, but the field must exist

Do not add any extra text, explanation, labels, or comments. Only output the pure JSON content inside a Markdown code block.

If the format is incorrect, it will cause a system error, so strictly follow the format requirements.
"""

    if len(memory) < 3:
        memory_snippet = memory
    else:
        memory_snippet = memory[-3]

    messages = [
        {"role": "system", "content": "You are a task planning assistant. The user has confirmed to start planning."},
        {"role": "user", "content": prompt + "\n\n" + json.dumps(memory_snippet, ensure_ascii=False, indent=2)}
    ]

    print("[LLM] Generating task plan...")
    response = openai.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
    )
    reply = response.choices[0].message.content
    return reply

def extract_schedule_and_reminder(text):

    match = re.search(r"```json\s*(\[.*?\])\s*```", text, re.DOTALL)
    if not match:
        match = re.search(r"(\[\s*{.*?}\s*\])", text, re.DOTALL)
    if match:
        try:
            schedule = json.loads(match.group(1))
            with open(SCHEDULE_PATH, "w", encoding="utf-8") as f:
                json.dump(schedule, f, ensure_ascii=False, indent=2)
            print("Plan has been written to today_schedule.json")
        except Exception as e:
            print(f"Failed to extract plan: {e}")

def main_loop():
    global last_memory_hash
    print("[Monitor] Started listening to memory.json...")
    while True:
        time.sleep(CHECK_INTERVAL_SEC)
        new_hash = file_hash(MEMORY_PATH)
        if new_hash != last_memory_hash:
            last_memory_hash = new_hash
            try:
                with open(MEMORY_PATH, "r", encoding="utf-8") as f:
                    memory = json.load(f)
                if should_trigger(memory):
                    print("[Trigger] User confirmation detected, generating new plan...")
                    reply = call_chatgpt(memory)
                    extract_schedule_and_reminder(reply)
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    main_loop()
