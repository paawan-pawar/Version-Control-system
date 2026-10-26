"""Merkle tree: combines file hashes into a single tamper-proof root."""
from core.hashing import sha256_str


def merkle_root(hashes: list[str]) -> str:
    """
    Build a Merkle root from a list of leaf hashes.
    If odd count, the last hash is duplicated (classic Bitcoin-style).
    Empty list -> hash of empty string.
    """
    if not hashes:
        return sha256_str("")

    layer = [h for h in hashes]
    while len(layer) > 1:
        if len(layer) % 2 == 1:
            layer.append(layer[-1])  # duplicate last
        next_layer = []
        for i in range(0, len(layer), 2):
            combined = layer[i] + layer[i + 1]
            next_layer.append(sha256_str(combined))
        layer = next_layer
    return layer[0]


def merkle_proof(hashes: list[str], index: int) -> list[tuple[str, str]]:
    """
    Return a Merkle proof (list of (sibling_hash, side)) for the leaf at `index`.
    side is 'left' or 'right' depending on where the sibling sits.
    """
    if not hashes or index < 0 or index >= len(hashes):
        return []

    layer = list(hashes)
    proof = []
    idx = index

    while len(layer) > 1:
        if len(layer) % 2 == 1:
            layer.append(layer[-1])

        sibling_idx = idx ^ 1
        side = "left" if sibling_idx < idx else "right"
        proof.append((layer[sibling_idx], side))

        next_layer = []
        for i in range(0, len(layer), 2):
            next_layer.append(sha256_str(layer[i] + layer[i + 1]))
        layer = next_layer
        idx //= 2

    return proof


def verify_proof(leaf_hash: str, proof: list[tuple[str, str]], root: str) -> bool:
    """Verify a Merkle proof against a known root."""
    current = leaf_hash
    for sibling, side in proof:
        if side == "left":
            current = sha256_str(sibling + current)
        else:
            current = sha256_str(current + sibling)
    return current == root