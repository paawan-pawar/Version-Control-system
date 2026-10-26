# BVCS — Blockchain Version Control System

A GitHub-like VCS where every commit is a cryptographically linked block.
Built with Python + Flask + SHA-256.

## Features
- SHA-256 hashing for files, commits, and Merkle roots
- Immutable commit chain — any tampering breaks verification
- Branching (create, switch, delete)
- 3-way merge with conflict detection
- CLI + Web UI (GitHub-like viewer)

## Quick start

```bash
pip install -r requirements.txt

# 1. Initialize a repo in a folder
mkdir myproject && cd myproject
python -m cli.main init

# 2. Create a file, add, commit
echo "hello" > a.txt
python -m cli.main add a.txt
python -m cli.main commit -a "alice" -m "first commit"

# 3. Branch + merge
python -m cli.main branch feature
python -m cli.main checkout feature
echo "world" > b.txt
python -m cli.main add b.txt
python -m cli.main commit -a "alice" -m "feature work"
python -m cli.main checkout main
python -m cli.main merge main feature -a "alice"

# 4. Verify chain
python -m cli.main verify
python -m cli.main log

# 5. Web UI
cd .. && BVCS_REPO=/path/to/myproject flask --app app run