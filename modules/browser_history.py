import sqlite3
import os
import shutil
from datetime import datetime, timedelta


def get_browser_history():

    history_path = os.path.expanduser(
        r"~\AppData\Local\Google\Chrome\User Data\Default\History"
    )

    temp_file = "history_temp.db"

    history = []

    try:
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
            visit_time = row[3]

            visit_time = datetime(1601, 1, 1) + timedelta(
                microseconds=visit_time
            )

            history.append({
                "url": url,
                "title": title,
                "visit_count": visit_count,
                "time": visit_time.strftime("%d-%m-%Y %I:%M:%S %p")
            })

        conn.close()

    except Exception as e:
        history.append({
            "url": "Error",
            "title": str(e),
            "visit_count": 0,
            "time": "Unknown"
        })

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

    return history


if __name__ == "__main__":

    data = get_browser_history()

    print("\n===== Browser History =====\n")

    for item in data:
        print("URL         :", item["url"])
        print("Title       :", item["title"])
        print("Visit Count :", item["visit_count"])
        print("Visit Time  :", item["time"])
        print("-" * 60)