"""The chain: list of blocks + validation + lookup helpers."""
from core.block import Block


class Blockchain:
    def __init__(self):
        self.blocks: list[Block] = []
        self._by_hash: dict[str, Block] = {}

    # ---------- add ----------
    def add_block(self, block: Block) -> bool:
        """Append a block if its parent exists in the chain (DAG-safe)."""
        if self.blocks:
            # Parent must exist somewhere in the chain (not just the tip)
            if block.parent_hash not in self._by_hash:
                raise ValueError(
                    f"Parent not found: block.parent={block.parent_hash[:8]} "
                    f"is not in the chain"
                )
        else:
            if block.parent_hash != "":
                raise ValueError("First block must have parent_hash == ''")

        block.seal()
        self.blocks.append(block)
        self._by_hash[block.block_hash] = block
        return True

    # ---------- lookups ----------
    def get(self, block_hash: str) -> Block | None:
        return self._by_hash.get(block_hash)

    def tip(self) -> Block | None:
        return self.blocks[-1] if self.blocks else None

    def ancestors(self, block_hash: str) -> list[Block]:
        """Return chain from given block back to genesis (inclusive)."""
        out = []
        cur = self.get(block_hash)
        while cur:
            out.append(cur)
            cur = self.get(cur.parent_hash) if cur.parent_hash else None
        return out

    def is_ancestor(self, ancestor_hash: str, descendant_hash: str) -> bool:
        cur = self.get(descendant_hash)
        while cur:
            if cur.block_hash == ancestor_hash:
                return True
            cur = self.get(cur.parent_hash) if cur.parent_hash else None
        return False

    def find_lca(self, hash_a: str, hash_b: str) -> Block | None:
        """Lowest common ancestor of two blocks."""
        ancestors_a = {b.block_hash: b for b in self.ancestors(hash_a)}
        cur = self.get(hash_b)
        while cur:
            if cur.block_hash in ancestors_a:
                return cur
            cur = self.get(cur.parent_hash) if cur.parent_hash else None
        return None

    # ---------- validation ----------
    def validate_chain(self) -> dict:
        """Walk entire chain checking integrity. Returns a report."""
        report = {"valid": True, "errors": [], "blocks_checked": 0}
        for i, blk in enumerate(self.blocks):
            report["blocks_checked"] += 1
            # 1. hash integrity
            if not blk.is_valid():
                report["valid"] = False
                report["errors"].append(
                    f"Block {i} ({blk.block_hash[:8]}): hash mismatch — content was tampered"
                )
            # 2. link integrity (DAG-safe: parent must exist in chain)
            if blk.parent_hash:
                if blk.parent_hash not in self._by_hash:
                    report["valid"] = False
                    report["errors"].append(
                        f"Block {i}: parent_hash {blk.parent_hash[:8]} not found in chain"
                    )
            elif i != 0:
                report["valid"] = False
                report["errors"].append(
                    f"Block {i}: empty parent_hash but not the genesis block"
                )
        return report

    # ---------- serialization ----------
    def to_dict(self) -> dict:
        return {"blocks": [b.to_dict() for b in self.blocks]}

    @staticmethod
    def from_dict(d: dict) -> "Blockchain":
        bc = Blockchain()
        for bd in d.get("blocks", []):
            blk = Block.from_dict(bd)
            bc.blocks.append(blk)
            bc._by_hash[blk.block_hash] = blk
        return bc