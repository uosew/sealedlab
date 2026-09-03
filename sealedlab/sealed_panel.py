"""Sealed ground truth for blind evaluation.

seal_truth():      write truth.json, truth.sha256 and a public manifest that carries no labels.
open_truth():      the ONLY sanctioned way to read the truth: it first hashes the predictions
                   file (so the predictions cannot be edited after seeing the truth), then
                   verifies the seal, then returns truth, predictions and an audit record.
blindness_audit(): grep the solver's source for references to the sealed file.

Lesson encoded: a panel whose truth and verdicts were committed together, without a
recorded hash, has a procedural seal only. Record the hash and commit the truth first.
"""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path


class SealViolation(RuntimeError):
    pass


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def seal_truth(out_dir: str | Path, truth: dict, public: dict) -> str:
    out = Path(out_dir); (out / "sealed").mkdir(parents=True, exist_ok=True)
    tp = out / "sealed" / "truth.json"
    tp.write_text(json.dumps(truth, indent=1, sort_keys=True, default=str), encoding="utf-8")
    sha = _sha(tp)
    (out / "sealed" / "truth.sha256").write_text(sha + "\n", encoding="utf-8")
    (out / "public_manifest.json").write_text(json.dumps(public, indent=1, sort_keys=True, default=str), encoding="utf-8")
    return sha


def open_truth(out_dir: str | Path, predictions_path: str | Path, expected_sha256: str | None = None) -> tuple[dict, dict, dict]:
    out = Path(out_dir); pp = Path(predictions_path); tp = out / "sealed" / "truth.json"
    if not pp.exists():
        raise SealViolation("predictions file does not exist: nothing to score, truth stays sealed")
    sha_pred = _sha(pp)                                     # hash predictions FIRST
    recorded = (out / "sealed" / "truth.sha256").read_text().strip()
    sha_now = _sha(tp)
    expected = expected_sha256 or recorded
    if sha_now != expected or sha_now != recorded:
        raise SealViolation(f"truth seal broken: now {sha_now[:12]}, recorded {recorded[:12]}, expected {expected[:12]}")
    audit = {"predictions_sha256": sha_pred, "truth_sha256": sha_now, "seal_intact": True}
    return json.loads(tp.read_text(encoding="utf-8")), json.loads(pp.read_text(encoding="utf-8")), audit


def blindness_audit(source_paths: list[str | Path], patterns=(r"sealed", r"truth\.json")) -> list[str]:
    """Lines in the solver sources that mention the sealed truth (comments excluded)."""
    hits = []
    for sp in source_paths:
        for i, line in enumerate(Path(sp).read_text(encoding="utf-8").splitlines(), 1):
            s = line.strip()
            if s.startswith("#") or s.startswith('"""') or s.startswith("'''"):
                continue
            if any(re.search(p, s) for p in patterns):
                hits.append(f"{Path(sp).name}:{i}: {s}")
    return hits
