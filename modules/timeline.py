from modules.browser_history import get_browser_history
from modules.usb_tracker import get_usb_devices


def create_timeline():
    timeline = []

    try:
        history = get_browser_history()

        for item in history:
            timeline.append({
                "Time": item.get("time", "Unknown"),
                "Type": "Browser",
                "Details": "Visited: " + item.get("url", "Unknown")
            })

    except Exception as e:
        timeline.append({
            "Time": "Unknown",
            "Type": "Browser Error",
            "Details": str(e)
        })

    try:
        usb_devices = get_usb_devices()

        for device in usb_devices:
            timeline.append({
                "Time": device.get("Checked Time", "Unknown"),
                "Type": "USB",
                "Details": "USB Connected: " + device.get("Device Name", "Unknown")
            })

    except Exception as e:
        timeline.append({
            "Time": "Unknown",
            "Type": "USB Error",
            "Details": str(e)
        })

    timeline = sorted(timeline, key=lambda x: x["Time"], reverse=True)

    return timeline


if __name__ == "__main__":
    result = create_timeline()

    print("===== DIGITAL FORENSICS TIMELINE =====\n")

    for entry in result:
        print(f"[{entry['Time']}] {entry['Type']} -> {entry['Details']}")