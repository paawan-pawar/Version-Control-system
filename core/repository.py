"""High-level repo operations: init, add, commit, log, status."""
import os
import time
from typing import Optional

from core.block import Block
from core.blockchain import Blockchain
from core.hashing import sha256_str
from core.merkle import merkle_root
from core import storage


class Repository:
    def __init__(self, root: str):
        self.root = os.path.abspath(root)
        self.chain = storage.load_chain(self.root)
        self.branches = storage.load_json(storage.branches_file(self.root), {})
        self.head = storage.load_json(storage.head_file(self.root), {})
        # Load staging from disk (persisted across CLI invocations)
        index = storage.load_json(storage.index_file(self.root), {})
        self.staged: dict[str, str] = index.get("staged", {})                # path -> sha256
        self.staged_contents: dict[str, str] = index.get("staged_contents", {})  # path -> text

    # ---------- init ----------
    def init(self, default_branch: str = "main"):
        storage.ensure_repo_dir(self.root)
        if self.chain.blocks:
            raise FileExistsError("Repository already initialized")

        # Genesis block
        genesis = Block(
            parent_hash="",
            merkle_root=merkle_root([]),
            author="system",
            message="Genesis block",
            timestamp=time.time(),
            files={},
            branch=default_branch,
            contents={},
        )
        genesis.seal()
        self.chain.add_block(genesis)

        self.branches = {default_branch: genesis.block_hash}
        self.head = {"branch": default_branch, "commit": genesis.block_hash}
        self._persist()
        return genesis

    # ---------- staging ----------
    def add(self, path: str):
        """Stage a file from working directory."""
        full = os.path.join(self.root, path)
        if not os.path.isfile(full):
            raise FileNotFoundError(path)
        with open(full, "r", encoding="utf-8") as f:
            content = f.read()
        self.staged[path] = sha256_str(content)
        self.staged_contents[path] = content
        self._save_index()

    # ---------- commit ----------
    def commit(self, author: str, message: str, branch: Optional[str] = None) -> Block:
        if not self.staged:
            raise ValueError("Nothing staged. Use `add` first.")

        if branch is None:
            branch = self.head.get("branch", "main")

        parent_hash = self.branches.get(branch, "")
        # Merge parent if HEAD was set by a merge in progress (optional feature)
        merge_parents = self.head.get("merge_parents", [])

        files = dict(self.staged)
        contents = dict(self.staged_contents)
        mr = merkle_root(sorted(files.values()))

        blk = Block(
            parent_hash=parent_hash,
            merkle_root=mr,
            author=author,
            message=message,
            timestamp=time.time(),
            files=files,
            branch=branch,
            merge_parents=merge_parents,
            contents=contents,
        )
        self.chain.add_block(blk)

        self.branches[branch] = blk.block_hash
        self.head = {"branch": branch, "commit": blk.block_hash}

        self.staged.clear()
        self.staged_contents.clear()
        self._persist()
        self._save_index()
        return blk

    # ---------- inspect ----------
    def log(self, limit: int = 20) -> list[Block]:
        tip = self.head.get("commit", "")
        if not tip:
            return []
        return self.chain.ancestors(tip)[:limit]

    def verify(self) -> dict:
        return self.chain.validate_chain()

    def status(self) -> dict:
        return {
            "branch": self.head.get("branch"),
            "head": self.head.get("commit", "")[:10],
            "staged": list(self.staged.keys()),
            "branches": self.branches,
        }

    # ---------- persistence ----------
    def _persist(self):
        storage.ensure_repo_dir(self.root)
        storage.save_chain(self.root, self.chain)
        storage.save_json(storage.branches_file(self.root), self.branches)
        storage.save_json(storage.head_file(self.root), self.head)

    def _save_index(self):
        """Persist staging area to disk so add/commit work across CLI calls."""
        storage.ensure_repo_dir(self.root)
        storage.save_json(storage.index_file(self.root), {
            "staged": self.staged,
            "staged_contents": self.staged_contents,
        })