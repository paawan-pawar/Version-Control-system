"""
Tree objects: directory snapshots pointing to blob hashes and sub-trees.

Each tree is stored at:
    .bvcs/objects/trees/<hash[:2]>/<hash[2:]>

A tree's hash is SHA-256 of its canonical (sorted, compact) JSON entries,
so identical directory layouts produce identical hashes.
"""
import os
import json

from core.hashing import sha256_str, hash_obj
from core.blob import BlobStore


class TreeStore:
    """Read/write content-addressed tree (directory snapshot) objects."""

    def __init__(self, repo_root: str):
        self.repo_root = os.path.abspath(repo_root)
        self.base_dir = os.path.join(self.repo_root, ".bvcs", "objects", "trees")

    def ensure_dirs(self):
        """Create the trees directory if it doesn't exist."""
        os.makedirs(self.base_dir, exist_ok=True)

    # ---------------------------------------------------------------- paths
    def _object_path(self, tree_hash: str) -> str:
        return os.path.join(self.base_dir, tree_hash[:2], tree_hash[2:])

    # ---------------------------------------------------------------- write
    def write(self, entries: dict) -> str:
        """
        Store a tree object and return its hash.

        entries = {
            "readme.txt": {"type": "blob", "hash": "<blob_hash>"},
            "src":        {"type": "tree", "hash": "<tree_hash>"},
        }

        Hash = sha256 of the canonical sorted JSON of entries.
        Deduplication: same entries → same hash → one file on disk.
        """
        tree_hash = hash_obj(entries)
        path = self._object_path(tree_hash)

        if os.path.exists(path):
            return tree_hash          # already stored — dedup

        os.makedirs(os.path.dirname(path), exist_ok=True)

        obj = {"type": "tree", "entries": entries, "hash": tree_hash}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, separators=(",", ":"))

        return tree_hash

    # ---------------------------------------------------------------- read
    def read(self, tree_hash: str) -> dict:
        """Return the entries dict of a tree, or raise if missing."""
        path = self._object_path(tree_hash)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Tree not found: {tree_hash}")
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        return obj["entries"]

    # ---------------------------------------------------------------- query
    def exists(self, tree_hash: str) -> bool:
        return os.path.exists(self._object_path(tree_hash))

    def list_all(self) -> list[str]:
        """Return a sorted list of every tree hash in the store."""
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

    # ---------------------------------------------------------------- flatten
    def flatten(self, tree_hash: str, prefix: str = "") -> dict:
        """
        Recursively walk the tree and return a flat map:
            {"src/a.txt": blob_hash, "readme.txt": blob_hash, ...}

        Used by diff, checkout, and merge to get a full file listing.
        """
        entries = self.read(tree_hash)
        result = {}
        for name, info in sorted(entries.items()):
            full_path = f"{prefix}{name}" if not prefix else f"{prefix}/{name}"
            if info["type"] == "blob":
                result[full_path] = info["hash"]
            elif info["type"] == "tree":
                result.update(self.flatten(info["hash"], prefix=full_path))
        return result


# ====================================================================
# Helper: build nested tree from a flat staging map
# ====================================================================

def build_tree_from_staging(staged: dict, blob_store: BlobStore,
                            tree_store: TreeStore) -> str:
    """
    Convert a flat file map into nested tree objects and return the
    root tree hash.

    staged = {"src/a.txt": blob_hash, "readme.txt": blob_hash, ...}

    Algorithm:
        1. Group paths by top-level directory component.
        2. For plain files (no '/'), add a blob entry.
        3. For directories, recurse to build a sub-tree, then add a
           tree entry.
        4. Write the tree object and return its hash.

    This automatically creates intermediate trees for nested paths
    like "src/lib/util.py".
    """
    # Partition into {name: blob_hash} and {dir: {subpath: blob_hash}}
    direct_files: dict[str, str] = {}            # name -> blob_hash
    subdirs: dict[str, dict[str, str]] = {}      # dir  -> {rest: blob_hash}

    for path, blob_hash in staged.items():
        # Normalise separators to forward slash
        path = path.replace("\\", "/")
        if "/" in path:
            top, rest = path.split("/", 1)
            subdirs.setdefault(top, {})[rest] = blob_hash
        else:
            direct_files[path] = blob_hash

    entries: dict[str, dict] = {}

    # Leaf files
    for name, blob_hash in direct_files.items():
        entries[name] = {"type": "blob", "hash": blob_hash}

    # Sub-directories (recurse)
    for dirname, sub_staged in subdirs.items():
        sub_tree_hash = build_tree_from_staging(sub_staged, blob_store,
                                                tree_store)
        entries[dirname] = {"type": "tree", "hash": sub_tree_hash}

    return tree_store.write(entries)


def write_tree_to_working_dir(root_tree_hash: str, tree_store: TreeStore,
                              blob_store: BlobStore, dest_dir: str):
    """
    Materialise a tree onto disk — used for checkout and merge output.
    Writes every blob referenced by the tree into dest_dir.
    """
    flat = tree_store.flatten(root_tree_hash)
    for rel_path, blob_hash in flat.items():
        full = os.path.join(dest_dir, rel_path.replace("/", os.sep))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        content = blob_store.read(blob_hash)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
