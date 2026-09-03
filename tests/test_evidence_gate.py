import json, pytest
from pathlib import Path
import evidence_gate as eg


def test_prereg_seal_and_ledger(tmp_path):
    p = tmp_path / "prereg.md"; p.write_text("H1: x > 0\n")
    sha = eg.seal_file(p); assert eg.verify_file(p, sha)
    p.write_text("H1: x > 0 (edited after the run)\n"); assert not eg.verify_file(p, sha)
    led = eg.Ledger(tmp_path / "ledger.jsonl")
    with pytest.raises(ValueError): led.append("run", "")
    led.append("prereg_sealed", "hash recorded before any run", sha256=sha); led.append("run_done", "stage 1 executed")
    assert led.verify_chain() and len(led.rows()) == 2


def test_sealed_panel_hashes_predictions_before_opening(tmp_path):
    sha = eg.seal_truth(tmp_path, {"c1": {"label": 1}}, {"c1": {"n": 10}})
    with pytest.raises(eg.SealViolation): eg.open_truth(tmp_path, tmp_path / "missing.json")
    pred = tmp_path / "predictions.json"; pred.write_text(json.dumps({"c1": 1}))
    truth, p, audit = eg.open_truth(tmp_path, pred)
    assert truth["c1"]["label"] == 1 and audit["seal_intact"] and audit["truth_sha256"] == sha
    (tmp_path / "sealed" / "truth.json").write_text("{}")
    with pytest.raises(eg.SealViolation): eg.open_truth(tmp_path, pred)


def test_blindness_audit_finds_reference(tmp_path):
    src = tmp_path / "solver.py"; src.write_text("# reads only cases/\nimport json\ntruth = json.load(open('sealed/truth.json'))\n")
    hits = eg.blindness_audit([src]); assert len(hits) == 1 and "truth.json" in hits[0]


def test_mutation_suite_refuses_verdict_when_a_gate_is_inert():
    def judge(d): return "CONFIRMED" if d["false_claims"] == 0 and d["n"] >= 30 else "REJECTED" if d["false_claims"] > 0 else "INCONCLUSIVE"
    base = {"false_claims": 0, "n": 40}
    s = eg.MutationSuite(judge, base).add("one false claim", lambda d: {**d, "false_claims": 1}, expect="REJECTED")
    s.add("too few cases", lambda d: {**d, "n": 10}, expect="INCONCLUSIVE")
    assert s.verdict({"false_claims": 0, "n": 59}) == "CONFIRMED"
    s.add("inert mutation", lambda d: dict(d), expect_not="CONFIRMED")          # does not bite
    with pytest.raises(eg.GateDoesNotBite): s.verdict(base)
    with pytest.raises(eg.GateDoesNotBite): eg.MutationSuite(judge, base).verdict(base)   # no mutations at all


def test_claim_card_vocabulary_and_stage(tmp_path):
    kw = dict(prereg_path="p.md", prereg_sha256="a" * 64, hypothesis="h", does_not_show=["nothing beyond 10% noise"])
    with pytest.raises(ValueError): eg.ClaimCard("t", "MAYBE", **kw)
    with pytest.raises(ValueError): eg.ClaimCard("t", "CONFIRMED", stage="screening", **kw)
    with pytest.raises(ValueError): eg.ClaimCard("t", "CONFIRMED", prereg_path="p", prereg_sha256="a" * 64, hypothesis="h", does_not_show=[])
    c = eg.ClaimCard("t", "PROMISING", stage="screening", **kw); assert not c.promotes()
    md, js = eg.ClaimCard("t", "CONFIRMED", evidence={"claims": 59}, **kw).write(tmp_path, "card")
    assert "What this does NOT show" in md.read_text() and json.loads(js.read_text())["verdict"] == "CONFIRMED"


def test_registry_refuses_silent_promotion(tmp_path):
    r = eg.Record("H002", claim_status="SUPPORTED", evidence_status="COMPLETE", implementation_status="READY")
    with pytest.raises(eg.PolicyNotAuthorized): r.activate()
    assert r.policy_status == "INACTIVE"
    with pytest.raises(eg.PolicyNotAuthorized): eg.Record("H", claim_status="VALIDATED", policy_status="ACTIVE")
    ok = eg.Record("H1", "VALIDATED", "READY", "COMPLETE"); ok.activate()
    reg = eg.Registry(tmp_path); reg.save(ok); reg.save(r)
    assert [x.hypothesis_id for x in reg.active_policies()] == ["H1"]


def test_runtime_guard_fail_closed_policy():
    rep = eg.environment_report(canaries={"always": lambda: {"fired": True}})
    assert rep["status"] == "FAIL" and rep["fired"] == ["always"]
    with pytest.raises(RuntimeError): eg.enforce(canaries={"always": lambda: {"fired": True}})
    assert eg.evaluate_envelope({}) == "EVIDENCE_INCOMPLETE"
    assert eg.evaluate_envelope({"runtime_guard": rep}) == "RUN_INVALID_ENVIRONMENT"
    good = eg.environment_report(canaries={"quiet": lambda: {"fired": False}})
    assert eg.evaluate_envelope({"runtime_guard": good}) == "RUN_VALID"


def test_numpy_canary_runs_and_is_quiet_on_a_fixed_numpy():
    np = pytest.importorskip("numpy")
    r = eg.numpy_elision_canary()
    assert r["available"]
    major, minor = map(int, np.__version__.split(".")[:2])
    if (major, minor) >= (2, 3):
        assert r["mutation"] is False
