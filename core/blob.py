"""
Content-addressed blob store (like Git's object/blob layer).

Each blob is stored at:
    .bvcs/objects/blobs/<hash[:2]>/<hash[2:]>

Deduplication is automatic: same content → same hash → one file on disk.
"""
import os
import json

from core.hashing import sha256_str


class BlobStore:
    """Read/write content-addressed file blobs."""

    def __init__(self, repo_root: str):
        self.repo_root = os.path.abspath(repo_root)
        self.base_dir = os.path.join(self.repo_root, ".bvcs", "objects", "blobs")

    def ensure_dirs(self):
        """Create the blobs directory if it doesn't exist."""
        os.makedirs(self.base_dir, exist_ok=True)

    # ---------------------------------------------------------------- paths
    def _object_path(self, blob_hash: str) -> str:
        """Return the sharded file path for a given hash."""
        return os.path.join(self.base_dir, blob_hash[:2], blob_hash[2:])

    # ---------------------------------------------------------------- write
    def write(self, content: str) -> str:
        """
        Store content and return its SHA-256 hash.
        If the blob already exists on disk, skip the write (dedup).
        """
        blob_hash = sha256_str(content)
        path = self._object_path(blob_hash)

        if os.path.exists(path):
            return blob_hash          # already stored — dedup!

        os.makedirs(os.path.dirname(path), exist_ok=True)

        obj = {"type": "blob", "content": content, "hash": blob_hash}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, separators=(",", ":"))

        return blob_hash

    # ---------------------------------------------------------------- read
    def read(self, blob_hash: str) -> str:
        """Return the text content of a blob, or raise if missing."""
        path = self._object_path(blob_hash)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Blob not found: {blob_hash}")
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        return obj["content"]

    # ---------------------------------------------------------------- query
    def exists(self, blob_hash: str) -> bool:
        """Check whether a blob is already stored."""
        return os.path.exists(self._object_path(blob_hash))

    def list_all(self) -> list[str]:
        """Return a sorted list of every blob hash in the store."""
        hashes = []
        if not os.path.isdir(self.base_dir):
            return hashes
        for prefix in sorted(os.listdir(self.base_dir)):
            prefix_dir = os.path.join(self.base_dir, prefix)
            if not os.path.isdir(prefix_dir):
                continue
            for suffix in sorted(os.listdir(prefix_dir)):
                hashes.append(prefix + suffix)
        return hashes
