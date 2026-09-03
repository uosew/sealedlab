"""sealedlab — discipline as code for computational experiments.

Six small, independent pieces, each of which exists because a specific failure
happened in a real research repository and was caught (or not) by it:

- prereg:        hash a preregistration BEFORE any run; verify it before scoring.
- sealed_panel:  seal ground truth with a hash, hash predictions before opening it,
                 audit that the solver source never references the sealed file.
- mutation:      a verdict is not trusted until every gate has been broken on purpose
                 and the verdict changed. A gate that does not bite is not a gate.
- claim_card:    a result is a card with a Verdict from a closed vocabulary, the
                 preregistration hash, the artifacts, and a mandatory
                 'what this does NOT show' section.
- registry:      four independent status axes; a policy cannot be ACTIVE unless the
                 claim is VALIDATED, the evidence COMPLETE and the implementation READY.
- runtime_guard: run canaries for known interpreter/library defects and refuse to
                 produce evidence on an unverified environment (fail closed).
"""
from .prereg import seal_file, verify_file, Ledger
from .sealed_panel import seal_truth, open_truth, blindness_audit, SealViolation
from .mutation import MutationSuite, GateDoesNotBite
from .claim_card import ClaimCard, VERDICTS
from .registry import Record, Registry, PolicyNotAuthorized
from .runtime_guard import enforce, environment_report, evaluate_envelope, numpy_elision_canary

__version__ = "0.1.0"
__all__ = ["seal_file", "verify_file", "Ledger", "seal_truth", "open_truth", "blindness_audit",
           "SealViolation", "MutationSuite", "GateDoesNotBite", "ClaimCard", "VERDICTS", "Record",
           "Registry", "PolicyNotAuthorized", "enforce", "environment_report", "evaluate_envelope",
           "numpy_elision_canary"]
