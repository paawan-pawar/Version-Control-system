# BVCS — Blockchain-based Version Control System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Web%20UI-green.svg)](https://flask.palletsprojects.com/)
[![Tests](https://img.shields.io/badge/Pytest-16%2F16%20Passing-brightgreen.svg)](https://pytest.org/)
[![Cryptography](https://img.shields.io/badge/Security-SHA--256%20%2B%20Merkle-orange.svg)]()

A modern, decentralized, GitHub-like Version Control System (VCS) where **every commit is a cryptographically linked block in a blockchain**. Built in Python with SHA-256 hashing, Merkle tree verification, DAG-safe branching, 3-way merge resolution, content-addressed blob storage, and an interactive Flask Web UI.

---

## 📌 Project Overview

Traditional version control systems like Git rely on commit DAGs with SHA-1/SHA-256 hashes, but history can still be altered via force pushes (`git push -f`) or rebasing. 

**BVCS** combines standard Git capabilities with **blockchain immutability**:
1. **Every Commit is a Sealed Block**: Each block stores metadata, author, commit message, timestamp, parent block hash, and a cryptographic **Merkle Root** representing the state of all tracked files.
2. **Strict Immutability & Tamper Detection**: If any historical file content, timestamp, or block header is modified by even a single byte, all downstream block hashes are invalidated immediately.
3. **Branching & 3-Way Merging**: Supports branching, switching (`checkout`), and three-way merging using Lowest Common Ancestor (LCA) detection and conflict marking.
4. **Content-Addressed Storage**: Content-addressed blob deduplication ensures identical files share storage without redundancy.
5. **Interactive Web Dashboard**: A GitHub-like visual explorer featuring real-time commit history, branch management, DAG visualization, and tamper-detection indicators.

---

## 🏗️ Architecture

```
                  ┌────────────────────────────────────────┐
                  │              Genesis Block             │
                  │ Block #0 | Hash: 39dfcb... | Parent: ∅ │
                  └───────────────────▲────────────────────┘
                                      │
                                (parent_hash)
                                      │
                  ┌───────────────────┴────────────────────┐
                  │              Commit Block #1           │
                  │ Block #1 | Hash: 6cfe27...             │
                  │ Merkle Root: 1d8d49...                 │
                  └───────────────────▲────────────────────┘
                                      │
                         ┌────────────┴────────────┐
                         │                         │
                  (main branch)             (feature branch)
                         │                         │
            ┌────────────┴────────────┐            │
            │      Commit Block #2    │            │
            │ Block #2                │            │
            └────────────▲────────────┘            │
                         │                         │
                         └────────────┬────────────┘
                                      │
                         ┌────────────┴────────────┐
                         │    Merge Block (LCA)    │
                         │ Parents: [Block 2, ...] │
                         └─────────────────────────┘
```

### Cryptographic Stack:
- **SHA-256**: Used for content hashing, tree hashing, and block sealing.
- **Merkle Tree**: Hierarchical hash tree of all file hashes. Allows verification of any individual file's presence via Merkle inclusion proofs in $O(\log N)$ time.
- **DAG Chain Validation**: Verifies that every block correctly links to an existing parent in the history and re-computes hashes on-demand.

---

## 📁 Project Structure

```
blockchain-vcs/
├── app.py                      # Flask web server & GitHub-like UI
├── requirements.txt            # Project dependencies
├── README.md                   # Documentation & CLI reference
├── core/
│   ├── __init__.py
│   ├── hashing.py              # SHA-256 utilities
│   ├── merkle.py               # Merkle Tree calculation & proofs
│   ├── block.py                # Block data structure and sealing
│   ├── blockchain.py           # Blockchain validation & DAG history
│   ├── repository.py           # Core repo operations (init, add, commit)
│   ├── branch.py               # Branch management & HEAD tracking
│   ├── merge.py                # 3-way merge logic & conflict detection
│   ├── blob.py                 # Content-addressed blob store & deduplication
│   ├── tree.py                 # Git-style tree snapshots & nesting
│   └── storage.py              # JSON disk persistence (.bvcs/)
├── cli/
│   ├── __init__.py
│   └── main.py                 # Command-line interface
├── web/
│   ├── static/
│   │   └── style.css           # Modern dark-mode styling
│   └── templates/
│       ├── base.html           # Main layout and navigation
│       ├── index.html          # Commits list & tamper alerts
│       ├── commit.html         # Commit details & file viewer
│       ├── branches.html       # Branch creation & merge forms
│       └── graph.html          # DAG chain visualizer
└── tests/
    ├── test_core.py            # Unit tests for Merkle, chain & merge
    └── test_blobs_trees_diff.py # Tests for blob dedup & tree building
```

---

## 🚀 Installation & Setup

### 1. Clone the repository
```powershell
git clone https://github.com/paawan-pawar/Version-Control-system.git
cd Version-Control-system
```

### 2. Create and activate a virtual environment (optional but recommended)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1   # On Windows (PowerShell)
# source venv/bin/activate    # On Linux / macOS
```

### 3. Install dependencies
```powershell
pip install -r requirements.txt
```

---

## 💻 CLI Commands & Usage

All commands can be run with `python cli/main.py <command>` or `python -m cli.main <command>`.

### 1. Initialize a Repository
Creates the `.bvcs/` repository directory and seals the Genesis block (Block #0).
```powershell
python cli/main.py init
```

### 2. Stage Files (`add`)
Stage modified or new files to the staging index:
```powershell
# Create a file
Set-Content -Path "hello.txt" -Value "Hello, Blockchain VCS!"

# Stage the file
python cli/main.py add hello.txt
```

### 3. Commit Changes (`commit`)
Seals a new block with the staged files, computes the Merkle root, and links to the current HEAD block:
```powershell
python cli/main.py commit -m "Add hello.txt" -a "Alice"
```
*(Note: `-a / --author` is optional and defaults to `"user"`).*

### 4. View Commit Log (`log`)
Shows the history of blocks, hashes, authors, and Merkle roots:
```powershell
python cli/main.py log
```

### 5. Check Working State (`status`)
Shows current branch, HEAD block hash, and currently staged files:
```powershell
python cli/main.py status
```

### 6. Verify Blockchain Integrity (`verify`)
Traverses the blockchain from genesis to head, recalculating all SHA-256 hashes to verify no blocks or files have been tampered with:
```powershell
python cli/main.py verify
```

### 7. Branching & Merging

#### Create a new branch:
```powershell
python cli/main.py branch feature-login
```

#### Switch to a branch:
```powershell
python cli/main.py checkout feature-login
```

#### Make a commit on the branch:
```powershell
Set-Content -Path "login.py" -Value "def login(): return True"
python cli/main.py add login.py
python cli/main.py commit -m "Implement login feature"
```

#### Switch back to main and merge:
```powershell
python cli/main.py checkout main
python cli/main.py merge main feature-login -a "Alice"
```

---

## 🌐 Running the Web Dashboard

The Flask web UI provides a GitHub-like experience for inspecting commits, viewing file contents, managing branches, and monitoring blockchain validity.

1. **Start the web server**:
   ```powershell
   python app.py
   ```
2. **Open in browser**:
   Navigate to **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

### Available Views:
- **`/` (Commits)**: Complete list of blocks, authors, messages, branches, and live blockchain validity status badge.
- **`/commit/<hash>`**: Deep-dive into an individual block: displays parent hash, Merkle root, files map, and stored source code.
- **`/branches`**: List active branches, checkout/switch between them, create new branches, or execute a 3-way merge.
- **`/graph`**: Visual graph of the commit chain showing block links and merge parents.
- **`/api/verify`**: JSON endpoint returning the cryptographic verification report.

---

## 🧪 Running Automated Tests

Run the complete test suite with `pytest`:
```powershell
python -m pytest tests/ -v
```

All 16 tests cover:
- Deterministic Merkle Root calculation
- Merkle inclusion proof generation and validation
- Repository initialization and multi-block commit sealing
- Chain tamper detection
- DAG-safe branching and 3-way merge resolution
- Content-addressed blob deduplication and round-trip read/writes
- Deterministic tree object generation and nested directory support

---

## 🛡️ Demonstrating Tamper Detection (Viva / Demo Guide)

To prove to your mentor that the blockchain prevents unauthorized history manipulation:

1. **Verify original state**:
   ```powershell
   python cli/main.py verify
   # Output: Chain valid! Checked N blocks.
   ```
2. **Simulate a malicious attack**:
   Open `.bvcs/chain.json` and alter any character in an earlier commit message or file content.
3. **Verify again**:
   ```powershell
   python cli/main.py verify
   ```
4. **Result**:
   The system immediately flags a **tamper detection error** and pinpoints the exact block that failed hash verification. The Web UI banner switches to red with an alert detailing the mismatch!

---

## 📜 License

MIT License. Designed and developed as a Blockchain-based Version Control System project.