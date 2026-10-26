"""Branch operations."""
from core.repository import Repository


def list_branches(repo: Repository) -> dict:
    return repo.branches


def create_branch(repo: Repository, name: str, from_branch: str | None = None) -> str:
    if name in repo.branches:
        raise ValueError(f"Branch '{name}' already exists")
    src = from_branch or repo.head.get("branch", "main")
    if src not in repo.branches:
        raise ValueError(f"Source branch '{src}' not found")
    repo.branches[name] = repo.branches[src]
    repo._persist()
    return repo.branches[name]


def switch_branch(repo: Repository, name: str) -> dict:
    if name not in repo.branches:
        raise ValueError(f"Branch '{name}' not found")
    repo.head = {"branch": name, "commit": repo.branches[name]}
    repo._persist()
    return repo.head


def delete_branch(repo: Repository, name: str):
    if name == repo.head.get("branch"):
        raise ValueError("Cannot delete the checked-out branch")
    if name not in repo.branches:
        raise ValueError(f"Branch '{name}' not found")
    del repo.branches[name]
    repo._persist()