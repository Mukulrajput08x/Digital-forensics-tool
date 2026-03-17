import os

def recover_deleted():

    deleted_files = []

    recycle_bin = "C:\\$Recycle.Bin"

    if os.path.exists(recycle_bin):

        for root, dirs, files in os.walk(recycle_bin):
            for file in files:
                deleted_files.append(file)

    return deleted_files