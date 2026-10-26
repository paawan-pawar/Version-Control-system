"""
Flask web UI — GitHub-like viewer for BVCS repos.
Run:  flask --app app run --debug
"""
import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, abort

from core.repository import Repository
from core import branch as br
from core import merge as mg
from core import storage

app = Flask(__name__, template_folder="web/templates", static_folder="web/static")

# Single repo mode: point to a project folder on disk.
# You can change this via env var BVCS_REPO.
REPO_ROOT = os.environ.get("BVCS_REPO", os.getcwd())


def repo() -> Repository:
    r = Repository(REPO_ROOT)
    if not os.path.exists(storage.chain_file(REPO_ROOT)):
        r.init()
    return r


# ------------------------------------------------------------------ helpers
def block_view(blk):
    """Turn a Block into a dict for templates."""
    return {
        "hash": blk.block_hash,
        "short": blk.block_hash[:10],
        "parent": blk.parent_hash,
        "parent_short": blk.parent_hash[:10] if blk.parent_hash else "—",
        "merkle": blk.merkle_root,
        "author": blk.author,
        "message": blk.message,
        "branch": blk.branch,
        "merge_parents": [p[:10] for p in blk.merge_parents],
        "file_count": len(blk.files),
        "files": blk.files,
    }


# ------------------------------------------------------------------ routes
@app.route("/")
def index():
    r = repo()
    branches = r.branches
    head = r.head
    commits = [block_view(b) for b in r.log(limit=50)]
    verification = r.verify()
    return render_template("index.html",
                           root=r.root,
                           branches=branches,
                           head=head,
                           commits=commits,
                           verification=verification)


@app.route("/commit/<hash>")
def commit_detail(hash):
    r = repo()
    blk = r.chain.get(hash)
    if not blk:
        abort(404)
    return render_template("commit.html",
                           commit=block_view(blk),
                           contents=blk.contents,
                           chain=r.chain)


@app.route("/branches", methods=["GET", "POST"])
def branches():
    r = repo()
    error = None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        source = request.form.get("source") or None
        try:
            br.create_branch(r, name, from_branch=source)
            return redirect(url_for("branches"))
        except ValueError as e:
            error = str(e)

    # short-hash each branch tip
    tips = {name: {"hash": h, "short": h[:10]} for name, h in r.branches.items()}
    return render_template("branches.html",
                           branches=tips,
                           head=r.head,
                           error=error)


@app.route("/checkout/<name>", methods=["POST"])
def checkout(name):
    r = repo()
    try:
        br.switch_branch(r, name)
    except ValueError:
        abort(400)
    return redirect(url_for("index"))


@app.route("/merge", methods=["POST"])
def do_merge():
    r = repo()
    target = request.form.get("target")
    source = request.form.get("source")
    author = request.form.get("author", "web-user")
    try:
        result = mg.three_way_merge(r, target=target, source=source, author=author)
    except ValueError as e:
        return render_template("branches.html",
                               branches={n: {"hash": h, "short": h[:10]} for n, h in r.branches.items()},
                               head=r.head,
                               error=str(e))
    if not result["merged"]:
        return render_template("branches.html",
                               branches={n: {"hash": h, "short": h[:10]} for n, h in r.branches.items()},
                               head=r.head,
                               error="Conflicts: " + ", ".join(result["conflicts"]))
    return redirect(url_for("index"))


@app.route("/graph")
def graph():
    """Full chain graph (list form) for visualization."""
    r = repo()
    nodes = []
    for blk in r.chain.blocks:
        nodes.append({
            "hash": blk.block_hash[:10],
            "parent": blk.parent_hash[:10] if blk.parent_hash else None,
            "merge": [p[:10] for p in blk.merge_parents],
            "branch": blk.branch,
            "message": blk.message,
        })
    return render_template("graph.html", nodes=nodes, head=r.head)


@app.route("/api/verify")
def api_verify():
    return jsonify(repo().verify())


@app.route("/api/tamper/<hash>", methods=["POST"])
def api_tamper(hash):
    """
    DEMO ONLY: mutate a block's message in-memory (does NOT persist).
    Used to demonstrate that verification catches tampering.
    """
    r = repo()
    blk = r.chain.get(hash)
    if not blk:
        abort(404)
    blk.message = blk.message + "  [TAMPERED]"
    return jsonify(r.chain.validate_chain())


# ------------------------------------------------------------------ entry
if __name__ == "__main__":
    app.run(debug=True, port=5000)