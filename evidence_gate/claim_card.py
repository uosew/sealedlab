"""A result is a claim card: closed verdict vocabulary, preregistration hash, artifacts,
and a mandatory 'does not show' section. Screening verdicts cannot promote."""
from __future__ import annotations
import json, time
from dataclasses import dataclass, field, asdict
from pathlib import Path

CONFIRMATORY = ("CONFIRMED", "REJECTED", "INCONCLUSIVE", "NOT_TESTABLE")
SCREENING = ("PROMISING", "NOT_PROMISING", "UNCLEAR")
VERDICTS = CONFIRMATORY + SCREENING


@dataclass
class ClaimCard:
    title: str
    verdict: str
    prereg_path: str
    prereg_sha256: str
    hypothesis: str
    evidence: dict = field(default_factory=dict)        # numbers, with their artifact paths
    artifacts: list[str] = field(default_factory=list)
    does_not_show: list[str] = field(default_factory=list)
    stage: str = "confirmatory"                         # or "screening"
    date: str = field(default_factory=lambda: time.strftime("%Y-%m-%d"))

    def __post_init__(self):
        if self.verdict not in VERDICTS:
            raise ValueError(f"verdict {self.verdict!r} not in {VERDICTS}")
        if self.stage == "screening" and self.verdict not in SCREENING:
            raise ValueError("a screening stage can only yield PROMISING / NOT_PROMISING / UNCLEAR")
        if self.stage == "confirmatory" and self.verdict not in CONFIRMATORY:
            raise ValueError("a confirmatory stage yields CONFIRMED / REJECTED / INCONCLUSIVE / NOT_TESTABLE")
        if not self.does_not_show:
            raise ValueError("a claim card must say what it does NOT show")
        if not self.prereg_sha256 or len(self.prereg_sha256) < 16:
            raise ValueError("a claim card must carry the preregistration hash")

    def promotes(self) -> bool:
        return self.stage == "confirmatory" and self.verdict == "CONFIRMED"

    def to_markdown(self) -> str:
        ev = "\n".join(f"| {k} | {v} |" for k, v in self.evidence.items())
        dns = "\n".join(f"- {x}" for x in self.does_not_show)
        arts = "\n".join(f"- `{a}`" for a in self.artifacts) or "- (none)"
        return (f"# Claim card — {self.title}\n\n**Date:** {self.date}  \n**Preregistration:** `{self.prereg_path}` sha256 `{self.prereg_sha256[:16]}…`  \n"
                f"**Stage:** {self.stage}\n\n## Verdict: **{self.verdict}**\n\n**Hypothesis.** {self.hypothesis}\n\n"
                f"| measure | value |\n|---|---|\n{ev}\n\n## Artifacts\n{arts}\n\n## What this does NOT show\n{dns}\n")

    def write(self, directory: str | Path, stem: str) -> tuple[Path, Path]:
        d = Path(directory); d.mkdir(parents=True, exist_ok=True)
        md = d / f"{stem}.md"; js = d / f"{stem}.json"
        md.write_text(self.to_markdown(), encoding="utf-8"); js.write_text(json.dumps(asdict(self), indent=1), encoding="utf-8")
        return md, js
