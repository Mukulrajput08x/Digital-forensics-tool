import os
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime, timedelta


def firefox_time_to_datetime(firefox_time):
    try:
        if not firefox_time:
            return "N/A"
        # Firefox timestamp microseconds since Unix epoch
        return (datetime(1970, 1, 1) + timedelta(microseconds=firefox_time)).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "N/A"


def get_firefox_profile_path():
    base_path = Path.home() / "AppData" / "Roaming" / "Mozilla" / "Firefox" / "Profiles"
    if not base_path.exists():
        return None

    profiles = list(base_path.glob("*.default-release")) + list(base_path.glob("*.default"))
    if profiles:
        return profiles[0]

    all_profiles = list(base_path.iterdir())
    if all_profiles:
        return all_profiles[0]

    return None


def safe_copy_db(source_path, temp_path):
    if not os.path.exists(source_path):
        return False
    try:
        shutil.copy2(source_path, temp_path)
        return True
    except:
        return False


def get_firefox_history():
    results = []
    profile_path = get_firefox_profile_path()

    if not profile_path:
        return [{"error": "Firefox profile not found"}]

    history_path = profile_path / "places.sqlite"
    temp_path = "firefox_places_temp.db"

    if not safe_copy_db(str(history_path), temp_path):
        return [{"error": "Firefox places.sqlite not found or browser may be open"}]

    try:
        conn = sqlite3.connect(temp_path)
        cursor = conn.cursor()

        # Last 3 months filter
        cutoff_date = datetime.now() - timedelta(days=90)
        cutoff_microseconds = int(cutoff_date.timestamp() * 1000000)

        cursor.execute("""
            SELECT url, title, visit_count, last_visit_date
            FROM moz_places
            WHERE last_visit_date IS NOT NULL AND last_visit_date >= ?
            ORDER BY last_visit_date DESC
            LIMIT 500
        """, (cutoff_microseconds,))

        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            results.append({
                "url": row[0],
                "title": row[1],
                "visit_count": row[2],
                "last_visit_time": firefox_time_to_datetime(row[3])
            })

    except Exception as e:
        return [{"error": str(e)}]

    return results


def get_firefox_bookmarks():
    results = []
    profile_path = get_firefox_profile_path()

    if not profile_path:
        return [{"error": "Firefox profile not found"}]

    history_path = profile_path / "places.sqlite"
    temp_path = "firefox_bookmarks_temp.db"

    if not safe_copy_db(str(history_path), temp_path):
        return [{"error": "Firefox places.sqlite not found or browser may be open"}]

    try:
        conn = sqlite3.connect(temp_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.title, p.url
            FROM moz_bookmarks b
            JOIN moz_places p ON b.fk = p.id
            WHERE p.url IS NOT NULL
            LIMIT 100
        """)
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            results.append({
                "name": row[0] if row[0] else "N/A",
                "url": row[1]
            })

    except Exception as e:
        return [{"error": str(e)}]

    return results


def get_firefox_cookies():
    results = []
    profile_path = get_firefox_profile_path()

    if not profile_path:
        return [{"error": "Firefox profile not found"}]

    cookie_path = profile_path / "cookies.sqlite"
    temp_path = "firefox_cookies_temp.db"

    if not safe_copy_db(str(cookie_path), temp_path):
        return [{"error": "Firefox cookies.sqlite not found or browser may be open"}]

    try:
        conn = sqlite3.connect(temp_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT host, name, path, expiry
            FROM moz_cookies
            LIMIT 100
        """)
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            results.append({
                "host_key": row[0],
                "name": row[1],
                "path": row[2],
                "expires": row[3]
            })

    except Exception as e:
        return [{"error": str(e)}]

    return results


def get_firefox_downloads():
    return [{"error": "Firefox downloads module basic version me abhi add nahi kiya gaya"}]