import sqlite3
import os
import shutil
from datetime import datetime, timedelta

def get_browser_history():

    path = os.path.expanduser(
        r"~\AppData\Local\Google\Chrome\User Data\Default\History"
    )

    temp = "history_temp.db"
    shutil.copy2(path, temp)

    conn = sqlite3.connect(temp)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT url, last_visit_time
        FROM urls
        ORDER BY last_visit_time DESC
        LIMIT 20
    """)

    results = []

    for url, visit_time in cursor.fetchall():

        visit_time = datetime(1601,1,1) + timedelta(microseconds=visit_time)

        results.append({
            "url": url,
            "visit_time": visit_time
        })

    conn.close()
    os.remove(temp)

    return results