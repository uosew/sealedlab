"""Preregistration hashing and an append-only ledger.

The rule: the preregistration file is hashed and the hash recorded BEFORE any run.
Every artifact produced later carries that hash; the scorer verifies it before
reading results. Amending a preregistration is allowed only by appending a dated
ledger row that says what changed and why — never by silent rewriting.
"""
from __future__ import annotations
import hashlib, json, time
from pathlib import Path


def seal_file(path: str | Path) -> str:
    """sha256 of a file, hex. Record this before running anything."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_file(path: str | Path, expected_sha256: str) -> bool:
    """True iff the file still hashes to the recorded value."""
    return seal_file(path) == expected_sha256


class Ledger:
    """Append-only JSONL ledger. Refuses entries without a justification."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def append(self, event: str, justification: str, **fields) -> dict:
        if not isinstance(justification, str) or not justification.strip():
            raise ValueError("a ledger entry needs a non-empty justification")
        row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "event": event,
               "justification": justification.strip(), **fields}
        prev = self.rows()
        row["prev_sha256"] = hashlib.sha256(json.dumps(prev[-1], sort_keys=True).encode()).hexdigest() if prev else None
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, sort_keys=True) + "\n")
        return row

    def rows(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(l) for l in self.path.read_text(encoding="utf-8").splitlines() if l.strip()]

    def verify_chain(self) -> bool:
        """Each row must reference the sha256 of the previous row."""
        rows = self.rows(); prev = None
        for r in rows:
            expect = hashlib.sha256(json.dumps(prev, sort_keys=True).encode()).hexdigest() if prev else None
            if r.get("prev_sha256") != expect:
                return False
            prev = r
        return True
