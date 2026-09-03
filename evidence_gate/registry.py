"""Four independent status axes per hypothesis, and one invariant enforced in code:
a policy cannot be ACTIVE unless claim=VALIDATED, evidence=COMPLETE, implementation=READY.
Fifty-three green tests are not a validation; a significant effect on one panel is not either."""
from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from pathlib import Path

CLAIM = ("HYPOTHESIS", "SUPPORTED", "VALIDATED", "REJECTED")
IMPLEMENTATION = ("NOT_IMPLEMENTED", "READY", "BROKEN")
EVIDENCE = ("NOT_TESTED", "UNDER_TEST", "COMPLETE", "INSUFFICIENT_PANEL")
POLICY = ("INACTIVE", "ACTIVE")


class PolicyNotAuthorized(RuntimeError):
    pass


@dataclass
class Record:
    hypothesis_id: str
    claim_status: str = "HYPOTHESIS"
    implementation_status: str = "NOT_IMPLEMENTED"
    evidence_status: str = "NOT_TESTED"
    policy_status: str = "INACTIVE"
    claim_card: str | None = None

    def __post_init__(self):
        for v, allowed, name in ((self.claim_status, CLAIM, "claim"), (self.implementation_status, IMPLEMENTATION, "implementation"),
                                 (self.evidence_status, EVIDENCE, "evidence"), (self.policy_status, POLICY, "policy")):
            if v not in allowed:
                raise ValueError(f"{name}_status {v!r} not in {allowed}")
        self._check()

    def _check(self):
        if self.policy_status != "ACTIVE":
            return
        missing = []
        if self.claim_status != "VALIDATED": missing.append(f"claim={self.claim_status} (needs VALIDATED)")
        if self.evidence_status != "COMPLETE": missing.append(f"evidence={self.evidence_status} (needs COMPLETE)")
        if self.implementation_status != "READY": missing.append(f"implementation={self.implementation_status} (needs READY)")
        if missing:
            raise PolicyNotAuthorized(f"{self.hypothesis_id}: policy cannot be ACTIVE: " + "; ".join(missing))

    def activate(self) -> None:
        prev = self.policy_status; self.policy_status = "ACTIVE"
        try:
            self._check()
        except PolicyNotAuthorized:
            self.policy_status = prev; raise


class Registry:
    def __init__(self, directory: str | Path):
        self.dir = Path(directory); self.dir.mkdir(parents=True, exist_ok=True)

    def save(self, r: Record) -> Path:
        r._check(); p = self.dir / f"{r.hypothesis_id}.json"
        p.write_text(json.dumps(asdict(r), indent=1), encoding="utf-8"); return p

    def load(self, hypothesis_id: str) -> Record:
        return Record(**json.loads((self.dir / f"{hypothesis_id}.json").read_text(encoding="utf-8")))

    def active_policies(self) -> list[Record]:
        out = []
        for p in sorted(self.dir.glob("*.json")):
            r = Record(**json.loads(p.read_text(encoding="utf-8")))
            if r.policy_status == "ACTIVE": out.append(r)
        return out
