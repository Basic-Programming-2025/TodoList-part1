from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import threading
import time
from datetime import datetime
from plyer import notification

app = Flask(__name__)
CORS(app)
DATA_FILE = "tasks.json"

# 파일이 없으면 초기화
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False)

# 알림 예약 함수
def schedule_notification(task):
    deadline_str = task.get("deadline")
    if not deadline_str:
        return

    try:
        deadline = datetime.fromisoformat(deadline_str)
    except ValueError:
        return

    now = datetime.now()
    delay = (deadline - now).total_seconds()
    if delay <= 0:
        return  # 이미 지난 마감 시간

    def notify():
        time.sleep(delay)
        notification.notify(
            title=f"[마감 알림] {task['title']}",
            message=task['desc'],
            app_name="일정 알림 시스템",
            timeout=10
        )

    threading.Thread(target=notify, daemon=True).start()

@app.route("/add", methods=["POST"])
def add_task():
    data = request.get_json()

    required_keys = {"date", "title", "desc", "deadline"}
    if not data or not required_keys.issubset(data.keys()):
        return jsonify({"status": "fail", "reason": "invalid data"}), 400

    with open(DATA_FILE, "r+", encoding="utf-8") as f:
        try:
            tasks = json.load(f)
        except json.JSONDecodeError:
            tasks = []

        tasks.append(data)

        f.seek(0)
        f.truncate()
        json.dump(tasks, f, ensure_ascii=False, indent=2)

    # 알림 예약
    schedule_notification(data)

    return jsonify({"status": "ok"}), 200

# 일정 수정
@app.route("/update/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    new_data = request.get_json()
    if not new_data:
        return jsonify({"status": "fail", "reason": "no data"}), 400

    with open(DATA_FILE, "r+", encoding="utf-8") as f:
        try:
            tasks = json.load(f)
        except json.JSONDecodeError:
            tasks = []

        if 0 <= task_id < len(tasks):
            tasks[task_id].update(new_data)

            f.seek(0)
            f.truncate()
            json.dump(tasks, f, ensure_ascii=False, indent=2)

            return jsonify({"status": "ok", "updated": tasks[task_id]}), 200
        else:
            return jsonify({"status": "fail", "reason": "invalid task ID"}), 404

# 일정 삭제
@app.route("/delete/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    with open(DATA_FILE, "r+", encoding="utf-8") as f:
        try:
            tasks = json.load(f)
        except json.JSONDecodeError:
            tasks = []

        if 0 <= task_id < len(tasks):
            deleted = tasks.pop(task_id)

            f.seek(0)
            f.truncate()
            json.dump(tasks, f, ensure_ascii=False, indent=2)

            return jsonify({"status": "ok", "deleted": deleted}), 200
        else:
            return jsonify({"status": "fail", "reason": "invalid task ID"}), 404
        
# 전체 일정 조회
@app.route("/tasks", methods=["GET"])
def get_tasks():
    if not os.path.exists(DATA_FILE):
        return jsonify([])

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            tasks = json.load(f)
        except json.JSONDecodeError:
            tasks = []
    return jsonify(tasks)

if __name__ == "__main__":
    app.run(debug=True)
