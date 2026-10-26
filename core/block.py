"""Block = one commit in our blockchain VCS."""
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Optional
from core.hashing import sha256_str, hash_obj


@dataclass
class Block:
    # Core identity
    parent_hash: str                # hash of previous block ("" for genesis)
    merkle_root: str                # root of file hashes in this commit
    author: str
    message: str
    timestamp: float
    files: dict                     # {relative_path: sha256_of_content}
    # Branching metadata
    branch: str = "main"
    # Merge metadata (None if not a merge commit)
    merge_parents: list = field(default_factory=list)
    # Optional: actual file contents (for a real VCS you'd store blobs separately)
    contents: dict = field(default_factory=dict)   # {path: text_content}

    # Computed
    block_hash: str = ""

    def compute_hash(self) -> str:
        """Hash of everything except block_hash itself."""
        payload = {
            "parent_hash": self.parent_hash,
            "merkle_root": self.merkle_root,
            "author": self.author,
            "message": self.message,
            "timestamp": self.timestamp,
            "files": self.files,
            "branch": self.branch,
            "merge_parents": sorted(self.merge_parents),
        }
        return sha256_str(json.dumps(payload, sort_keys=True, separators=(",", ":")))

    def seal(self):
        """Compute and set block_hash."""
        self.block_hash = self.compute_hash()

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Block":
        return Block(**d)

    def is_valid(self) -> bool:
        """Self-check: stored hash matches recomputed hash."""
        return self.block_hash == self.compute_hash()