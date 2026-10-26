"""SHA-256 hashing utilities."""
import hashlib
import os


def sha256_bytes(data: bytes) -> str:
    """Return hex SHA-256 of bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_str(text: str) -> str:
    """Return hex SHA-256 of a string."""
    return sha256_bytes(text.encode("utf-8"))


def hash_file(path: str) -> str:
    """Hash a file's contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_obj(obj) -> str:
    """Stable hash of a Python dict/list (JSON-serialized, key-sorted)."""
    import json
    serialized = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(serialized)