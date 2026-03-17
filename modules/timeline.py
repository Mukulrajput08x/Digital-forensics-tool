import os
from datetime import datetime

def get_timeline(folder_path):

    timeline = []

    for root, dirs, files in os.walk(folder_path):
        for file in files:

            path = os.path.join(root, file)

            created = os.path.getctime(path)
            modified = os.path.getmtime(path)

            timeline.append({
                "file": file,
                "created": datetime.fromtimestamp(created),
                "modified": datetime.fromtimestamp(modified)
            })

    return timeline