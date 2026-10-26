"""
Tests for the new Git-style object model: blobs, trees, and (later) diff.
Run with:  pytest tests/test_blobs_trees_diff.py -v
"""
import os
import tempfile

import pytest

from core.blob import BlobStore
from core.tree import TreeStore, build_tree_from_staging


# ====================================================================
# TEST 1 — Blob deduplication
# ====================================================================

class TestBlobDedup:
    """write() with identical content must produce exactly one file on disk."""

    def test_same_content_stored_once(self):
        with tempfile.TemporaryDirectory() as d:
            bs = BlobStore(d)
            bs.ensure_dirs()

            h1 = bs.write("hello")
            h2 = bs.write("hello")

            assert h1 == h2, "Same content must produce same hash"
            assert len(bs.list_all()) == 1, "Only ONE blob on disk"

    def test_different_content_stored_separately(self):
        with tempfile.TemporaryDirectory() as d:
            bs = BlobStore(d)
            bs.ensure_dirs()

            h1 = bs.write("hello")
            h2 = bs.write("world")

            assert h1 != h2
            assert len(bs.list_all()) == 2, "Two distinct blobs on disk"

    def test_read_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            bs = BlobStore(d)
            bs.ensure_dirs()

            h = bs.write("the quick brown fox")
            assert bs.read(h) == "the quick brown fox"

    def test_exists(self):
        with tempfile.TemporaryDirectory() as d:
            bs = BlobStore(d)
            bs.ensure_dirs()

            h = bs.write("exists-test")
            assert bs.exists(h) is True
            assert bs.exists("0" * 64) is False

    def test_read_missing_raises(self):
        with tempfile.TemporaryDirectory() as d:
            bs = BlobStore(d)
            bs.ensure_dirs()
            with pytest.raises(FileNotFoundError):
                bs.read("0" * 64)


# ====================================================================
# TEST 2 — Tree building and determinism
# ====================================================================

class TestTreeBuilding:
    """Trees must be deterministic, nestable, and flattened correctly."""

    def test_deterministic_hash(self):
        """Same staged files → same root tree hash."""
        with tempfile.TemporaryDirectory() as d:
            bs = BlobStore(d)
            ts = TreeStore(d)
            bs.ensure_dirs()
            ts.ensure_dirs()

            h_a = bs.write("content-a")
            h_b = bs.write("content-b")

            staged = {"a.txt": h_a, "b.txt": h_b}
            root1 = build_tree_from_staging(staged, bs, ts)
            root2 = build_tree_from_staging(staged, bs, ts)

            assert root1 == root2, "Same staging must produce same tree hash"

    def test_nested_dirs_create_nested_trees(self):
        """Staging 'src/lib/util.py' must create trees for src/ and src/lib/."""
        with tempfile.TemporaryDirectory() as d:
            bs = BlobStore(d)
            ts = TreeStore(d)
            bs.ensure_dirs()
            ts.ensure_dirs()

            h = bs.write("util code")
            staged = {"src/lib/util.py": h, "readme.txt": bs.write("hi")}

            root = build_tree_from_staging(staged, bs, ts)

            # Root tree should have two entries: "readme.txt" (blob) and "src" (tree)
            entries = ts.read(root)
            assert "readme.txt" in entries
            assert entries["readme.txt"]["type"] == "blob"
            assert "src" in entries
            assert entries["src"]["type"] == "tree"

            # "src" tree should have one entry: "lib" (tree)
            src_entries = ts.read(entries["src"]["hash"])
            assert "lib" in src_entries
            assert src_entries["lib"]["type"] == "tree"

            # "lib" tree should have one entry: "util.py" (blob)
            lib_entries = ts.read(src_entries["lib"]["hash"])
            assert "util.py" in lib_entries
            assert lib_entries["util.py"]["type"] == "blob"
            assert lib_entries["util.py"]["hash"] == h

    def test_flatten_roundtrip(self):
        """Flatten must return the exact flat map that was staged."""
        with tempfile.TemporaryDirectory() as d:
            bs = BlobStore(d)
            ts = TreeStore(d)
            bs.ensure_dirs()
            ts.ensure_dirs()

            h1 = bs.write("aaa")
            h2 = bs.write("bbb")
            h3 = bs.write("ccc")

            staged = {
                "a.txt": h1,
                "dir/b.txt": h2,
                "dir/sub/c.txt": h3,
            }
            root = build_tree_from_staging(staged, bs, ts)
            flat = ts.flatten(root)

            assert flat == staged, f"Flatten mismatch: {flat} vs {staged}"

    def test_tree_dedup(self):
        """Identical directory structures share the same tree hash."""
        with tempfile.TemporaryDirectory() as d:
            bs = BlobStore(d)
            ts = TreeStore(d)
            bs.ensure_dirs()
            ts.ensure_dirs()

            h = bs.write("same")
            staged = {"x.txt": h}

            root1 = build_tree_from_staging(staged, bs, ts)
            root2 = build_tree_from_staging(staged, bs, ts)

            assert root1 == root2
            # Only one tree object should exist (the root)
            assert len(ts.list_all()) == 1

    def test_empty_tree(self):
        """An empty staging area produces a valid (empty) tree."""
        with tempfile.TemporaryDirectory() as d:
            bs = BlobStore(d)
            ts = TreeStore(d)
            bs.ensure_dirs()
            ts.ensure_dirs()

            root = build_tree_from_staging({}, bs, ts)
            assert ts.exists(root)
            flat = ts.flatten(root)
            assert flat == {}

    def test_tree_object_count_for_nested(self):
        """Staging src/lib/util.py creates exactly 3 tree objects:
        root, src/, src/lib/."""
        with tempfile.TemporaryDirectory() as d:
            bs = BlobStore(d)
            ts = TreeStore(d)
            bs.ensure_dirs()
            ts.ensure_dirs()

            h = bs.write("code")
            build_tree_from_staging({"src/lib/util.py": h}, bs, ts)
            assert len(ts.list_all()) == 3
