import winreg
from datetime import datetime, timedelta

def filetime_to_dt(ft):
    # Windows FILETIME → Python datetime
    return datetime(1601,1,1) + timedelta(microseconds=ft/10)

def get_usb_devices():

    usb_list = []

    try:
        reg_path = r"SYSTEM\CurrentControlSet\Enum\USBSTOR"
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)

        for i in range(winreg.QueryInfoKey(key)[0]):

            device_name = winreg.EnumKey(key, i)
            device_key = winreg.OpenKey(key, device_name)

            for j in range(winreg.QueryInfoKey(device_key)[0]):

                serial_number = winreg.EnumKey(device_key, j)
                serial_key = winreg.OpenKey(device_key, serial_number)

                try:
                    ft = winreg.QueryInfoKey(serial_key)[2]
                    last_time = filetime_to_dt(ft)
                except:
                    last_time = "Unknown"

                usb_list.append({
                    "Device Name": device_name,
                    "Serial Number": serial_number,
                    "Checked Time": last_time
                })

    except Exception as e:

        usb_list.append({
            "Device Name": "Error",
            "Serial Number": "N/A",
            "Checked Time": str(e)
        })

    return usb_list