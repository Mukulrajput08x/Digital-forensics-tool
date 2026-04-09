import os
from datetime import datetime
import platform

print("Deleted File Recovery Started")

def recover_deleted():
    deleted_files = []
    
    # Adjust recycle bin path based on OS
    if platform.system() == "Windows":
        recycle_bin = r"C:\$Recycle.Bin"
    else:
        print("Recycle Bin check only works on Windows")
        return deleted_files
    
    print("Checking Recycle Bin:", recycle_bin)
    
    if not os.path.exists(recycle_bin):
        print("Recycle Bin Not Found")
        return deleted_files
    
    for root, dirs, files in os.walk(recycle_bin):
        for file in files:
            full_path = os.path.join(root, file)
            
            try:
                size = os.path.getsize(full_path)
                modified_time = datetime.fromtimestamp(
                    os.path.getmtime(full_path)
                ).strftime("%d-%m-%Y %I:%M:%S %p")
                
                deleted_files.append({
                    "File Name": file,
                    "Location": full_path,
                    "Size": size,
                    "Modified Time": modified_time
                })
                
            except PermissionError:
                print("Permission Denied:", full_path)
            except Exception as e:
                print("Error Reading File:", full_path)
                print("Reason:", e)
    
    return deleted_files

results = recover_deleted()

print("""
===== Deleted Files Found =====
""")
print("Total Files:", len(results))

for item in results:
    print("File Name     :", item["File Name"])
    print("Location      :", item["Location"])
    print("Size (Bytes)  :", item["Size"])
    print("Modified Time :", item["Modified Time"])
    print("-" * 60)