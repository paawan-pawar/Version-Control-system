"""
Three-way merge between two branches.

Produces a merge commit whose parents are the tips of both branches
(merge_parents = [other_branch_tip]).  Conflict detection: any file where
both sides diverged from the LCA with different contents is a conflict.
"""
from core.block import Block
from core.hashing import sha256_str
from core.merkle import merkle_root
from core.repository import Repository


def _files_at(chain, commit_hash: str) -> dict:
    """All files visible at a given commit (walk from commit to genesis)."""
    seen = {}
    for blk in chain.ancestors(commit_hash):
        for path, h in blk.files.items():
            if path not in seen:
                seen[path] = h
    return seen


def _contents_at(chain, commit_hash: str) -> dict:
    """Actual text contents visible at a commit."""
    seen = {}
    for blk in chain.ancestors(commit_hash):
        for path, content in blk.contents.items():
            if path not in seen:
                seen[path] = content
    return seen


def three_way_merge(repo: Repository, target: str, source: str, author: str) -> dict:
    """
    Merge `source` into `target` (target must be checked out).
    Returns dict with keys: merged (bool), conflicts (list), commit (Block|None).
    """
    chain = repo.chain
    if target not in repo.branches:
        raise ValueError(f"Target branch '{target}' not found")
    if source not in repo.branches:
        raise ValueError(f"Source branch '{source}' not found")

    target_tip = repo.branches[target]
    source_tip = repo.branches[source]

    lca = chain.find_lca(target_tip, source_tip)
    if lca is None:
        raise ValueError("No common ancestor — cannot merge unrelated histories")

    base_files = _files_at(chain, lca.block_hash)
    ours_files = _files_at(chain, target_tip)
    theirs_files = _files_at(chain, source_tip)

    base_contents = _contents_at(chain, lca.block_hash)
    ours_contents = _contents_at(chain, target_tip)
    theirs_contents = _contents_at(chain, source_tip)

    all_paths = set(base_files) | set(ours_files) | set(theirs_files)
    merged_contents: dict[str, str] = {}
    conflicts: list[str] = []

    for path in sorted(all_paths):
        b = base_files.get(path)
        o = ours_files.get(path)
        t = theirs_files.get(path)

        if o == t:
            # same on both sides (or both deleted)
            if o is not None:
                merged_contents[path] = ours_contents.get(path, "")
            continue

        if o == b:
            # only theirs changed
            if t is not None:
                merged_contents[path] = theirs_contents.get(path, "")
            continue

        if t == b:
            # only ours changed
            if o is not None:
                merged_contents[path] = ours_contents.get(path, "")
            continue

        # Both changed differently -> conflict
        conflicts.append(path)

    if conflicts:
        return {"merged": False, "conflicts": conflicts, "commit": None}

    # Build merge commit
    files = {p: sha256_str(c) for p, c in merged_contents.items()}
    mr = merkle_root(sorted(files.values()))

    merge_block = Block(
        parent_hash=target_tip,
        merkle_root=mr,
        author=author,
        message=f"Merge branch '{source}' into '{target}'",
        timestamp=__import__("time").time(),
        files=files,
        branch=target,
        merge_parents=[source_tip],
        contents=merged_contents,
    )
    chain.add_block(merge_block)

    repo.branches[target] = merge_block.block_hash
    repo.head = {"branch": target, "commit": merge_block.block_hash}
    repo._persist()

    return {"merged": True, "conflicts": [], "commit": merge_block}