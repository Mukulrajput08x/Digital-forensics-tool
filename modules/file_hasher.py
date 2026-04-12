import hashlib
import os


def hash_file(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    md5_hash = hashlib.md5()
    sha256_hash = hashlib.sha256()

    with open(path, "rb") as file:
        while True:
            data = file.read(4096)
            if not data:
                break
            md5_hash.update(data)
            sha256_hash.update(data)

    return {
        "md5": md5_hash.hexdigest(),
        "sha256": sha256_hash.hexdigest()
    }