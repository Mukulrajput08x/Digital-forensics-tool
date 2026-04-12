import sqlite3
import os
import shutil
import platform
from datetime import datetime, timedelta


def get_browser_history():
    history = []
    temp_file = "history_temp.db"

    # Windows Chrome path
    if platform.system() == "Windows":
        history_path = os.path.expanduser(
            r"~\AppData\Local\Google\Chrome\User Data\Default\History"
        )
    else:
        return [{
            "url": "Not Supported",
            "title": "Browser history works only on Windows Chrome path",
            "visit_count": 0,
            "time": None,
            "display_time": "Unknown"
        }]

    try:
        if not os.path.exists(history_path):
            return [{
                "url": "Error",
                "title": "Chrome history file not found",
                "visit_count": 0,
                "time": None,
                "display_time": "Unknown"
            }]

        # old temp file remove if already exists
        if os.path.exists(temp_file):
            os.remove(temp_file)

        shutil.copy2(history_path, temp_file)

        conn = sqlite3.connect(temp_file)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT url, title, visit_count, last_visit_time
            FROM urls
            ORDER BY last_visit_time DESC
            LIMIT 20
        """)

        rows = cursor.fetchall()

        for row in rows:
            url = row[0]
            title = row[1]
            visit_count = row[2]
            raw_visit_time = row[3]

            try:
                visit_time = datetime(1601, 1, 1) + timedelta(microseconds=raw_visit_time)
                display_time = visit_time.strftime("%d-%m-%Y %I:%M:%S %p")
            except Exception:
                visit_time = None
                display_time = "Unknown"

            history.append({
                "url": url,
                "title": title if title else "No Title",
                "visit_count": visit_count,
                "time": visit_time,
                "display_time": display_time
            })

        conn.close()

    except Exception as e:
        history.append({
            "url": "Error",
            "title": str(e),
            "visit_count": 0,
            "time": None,
            "display_time": "Unknown"
        })

    return history


if __name__ == "__main__":
    data = get_browser_history()

    print("\n===== Browser History =====\n")

    for item in data:
        print("URL         :", item["url"])
        print("Title       :", item["title"])
        print("Visit Count :", item["visit_count"])
        print("Visit Time  :", item["display_time"])
        print("-" * 60)