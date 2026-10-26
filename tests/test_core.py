"""Basic sanity tests — run with: pytest tests/"""
import os
import tempfile
import pytest

from core.merkle import merkle_root, merkle_proof, verify_proof
from core.hashing import sha256_str
from core.repository import Repository


def test_merkle_root_deterministic():
    hashes = [sha256_str("a"), sha256_str("b"), sha256_str("c")]
    assert merkle_root(hashes) == merkle_root(hashes)


def test_merkle_proof():
    hashes = [sha256_str(x) for x in ["a", "b", "c", "d"]]
    root = merkle_root(hashes)
    for i, h in enumerate(hashes):
        proof = merkle_proof(hashes, i)
        assert verify_proof(h, proof, root)


def test_init_and_commit():
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "a.txt"), "w") as f:
            f.write("hello")

        repo = Repository(d)
        repo.init()
        repo.add("a.txt")
        blk = repo.commit("me", "first commit")
        assert blk.parent_hash != ""
        assert repo.verify()["valid"]


def test_tamper_detected():
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "a.txt"), "w") as f:
            f.write("hello")
        repo = Repository(d)
        repo.init()
        repo.add("a.txt")
        repo.commit("me", "first")
        # tamper
        repo.chain.blocks[1].message = "hacked"
        rep = repo.verify()
        assert rep["valid"] is False


def test_branch_and_merge():
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "a.txt"), "w") as f:
            f.write("line1\n")

        repo = Repository(d)
        repo.init()
        repo.add("a.txt")
        repo.commit("me", "initial")

        # branch
        from core import branch as br
        br.create_branch(repo, "feature")
        br.switch_branch(repo, "feature")
        with open(os.path.join(d, "b.txt"), "w") as f:
            f.write("feature file")
        repo = Repository(d)
        repo.add("b.txt")
        repo.commit("me", "feature work")

        # merge into main
        from core import merge as mg
        br.switch_branch(repo, "main")
        repo = Repository(d)
        result = mg.three_way_merge(repo, target="main", source="feature", author="me")
        assert result["merged"] is True
        assert result["commit"].merge_parents