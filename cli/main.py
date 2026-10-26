"""
Command-line interface: python -m cli.main <command> ...

Usage examples:
    python -m cli.main init
    python -m cli.main add file.txt
    python -m cli.main commit -a "your name" -m "message"
    python -m cli.main log
    python -m cli.main verify
    python -m cli.main branch newfeature
    python -m cli.main checkout newfeature
    python -m cli.main merge main newfeature -a "your name"
"""
import argparse
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.repository import Repository
from core import branch as br
from core import merge as mg


def get_repo() -> Repository:
    return Repository(os.getcwd())


def cmd_init(args):
    repo = get_repo()
    g = repo.init(default_branch=args.branch)
    print(f"Initialized empty BVCS repository in {repo.root}/.bvcs")
    print(f"Genesis: {g.block_hash}")


def cmd_add(args):
    repo = get_repo()
    for f in args.files:
        repo.add(f)
        print(f"staged: {f}")


def cmd_commit(args):
    repo = get_repo()
    blk = repo.commit(author=args.author, message=args.message)
    print(f"[{blk.branch} {blk.block_hash[:10]}] {blk.message}")


def cmd_log(args):
    repo = get_repo()
    for blk in repo.log(limit=args.n):
        marker = "*" if blk.block_hash == repo.head.get("commit") else " "
        merge_info = f" (merge of {', '.join(p[:8] for p in blk.merge_parents)})" if blk.merge_parents else ""
        print(f"{marker} {blk.block_hash[:10]} [{blk.branch}] {blk.message}{merge_info}")
        print(f"    author={blk.author}  merkle={blk.merkle_root[:10]}")


def cmd_status(args):
    repo = get_repo()
    s = repo.status()
    print(f"On branch {s['branch']}  HEAD={s['head']}")
    print(f"Staged: {s['staged']}")
    print(f"Branches: {list(s['branches'].keys())}")


def cmd_verify(args):
    repo = get_repo()
    rep = repo.verify()
    print(f"Chain valid: {rep['valid']}  ({rep['blocks_checked']} blocks checked)")
    for err in rep["errors"]:
        print(f"  ✗ {err}")


def cmd_branch(args):
    repo = get_repo()
    try:
        h = br.create_branch(repo, args.name, from_branch=args.from_branch)
        print(f"Created branch '{args.name}' at {h[:10]}")
    except ValueError as e:
        print(f"error: {e}")


def cmd_checkout(args):
    repo = get_repo()
    try:
        head = br.switch_branch(repo, args.name)
        print(f"Switched to '{args.name}' ({head['commit'][:10]})")
    except ValueError as e:
        print(f"error: {e}")


def cmd_merge(args):
    repo = get_repo()
    result = mg.three_way_merge(repo, target=args.target, source=args.source, author=args.author)
    if result["merged"]:
        blk = result["commit"]
        print(f"Merged! [{blk.branch} {blk.block_hash[:10]}] {blk.message}")
    else:
        print("CONFLICTS in:")
        for c in result["conflicts"]:
            print(f"  ! {c}")


def build_parser():
    p = argparse.ArgumentParser(prog="bvcs", description="Blockchain version control")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init")
    p_init.add_argument("--branch", default="main")
    p_init.set_defaults(func=cmd_init)

    p_add = sub.add_parser("add")
    p_add.add_argument("files", nargs="+")
    p_add.set_defaults(func=cmd_add)

    p_commit = sub.add_parser("commit")
    p_commit.add_argument("-a", "--author", default="user")
    p_commit.add_argument("-m", "--message", required=True)
    p_commit.set_defaults(func=cmd_commit)

    p_log = sub.add_parser("log")
    p_log.add_argument("-n", type=int, default=20)
    p_log.set_defaults(func=cmd_log)

    p_status = sub.add_parser("status")
    p_status.set_defaults(func=cmd_status)

    p_verify = sub.add_parser("verify")
    p_verify.set_defaults(func=cmd_verify)

    p_branch = sub.add_parser("branch")
    p_branch.add_argument("name")
    p_branch.add_argument("--from", dest="from_branch", default=None)
    p_branch.set_defaults(func=cmd_branch)

    p_co = sub.add_parser("checkout")
    p_co.add_argument("name")
    p_co.set_defaults(func=cmd_checkout)

    p_merge = sub.add_parser("merge")
    p_merge.add_argument("target")
    p_merge.add_argument("source")
    p_merge.add_argument("-a", "--author", default="user")
    p_merge.set_defaults(func=cmd_merge)

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()