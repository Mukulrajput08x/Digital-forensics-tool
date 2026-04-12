from datetime import datetime
from modules.browser_history import get_browser_history
from modules.usb_tracker import get_usb_devices


def parse_time(value):
    """Convert string time to datetime for sorting"""
    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%d-%m-%Y %I:%M:%S %p")
        except:
            return datetime.min

    return datetime.min


def create_timeline():
    timeline = []

    # 🔵 Browser Data
    try:
        history = get_browser_history()

        for item in history:
            raw_time = item.get("time", None)

            timeline.append({
                "Time": raw_time,
                "Type": "Browser",
                "Details": f"Visited: {item.get('title', 'No Title')} | {item.get('url', 'Unknown')}"
            })

    except Exception as e:
        timeline.append({
            "Time": None,
            "Type": "Browser Error",
            "Details": str(e)
        })

    # 🟢 USB Data
    try:
        usb_devices = get_usb_devices()

        for device in usb_devices:
            raw_time = device.get("Checked Time", None)

            timeline.append({
                "Time": raw_time,
                "Type": "USB",
                "Details": f"USB Connected: {device.get('Friendly Name', 'Unknown')}"
            })

    except Exception as e:
        timeline.append({
            "Time": None,
            "Type": "USB Error",
            "Details": str(e)
        })

    # 🔥 Proper Sorting (datetime + string handled)
    timeline = sorted(timeline, key=lambda x: parse_time(x["Time"]), reverse=True)

    # 🎯 Display Formatting
    for entry in timeline:
        if isinstance(entry["Time"], datetime):
            entry["Time"] = entry["Time"].strftime("%d/%m/%Y %H:%M:%S")
        elif isinstance(entry["Time"], str):
            entry["Time"] = entry["Time"]
        else:
            entry["Time"] = "Unknown"

    return timeline


if __name__ == "__main__":
    result = create_timeline()

    print("===== DIGITAL FORENSICS TIMELINE =====\n")

    for entry in result:
        print(f"[{entry['Time']}] {entry['Type']} -> {entry['Details']}")