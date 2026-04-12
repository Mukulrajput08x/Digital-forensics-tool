import os
import struct
import platform
from datetime import datetime, timedelta


def read_recycle_metadata(i_file_path):
    try:
        with open(i_file_path, "rb") as f:
            data = f.read()

        # Basic validation
        if len(data) < 28:
            return None, None, None

        # FILETIME at offset 16:24
        filetime = struct.unpack("<Q", data[16:24])[0]
        deleted_time = datetime(1601, 1, 1) + timedelta(microseconds=filetime / 10)

        # Original path usually starts at offset 28 in modern Windows recycle metadata
        raw_path = data[28:]

        # Decode UTF-16LE and strip nulls
        original_path = raw_path.decode("utf-16le", errors="ignore").split("\x00")[0].strip()

        # Fallback if decoding fails
        if not original_path:
            return None, None, deleted_time.strftime("%d-%m-%Y %I:%M:%S %p")

        original_name = os.path.basename(original_path)

        return original_name, original_path, deleted_time.strftime("%d-%m-%Y %I:%M:%S %p")

    except Exception:
        return None, None, None


def recover_deleted():
    deleted_files = []

    if platform.system() != "Windows":
        return deleted_files

    recycle_bin = r"C:\$Recycle.Bin"

    if not os.path.exists(recycle_bin):
        return deleted_files

    for root, dirs, files in os.walk(recycle_bin):
        for file in files:
            if not file.startswith("$I"):
                continue

            i_file_path = os.path.join(root, file)

            try:
                original_name, original_path, deleted_time = read_recycle_metadata(i_file_path)

                # Matching $R file
                r_file_name = "$R" + file[2:]
                r_file_path = os.path.join(root, r_file_name)
                size = os.path.getsize(r_file_path) if os.path.exists(r_file_path) else 0

                deleted_files.append({
                    "File Name": original_name if original_name else file,
                    "Location": original_path if original_path else i_file_path,
                    "Size": size,
                    "Modified Time": deleted_time if deleted_time else "Unknown"
                })

            except Exception as e:
                deleted_files.append({
                    "File Name": file,
                    "Location": i_file_path,
                    "Size": 0,
                    "Modified Time": f"Error: {e}"
                })

    return deleted_files