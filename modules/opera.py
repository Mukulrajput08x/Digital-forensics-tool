import os
import sqlite3
import shutil
import json
from datetime import datetime, timedelta


def chrome_time_to_datetime(chrome_time):
    try:
        if not chrome_time:
            return "N/A"
        return (datetime(1601, 1, 1) + timedelta(microseconds=chrome_time)).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "N/A"


def safe_copy_db(source_path, temp_path):
    if not os.path.exists(source_path):
        return False
    try:
        shutil.copy2(source_path, temp_path)
        return True
    except:
        return False


def get_opera_history():
    results = []
    history_path = os.path.expanduser(
        r"~\AppData\Roaming\Opera Software\Opera Stable\History"
    )
    temp_path = "opera_history_temp.db"

    if not safe_copy_db(history_path, temp_path):
        return [{"error": "Opera History file not found or browser may be open"}]

    try:
        conn = sqlite3.connect(temp_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT url, title, visit_count, last_visit_time
            FROM urls
            ORDER BY last_visit_time DESC
            LIMIT 100
        """)
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            results.append({
                "url": row[0],
                "title": row[1],
                "visit_count": row[2],
                "last_visit_time": chrome_time_to_datetime(row[3])
            })

    except Exception as e:
        return [{"error": str(e)}]

    return results


def get_opera_downloads():
    results = []
    history_path = os.path.expanduser(
        r"~\AppData\Roaming\Opera Software\Opera Stable\History"
    )
    temp_path = "opera_downloads_temp.db"

    if not safe_copy_db(history_path, temp_path):
        return [{"error": "Opera History file not found or browser may be open"}]

    try:
        conn = sqlite3.connect(temp_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT target_path, tab_url, start_time
            FROM downloads
            ORDER BY start_time DESC
            LIMIT 100
        """)
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            results.append({
                "target_path": row[0],
                "source_url": row[1],
                "start_time": chrome_time_to_datetime(row[2])
            })

    except Exception as e:
        return [{"error": str(e)}]

    return results


def get_opera_bookmarks():
    results = []
    bookmark_path = os.path.expanduser(
        r"~\AppData\Roaming\Opera Software\Opera Stable\Bookmarks"
    )

    if not os.path.exists(bookmark_path):
        return [{"error": "Opera Bookmarks file not found"}]

    try:
        with open(bookmark_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        def extract_bookmarks(node):
            if isinstance(node, dict):
                if node.get("type") == "url":
                    results.append({
                        "name": node.get("name", "N/A"),
                        "url": node.get("url", "N/A")
                    })
                for value in node.values():
                    extract_bookmarks(value)
            elif isinstance(node, list):
                for item in node:
                    extract_bookmarks(item)

        extract_bookmarks(data)

    except Exception as e:
        return [{"error": str(e)}]

    return results[:100]


def get_opera_cookies():
    results = []
    cookie_path = os.path.expanduser(
        r"~\AppData\Roaming\Opera Software\Opera Stable\Network\Cookies"
    )
    temp_path = "opera_cookies_temp.db"

    if not safe_copy_db(cookie_path, temp_path):
        return [{"error": "Opera Cookies file not found or browser may be open"}]

    try:
        conn = sqlite3.connect(temp_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT host_key, name, path, expires_utc
            FROM cookies
            LIMIT 100
        """)
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            results.append({
                "host_key": row[0],
                "name": row[1],
                "path": row[2],
                "expires": chrome_time_to_datetime(row[3])
            })

    except Exception as e:
        return [{"error": str(e)}]

    return results