"""JSON persistence for a repository."""
import json
import os

from core.blockchain import Blockchain


REPO_DIR = ".bvcs"          # our repo metadata folder (like .git)


def repo_path(repo_root: str) -> str:
    return os.path.join(repo_root, REPO_DIR)


def chain_file(repo_root: str) -> str:
    return os.path.join(repo_path(repo_root), "chain.json")


def branches_file(repo_root: str) -> str:
    return os.path.join(repo_path(repo_root), "branches.json")


def head_file(repo_root: str) -> str:
    return os.path.join(repo_path(repo_root), "HEAD.json")


def index_file(repo_root: str) -> str:
    return os.path.join(repo_path(repo_root), "index.json")


def ensure_repo_dir(repo_root: str) -> None:
    os.makedirs(repo_path(repo_root), exist_ok=True)


def save_chain(repo_root: str, chain: Blockchain) -> None:
    with open(chain_file(repo_root), "w", encoding="utf-8") as f:
        json.dump(chain.to_dict(), f, indent=2)


def load_chain(repo_root: str) -> Blockchain:
    path = chain_file(repo_root)
    if not os.path.exists(path):
        return Blockchain()
    with open(path, "r", encoding="utf-8") as f:
        return Blockchain.from_dict(json.load(f))


def save_json(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_json(path: str, default=None):
    if not os.path.exists(path):
        return default if default is not None else {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)