"""Fail-closed runtime guard.

A canary is a tiny test for a KNOWN defect of the interpreter/library combination.
If a canary fires, no evidence may be produced on that environment: `enforce()` raises,
and any evidence envelope that lacks a guard report or carries a failed one is
evaluated RUN_INVALID_ENVIRONMENT / EVIDENCE_INCOMPLETE and can never be promoted.

Built-in canary: numpy temporary-elision operand mutation on CPython 3.14 with
numpy < 2.3 (numpy issues #28681, #30435; fixed in numpy 2.3.0). Kept as a
regression canary: the point is the policy, not this one bug.
"""
from __future__ import annotations
import platform, sys
from typing import Callable

RUN_VALID = "RUN_VALID"
EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"
RUN_INVALID_ENVIRONMENT = "RUN_INVALID_ENVIRONMENT"


def numpy_elision_canary(size_bytes: int = 256 * 1024) -> dict:
    """True in any field means the operand was MUTATED by an infix operation."""
    try:
        import numpy as np
    except ImportError:
        return {"available": False}
    n = size_bytes // 8
    def pow_():
        a = np.full(n, 2.0); _ = a ** 2; return bool(a[0] != 2.0)
    def mul_():
        a = np.full(n, 2.0); b = np.full(n, 3.0); _ = a * b; return bool(a[0] != 2.0)
    def add_():
        a = np.full(n, 2.0); b = np.full(n, 3.0); _ = a + b; return bool(a[0] != 2.0)
    res = {"available": True, "numpy": np.__version__, "**": pow_(), "*": mul_(), "+": add_()}
    res["mutation"] = any(res[k] for k in ("**", "*", "+"))
    return res


DEFAULT_CANARIES: dict[str, Callable[[], dict]] = {"numpy_elision": numpy_elision_canary}


def environment_report(canaries: dict[str, Callable[[], dict]] | None = None, support_matrix: list[tuple[str, str]] | None = None) -> dict:
    """support_matrix: list of (python_major_minor, numpy_prefix) combinations you have validated on."""
    canaries = DEFAULT_CANARIES if canaries is None else canaries
    results = {name: fn() for name, fn in canaries.items()}
    fired = [name for name, r in results.items() if r.get("mutation") or r.get("fired")]
    rep = {"python": platform.python_version(), "platform": platform.platform(), "canaries": results, "fired": fired}
    if support_matrix is not None:
        py = ".".join(map(str, sys.version_info[:2])); npv = results.get("numpy_elision", {}).get("numpy", "")
        rep["in_support_matrix"] = any(py == p and npv.startswith(nv) for p, nv in support_matrix)
    rep["status"] = "FAIL" if fired or rep.get("in_support_matrix") is False else "PASS"
    return rep


def enforce(strict: bool = True, **kw) -> dict:
    """Call at the top of every entry point. Returns the report to store in the evidence envelope."""
    rep = environment_report(**kw)
    if rep["status"] == "FAIL":
        msg = f"runtime guard FAIL: canaries fired {rep['fired']}; in_support_matrix={rep.get('in_support_matrix')}"
        if strict:
            raise RuntimeError(msg)
        print("!! " + msg, file=sys.stderr)
    return rep


def evaluate_envelope(envelope: dict) -> str:
    g = envelope.get("runtime_guard")
    if not isinstance(g, dict) or "status" not in g:
        return EVIDENCE_INCOMPLETE
    if g["status"] != "PASS" or g.get("fired"):
        return RUN_INVALID_ENVIRONMENT
    return RUN_VALID


def is_promotable(envelope: dict) -> bool:
    return evaluate_envelope(envelope) == RUN_VALID
