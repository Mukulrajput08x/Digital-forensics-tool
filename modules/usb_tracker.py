import platform
from datetime import datetime, timedelta

# Safe import for Windows/Linux
if platform.system() == "Windows":
    import winreg
else:
    winreg = None


def filetime_to_dt(ft):
    try:
        return datetime(1601, 1, 1) + timedelta(microseconds=ft / 10)
    except:
        return "Unknown"


def get_usb_devices():

    # Agar Windows nahi hai → safe return
    if winreg is None:
        return [{
            "Device Name": "Not Supported",
            "Friendly Name": "USB tracking works only on Windows",
            "Serial Number": "-",
            "Checked Time": "-"
        }]

    usb_list = []

    try:
        reg_path = r"SYSTEM\CurrentControlSet\Enum\USBSTOR"

        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)

        total_devices = winreg.QueryInfoKey(key)[0]

        for i in range(total_devices):

            device_name = winreg.EnumKey(key, i)
            device_key = winreg.OpenKey(key, device_name)

            total_serials = winreg.QueryInfoKey(device_key)[0]

            for j in range(total_serials):

                serial_number = winreg.EnumKey(device_key, j)
                serial_key = winreg.OpenKey(device_key, serial_number)

                try:
                    friendly_name, _ = winreg.QueryValueEx(
                        serial_key,
                        "FriendlyName"
                    )
                except:
                    friendly_name = "Unknown USB Device"

                try:
                    ft = winreg.QueryInfoKey(serial_key)[2]
                    last_time = filetime_to_dt(ft)
                except:
                    last_time = "Unknown"

                usb_list.append({
                    "Device Name": device_name,
                    "Friendly Name": friendly_name,
                    "Serial Number": serial_number,
                    "Checked Time": last_time
                })

    except Exception as e:
        usb_list.append({
            "Device Name": "Error",
            "Friendly Name": "N/A",
            "Serial Number": "N/A",
            "Checked Time": str(e)
        })

    return usb_list


# Test run (sirf local execution ke liye)
if __name__ == "__main__":
    print("USB Tracker Started\n")

    usb_devices = get_usb_devices()

    print("Total USB Devices:", len(usb_devices))
    print("\n===== USB Devices Found =====\n")

    for usb in usb_devices:
        print("Friendly Name :", usb["Friendly Name"])
        print("Device Name   :", usb["Device Name"])
        print("Serial Number :", usb["Serial Number"])
        print("Checked Time  :", usb["Checked Time"])
        print("-" * 60)