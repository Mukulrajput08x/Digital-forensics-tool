import hashlib

def hash_file(filename):

    md5_hash = hashlib.md5()
    sha256_hash = hashlib.sha256()

    with open(filename,"rb") as f:
        while True:
            data = f.read(4096)
            if not data:
                break

            md5_hash.update(data)
            sha256_hash.update(data)

    return {
        "md5": md5_hash.hexdigest(),
        "sha256": sha256_hash.hexdigest()
    }