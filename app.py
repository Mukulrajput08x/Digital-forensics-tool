from flask import Flask, render_template, request, send_file, render_template_string
from modules.browser_history import get_browser_history
from modules.file_hasher import hash_file
from modules.deleted_recovery import recover_deleted
from modules.timeline import create_timeline
from modules.report_generator import generate_report
from datetime import datetime, timedelta
import platform
import webbrowser
import threading
import os
import sqlite3
import shutil
import json
from pathlib import Path

app = Flask(__name__)


# =========================
# SAFE USB IMPORT
# =========================
if platform.system() == "Windows":
    try:
        from modules.usb_tracker import get_usb_devices
    except Exception:
        def get_usb_devices():
            return [{"Device Name": "Error", "Friendly Name": "USB module error", "Checked Time": "-"}]
else:
    def get_usb_devices():
        return [{"Device Name": "Not Supported", "Friendly Name": "USB works only on Windows", "Checked Time": "-"}]


# =========================
# COMMON HELPERS
# =========================
def get_time():
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def safe_copy_db(source_path, temp_path):
    if not os.path.exists(source_path):
        return False
    try:
        shutil.copy2(source_path, temp_path)
        return True
    except Exception:
        return False


def chrome_time_to_datetime(chrome_time):
    try:
        if not chrome_time:
            return "N/A"
        return (datetime(1601, 1, 1) + timedelta(microseconds=chrome_time)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "N/A"


def firefox_time_to_datetime(firefox_time):
    try:
        if not firefox_time:
            return "N/A"
        return (datetime(1970, 1, 1) + timedelta(microseconds=firefox_time)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "N/A"


# =========================
# EMAIL FORENSICS HELPERS
# =========================
try:
    import winreg
except ImportError:
    winreg = None


def get_gmail_activity(browser_data):
    results = []

    for item in browser_data:
        url = str(item.get("url", "")).lower()
        title = str(item.get("title", ""))
        visit_time = item.get("last_visit_time", "N/A")

        if (
            "mail.google.com" in url
            or "gmail" in url
            or "accounts.google.com" in url
        ):
            results.append({
                "url": item.get("url", "N/A"),
                "title": title if title else "N/A",
                "visit_count": item.get("visit_count", "-"),
                "last_visit_time": visit_time
            })

    return results[:200] if results else [{"error": "No Gmail activity found"}]


def find_outlook_files():
    results = []

    possible_paths = [
        Path.home() / "Documents" / "Outlook Files",
        Path.home() / "AppData" / "Local" / "Microsoft" / "Outlook"
    ]

    for folder in possible_paths:
        if folder.exists():
            for file in folder.glob("*"):
                if file.is_file() and file.suffix.lower() in [".pst", ".ost"]:
                    try:
                        stat = file.stat()
                        results.append({
                            "file_name": file.name,
                            "path": str(file),
                            "size_mb": round(stat.st_size / (1024 * 1024), 2),
                            "modified_time": datetime.fromtimestamp(
                                stat.st_mtime
                            ).strftime("%Y-%m-%d %H:%M:%S")
                        })
                    except Exception:
                        pass

    return results if results else [{"error": "No Outlook PST/OST files found"}]


def get_outlook_profiles():
    if winreg is None:
        return [{"error": "Registry access only works on Windows"}]

    profiles = []
    office_versions = ["16.0", "15.0", "14.0"]

    for version in office_versions:
        key_path = fr"Software\Microsoft\Office\{version}\Outlook\Profiles"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                count = winreg.QueryInfoKey(key)[0]
                for i in range(count):
                    profile_name = winreg.EnumKey(key, i)
                    profiles.append({
                        "profile_name": profile_name,
                        "office_version": version
                    })
        except Exception:
            continue

    return profiles if profiles else [{"error": "No Outlook profiles found"}]


# =========================
# CHROMIUM BROWSER HELPERS
# =========================
def get_chromium_history(history_path, temp_path):
    results = []

    if not safe_copy_db(history_path, temp_path):
        return [{"error": "History file not found or browser may be open"}]

    try:
        conn = sqlite3.connect(temp_path)
        cursor = conn.cursor()

        # Last 3 months filter
        cutoff_date = datetime.now() - timedelta(days=90)
        chromium_epoch = datetime(1601, 1, 1)
        cutoff_microseconds = int((cutoff_date - chromium_epoch).total_seconds() * 1000000)

        cursor.execute("""
            SELECT url, title, visit_count, last_visit_time
            FROM urls
            WHERE last_visit_time >= ?
            ORDER BY last_visit_time DESC
            LIMIT 500
        """, (cutoff_microseconds,))

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


def get_chromium_downloads(history_path, temp_path):
    results = []

    if not safe_copy_db(history_path, temp_path):
        return [{"error": "History file not found or browser may be open"}]

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


def get_chromium_bookmarks(bookmark_path):
    results = []

    if not os.path.exists(bookmark_path):
        return [{"error": "Bookmarks file not found"}]

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


def get_chromium_cookies(cookie_path, temp_path):
    results = []

    if not safe_copy_db(cookie_path, temp_path):
        return [{"error": "Cookies file not found or browser may be open"}]

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


# =========================
# CHROME
# =========================
def get_chrome_history():
    return get_chromium_history(
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data\Default\History"),
        "history_temp.db"
    )


def get_chrome_downloads():
    return get_chromium_downloads(
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data\Default\History"),
        "chrome_downloads_temp.db"
    )


def get_chrome_bookmarks():
    return get_chromium_bookmarks(
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data\Default\Bookmarks")
    )


def get_chrome_cookies():
    return get_chromium_cookies(
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data\Default\Network\Cookies"),
        "chrome_cookies_temp.db"
    )


# =========================
# EDGE
# =========================
def get_edge_history():
    return get_chromium_history(
        os.path.expanduser(r"~\AppData\Local\Microsoft\Edge\User Data\Default\History"),
        "edge_history_temp.db"
    )


def get_edge_downloads():
    return get_chromium_downloads(
        os.path.expanduser(r"~\AppData\Local\Microsoft\Edge\User Data\Default\History"),
        "edge_downloads_temp.db"
    )


def get_edge_bookmarks():
    return get_chromium_bookmarks(
        os.path.expanduser(r"~\AppData\Local\Microsoft\Edge\User Data\Default\Bookmarks")
    )


def get_edge_cookies():
    return get_chromium_cookies(
        os.path.expanduser(r"~\AppData\Local\Microsoft\Edge\User Data\Default\Network\Cookies"),
        "edge_cookies_temp.db"
    )


# =========================
# OPERA
# =========================
def get_opera_history():
    return get_chromium_history(
        os.path.expanduser(r"~\AppData\Roaming\Opera Software\Opera Stable\History"),
        "opera_history_temp.db"
    )


def get_opera_downloads():
    return get_chromium_downloads(
        os.path.expanduser(r"~\AppData\Roaming\Opera Software\Opera Stable\History"),
        "opera_downloads_temp.db"
    )


def get_opera_bookmarks():
    return get_chromium_bookmarks(
        os.path.expanduser(r"~\AppData\Roaming\Opera Software\Opera Stable\Bookmarks")
    )


def get_opera_cookies():
    return get_chromium_cookies(
        os.path.expanduser(r"~\AppData\Roaming\Opera Software\Opera Stable\Network\Cookies"),
        "opera_cookies_temp.db"
    )


# =========================
# FIREFOX
# =========================
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


# =========================
# INLINE HTML TEMPLATES
# =========================
BROWSER_MAIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Browser Analysis</title>
    <style>
        body {
            font-family: Arial;
            text-align: center;
            background: #111827;
            color: white;
            margin: 0;
            padding: 0;
        }
        h1 { margin-top: 40px; }
        .container {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            width: 720px;
            margin: 40px auto;
        }
        .card {
            background: #1f2937;
            padding: 30px;
            border-radius: 12px;
            cursor: pointer;
            font-size: 20px;
            font-weight: bold;
            transition: 0.3s;
        }
        .card:hover {
            background: #374151;
            transform: scale(1.03);
        }
        .back {
            display: inline-block;
            margin-top: 20px;
            color: white;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <h1>Select Browser</h1>
    <p>Time: {{ time }}</p>

    <div class="container">
        <div class="card" onclick="location.href='/browser/chrome'">Chrome</div>
        <div class="card" onclick="location.href='/browser/edge'">Edge</div>
        <div class="card" onclick="location.href='/browser/firefox'">Firefox</div>
        <div class="card" onclick="location.href='/browser/opera'">Opera</div>
    </div>

    <a class="back" href="/">Back to Dashboard</a>
</body>
</html>
"""

BROWSER_MENU_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ browser }} Analysis</title>
    <style>
        body {
            font-family: Arial;
            text-align: center;
            background: #0b1120;
            color: white;
            margin: 0;
            padding: 0;
        }
        h1 { margin-top: 40px; }
        .container {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            width: 720px;
            margin: 40px auto;
        }
        .card {
            background: #1e293b;
            padding: 25px;
            border-radius: 12px;
            cursor: pointer;
            font-size: 18px;
            font-weight: bold;
            transition: 0.3s;
        }
        .card:hover {
            background: #334155;
            transform: scale(1.03);
        }
        .back {
            display: inline-block;
            margin-top: 20px;
            color: white;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <h1>{{ browser }} Analysis</h1>
    <p>Time: {{ time }}</p>

    <div class="container">
        <div class="card" onclick="location.href='{{ base }}/history'">History</div>
        <div class="card" onclick="location.href='{{ base }}/downloads'">Downloads</div>
        <div class="card" onclick="location.href='{{ base }}/bookmarks'">Bookmarks</div>
        <div class="card" onclick="location.href='{{ base }}/cookies'">Cookies</div>
    </div>

    <a class="back" href="/browser">Back to Browser Selection</a>
</body>
</html>
"""

EMAIL_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Email Forensics</title>
    <style>
        body {
            font-family: Arial;
            text-align: center;
            background: #0b1120;
            color: white;
            margin: 0;
            padding: 0;
        }
        h1 { margin-top: 40px; }
        .container {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            width: 950px;
            margin: 40px auto;
        }
        .card {
            background: #1e293b;
            padding: 25px;
            border-radius: 12px;
            cursor: pointer;
            font-size: 18px;
            font-weight: bold;
            transition: 0.3s;
        }
        .card:hover {
            background: #334155;
            transform: scale(1.03);
        }
        .back {
            display: inline-block;
            margin-top: 20px;
            color: white;
            text-decoration: none;
        }
    </style>
</head>
<body>

<h1>Email Forensics</h1>
<p>Time: {{ time }}</p>

<div class="container">
    <div class="card" onclick="location.href='/email/gmail'">Gmail Activity</div>
    <div class="card" onclick="location.href='/email/outlook-files'">Outlook Files</div>
    <div class="card" onclick="location.href='/email/outlook-profiles'">Outlook Profiles</div>
</div>

<a class="back" href="/">Back to Dashboard</a>
</body>
</html>
"""

HISTORY_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ browser }} History</title>
    <style>
        body { font-family: Arial; background: #f8fafc; margin: 20px; }
        h1 { text-align: center; }
        p { text-align: center; }
        table { width: 100%; border-collapse: collapse; background: white; }
        th, td {
            border: 1px solid #cbd5e1;
            padding: 10px;
            text-align: left;
            font-size: 14px;
            vertical-align: top;
        }
        th { background: #1e293b; color: white; }
        a { color: #2563eb; word-break: break-all; }
    </style>
</head>
<body>
    <h1>{{ browser }}</h1>
    <p>Time: {{ time }}</p>

    <table>
        <tr>
            <th>URL</th>
            <th>Title</th>
            <th>Visit Count</th>
            <th>Last Visit Time</th>
        </tr>
        {% for item in data %}
        <tr>
            <td>
                {% if item.error %}
                    {{ item.error }}
                {% else %}
                    <a href="{{ item.url }}" target="_blank">{{ item.url }}</a>
                {% endif %}
            </td>
            <td>{{ item.title if item.title else "-" }}</td>
            <td>{{ item.visit_count if item.visit_count is not none else "-" }}</td>
            <td>{{ item.last_visit_time if item.last_visit_time else "-" }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

DOWNLOADS_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ browser }} Downloads</title>
    <style>
        body { font-family: Arial; background: #f8fafc; margin: 20px; }
        h1, p { text-align: center; }
        table { width: 100%; border-collapse: collapse; background: white; }
        th, td {
            border: 1px solid #cbd5e1;
            padding: 10px;
            text-align: left;
            font-size: 14px;
            vertical-align: top;
        }
        th { background: #1e293b; color: white; }
    </style>
</head>
<body>
    <h1>{{ browser }}</h1>
    <p>Time: {{ time }}</p>

    <table>
        <tr>
            <th>Target Path</th>
            <th>Source URL</th>
            <th>Start Time</th>
        </tr>
        {% for item in data %}
        <tr>
            <td>{{ item.target_path if item.target_path else item.error }}</td>
            <td>{{ item.source_url if item.source_url else "-" }}</td>
            <td>{{ item.start_time if item.start_time else "-" }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

BOOKMARKS_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ browser }} Bookmarks</title>
    <style>
        body { font-family: Arial; background: #f8fafc; margin: 20px; }
        h1, p { text-align: center; }
        table { width: 100%; border-collapse: collapse; background: white; }
        th, td {
            border: 1px solid #cbd5e1;
            padding: 10px;
            text-align: left;
            vertical-align: top;
        }
        th { background: #1e293b; color: white; }
        a { color: #2563eb; word-break: break-all; }
    </style>
</head>
<body>
    <h1>{{ browser }}</h1>
    <p>Time: {{ time }}</p>

    <table>
        <tr>
            <th>Name</th>
            <th>URL</th>
        </tr>
        {% for item in data %}
        <tr>
            <td>{{ item.name if item.name else item.error }}</td>
            <td>
                {% if item.url %}
                    <a href="{{ item.url }}" target="_blank">{{ item.url }}</a>
                {% else %}
                    -
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

COOKIES_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ browser }} Cookies</title>
    <style>
        body { font-family: Arial; background: #f8fafc; margin: 20px; }
        h1, p { text-align: center; }
        table { width: 100%; border-collapse: collapse; background: white; }
        th, td {
            border: 1px solid #cbd5e1;
            padding: 10px;
            text-align: left;
            vertical-align: top;
        }
        th { background: #1e293b; color: white; }
    </style>
</head>
<body>
    <h1>{{ browser }}</h1>
    <p>Time: {{ time }}</p>

    <table>
        <tr>
            <th>Host</th>
            <th>Name</th>
            <th>Path</th>
            <th>Expires</th>
        </tr>
        {% for item in data %}
        <tr>
            <td>{{ item.host_key if item.host_key else item.error }}</td>
            <td>{{ item.name if item.name else "-" }}</td>
            <td>{{ item.path if item.path else "-" }}</td>
            <td>{{ item.expires if item.expires else "-" }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

OUTLOOK_FILES_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Outlook Files</title>
    <style>
        body { font-family: Arial; background: #f8fafc; margin: 20px; }
        h1, p { text-align: center; }
        table { width: 100%; border-collapse: collapse; background: white; }
        th, td {
            border: 1px solid #cbd5e1;
            padding: 10px;
            text-align: left;
            vertical-align: top;
        }
        th { background: #1e293b; color: white; }
    </style>
</head>
<body>
    <h1>Outlook Files</h1>
    <p>Time: {{ time }}</p>
    <table>
        <tr>
            <th>File Name</th>
            <th>Path</th>
            <th>Size (MB)</th>
            <th>Modified Time</th>
        </tr>
        {% for item in data %}
        <tr>
            <td>{{ item.file_name if item.file_name else item.error }}</td>
            <td>{{ item.path if item.path else "-" }}</td>
            <td>{{ item.size_mb if item.size_mb is not none else "-" }}</td>
            <td>{{ item.modified_time if item.modified_time else "-" }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

OUTLOOK_PROFILES_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Outlook Profiles</title>
    <style>
        body { font-family: Arial; background: #f8fafc; margin: 20px; }
        h1, p { text-align: center; }
        table { width: 100%; border-collapse: collapse; background: white; }
        th, td {
            border: 1px solid #cbd5e1;
            padding: 10px;
            text-align: left;
            vertical-align: top;
        }
        th { background: #1e293b; color: white; }
    </style>
</head>
<body>
    <h1>Outlook Profiles</h1>
    <p>Time: {{ time }}</p>
    <table>
        <tr>
            <th>Profile Name</th>
            <th>Office Version</th>
        </tr>
        {% for item in data %}
        <tr>
            <td>{{ item.profile_name if item.profile_name else item.error }}</td>
            <td>{{ item.office_version if item.office_version else "-" }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""


# =========================
# MAIN ROUTES
# =========================
@app.route("/")
def home():
    return render_template("index.html", time=get_time())


@app.route("/browser")
def browser_main():
    return render_template_string(BROWSER_MAIN_HTML, time=get_time())


@app.route("/browser/chrome")
def chrome_page():
    return render_template_string(BROWSER_MENU_HTML, browser="Chrome", base="/browser/chrome", time=get_time())


@app.route("/browser/edge")
def edge_page():
    return render_template_string(BROWSER_MENU_HTML, browser="Edge", base="/browser/edge", time=get_time())


@app.route("/browser/firefox")
def firefox_page():
    return render_template_string(BROWSER_MENU_HTML, browser="Firefox", base="/browser/firefox", time=get_time())


@app.route("/browser/opera")
def opera_page():
    return render_template_string(BROWSER_MENU_HTML, browser="Opera", base="/browser/opera", time=get_time())


@app.route("/email")
def email_page():
    return render_template_string(EMAIL_HTML, time=get_time())


# =========================
# CHROME ROUTES
# =========================
@app.route("/browser/chrome/history")
def chrome_history():
    data = get_chrome_history()
    return render_template_string(HISTORY_HTML, data=data, browser="Chrome History (Last 3 Months)", time=get_time())


@app.route("/browser/chrome/downloads")
def chrome_downloads():
    data = get_chrome_downloads()
    return render_template_string(DOWNLOADS_HTML, data=data, browser="Chrome Downloads", time=get_time())


@app.route("/browser/chrome/bookmarks")
def chrome_bookmarks():
    data = get_chrome_bookmarks()
    return render_template_string(BOOKMARKS_HTML, data=data, browser="Chrome Bookmarks", time=get_time())


@app.route("/browser/chrome/cookies")
def chrome_cookies():
    data = get_chrome_cookies()
    return render_template_string(COOKIES_HTML, data=data, browser="Chrome Cookies", time=get_time())


# =========================
# EDGE ROUTES
# =========================
@app.route("/browser/edge/history")
def edge_history():
    data = get_edge_history()
    return render_template_string(HISTORY_HTML, data=data, browser="Edge History (Last 3 Months)", time=get_time())


@app.route("/browser/edge/downloads")
def edge_downloads():
    data = get_edge_downloads()
    return render_template_string(DOWNLOADS_HTML, data=data, browser="Edge Downloads", time=get_time())


@app.route("/browser/edge/bookmarks")
def edge_bookmarks():
    data = get_edge_bookmarks()
    return render_template_string(BOOKMARKS_HTML, data=data, browser="Edge Bookmarks", time=get_time())


@app.route("/browser/edge/cookies")
def edge_cookies():
    data = get_edge_cookies()
    return render_template_string(COOKIES_HTML, data=data, browser="Edge Cookies", time=get_time())


# =========================
# OPERA ROUTES
# =========================
@app.route("/browser/opera/history")
def opera_history():
    data = get_opera_history()
    return render_template_string(HISTORY_HTML, data=data, browser="Opera History (Last 3 Months)", time=get_time())


@app.route("/browser/opera/downloads")
def opera_downloads():
    data = get_opera_downloads()
    return render_template_string(DOWNLOADS_HTML, data=data, browser="Opera Downloads", time=get_time())


@app.route("/browser/opera/bookmarks")
def opera_bookmarks():
    data = get_opera_bookmarks()
    return render_template_string(BOOKMARKS_HTML, data=data, browser="Opera Bookmarks", time=get_time())


@app.route("/browser/opera/cookies")
def opera_cookies():
    data = get_opera_cookies()
    return render_template_string(COOKIES_HTML, data=data, browser="Opera Cookies", time=get_time())


# =========================
# FIREFOX ROUTES
# =========================
@app.route("/browser/firefox/history")
def firefox_history():
    data = get_firefox_history()
    return render_template_string(HISTORY_HTML, data=data, browser="Firefox History (Last 3 Months)", time=get_time())


@app.route("/browser/firefox/downloads")
def firefox_downloads():
    data = get_firefox_downloads()
    return render_template_string(DOWNLOADS_HTML, data=data, browser="Firefox Downloads", time=get_time())


@app.route("/browser/firefox/bookmarks")
def firefox_bookmarks():
    data = get_firefox_bookmarks()
    return render_template_string(BOOKMARKS_HTML, data=data, browser="Firefox Bookmarks", time=get_time())


@app.route("/browser/firefox/cookies")
def firefox_cookies():
    data = get_firefox_cookies()
    return render_template_string(COOKIES_HTML, data=data, browser="Firefox Cookies", time=get_time())


# =========================
# EMAIL ROUTES
# =========================
@app.route("/email/gmail")
def gmail_page():
    browser_data = get_browser_history()
    data = get_gmail_activity(browser_data)
    return render_template_string(HISTORY_HTML, data=data, browser="Gmail Activity", time=get_time())


@app.route("/email/outlook-files")
def outlook_files_page():
    data = find_outlook_files()
    return render_template_string(OUTLOOK_FILES_HTML, data=data, time=get_time())


@app.route("/email/outlook-profiles")
def outlook_profiles_page():
    data = get_outlook_profiles()
    return render_template_string(OUTLOOK_PROFILES_HTML, data=data, time=get_time())


# =========================
# OPTIONAL OLD BROWSER ROUTE
# =========================
@app.route("/browser-old")
def browser_old():
    data = get_browser_history()
    return render_template("browser.html", data=data, time=get_time())


# =========================
# USB
# =========================
@app.route("/usb")
def usb():
    data = get_usb_devices()
    return render_template("usb.html", data=data, time=get_time())


# =========================
# HASH
# =========================
@app.route("/hash")
def hash_page():
    try:
        hashes = hash_file("history_temp.db")

        return f"""
        <h2>File Hash Result</h2>
        MD5 : {hashes['md5']} <br><br>
        SHA256 : {hashes['sha256']} <br><br>
        Time : {get_time()}
        """
    except Exception:
        return f"""
        <h2>Error</h2>
        history_temp.db file not found<br><br>
        Please open Chrome History page first.<br><br>
        Time : {get_time()}
        """


# =========================
# DELETED RECOVERY
# =========================
@app.route("/deleted")
def deleted():
    files = recover_deleted()
    return render_template("deleted.html", files=files, time=get_time())


# =========================
# TIMELINE
# =========================
@app.route("/timeline")
def timeline():
    data = create_timeline()
    return render_template("timeline.html", data=data, time=get_time())


# =========================
# REPORT
# =========================
@app.route("/report", methods=["GET", "POST"])
def report():
    if request.method == "POST":
        try:
            case_id = request.form["case_id"]
            case_name = request.form["case_name"]
            investigator = request.form["investigator"]

            browser_data = get_browser_history()
            usb_data = get_usb_devices()
            timeline_data = create_timeline()

            try:
                hashes = hash_file("history_temp.db")
                md5 = hashes["md5"]
                sha256 = hashes["sha256"]
            except Exception:
                md5 = "Not Available"
                sha256 = "Not Available"

            file_path = generate_report(
                browser_data,
                usb_data,
                timeline_data,
                case_id,
                case_name,
                investigator,
                md5,
                sha256
            )

            return send_file(file_path, as_attachment=True)

        except Exception as e:
            return f"""
            <h2>Report Generation Failed</h2>
            Error: {str(e)} <br><br>
            Time : {get_time()}
            """

    return render_template("report_form.html", time=get_time())


def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")


if __name__ == "__main__":
    threading.Timer(1.5, open_browser).start()
    app.run(debug=True, host="127.0.0.1", port=5000, use_reloader=False)