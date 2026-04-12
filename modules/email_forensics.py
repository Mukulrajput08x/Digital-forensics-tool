import os
from pathlib import Path
from datetime import datetime

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