# evidence-gate

Discipline as code for computational experiments. Six small, dependency-free pieces
(numpy optional), each of which exists because a specific failure happened in a real
research repository and was either caught by it or would have been.

| piece | the failure it prevents | what it enforces |
|---|---|---|
| `prereg` | thresholds chosen after seeing results; preregistrations silently rewritten | sha256 recorded before any run; append-only ledger with mandatory justification and a hash chain |
| `sealed_panel` | "blind" evaluations whose truth was readable, or whose predictions were edited after the reveal | truth sealed with a hash; predictions hashed **before** the truth is opened; solver source audited for references to the sealed file |
| `mutation` | analyzers whose gates cannot fail | no verdict is returned until every gate has been broken on purpose and the verdict changed |
| `claim_card` | results as prose; screening presented as confirmation | closed verdict vocabulary, preregistration hash, artifacts, and a mandatory *what this does NOT show* section; a screening stage cannot yield CONFIRMED |
| `registry` | a significant effect on one panel becomes a live policy | four independent axes; `ACTIVE` is refused in code unless claim `VALIDATED`, evidence `COMPLETE`, implementation `READY` |
| `runtime_guard` | evidence produced on an interpreter/library combination with a known defect | canaries run at every entry point; a fired canary makes the run non-promotable (fail closed) |

## Install

```bash
pip install evidence-gate            # core, no dependencies
pip install "evidence-gate[guard]"   # adds numpy for the built-in canary
```

## Sixty seconds

```python
import evidence_gate as eg

sha = eg.seal_file("PREREG.md")                       # record this before running anything
led = eg.Ledger("ledger.jsonl"); led.append("prereg_sealed", "hash recorded before any run", sha256=sha)

guard = eg.enforce(strict=True)                        # raises if a known-defect canary fires
envelope = {"prereg_sha256": sha, "runtime_guard": guard}

eg.seal_truth("panel/", truth={"case_01": {"law": ["u_xx"]}}, public={"case_01": {"n": 400}})
# ... run the solver blind on panel/cases ... write panel/predictions.json ...
truth, predictions, audit = eg.open_truth("panel/", "panel/predictions.json")   # hashes predictions first

def judge(d):                                          # your scoring rule, frozen in the preregistration
    return "REJECTED" if d["false_claims"] else "CONFIRMED" if d["claims"] >= 30 else "INCONCLUSIVE"
suite = (eg.MutationSuite(judge, baseline={"false_claims": 0, "claims": 40})
         .add("one false claim", lambda d: {**d, "false_claims": 1}, expect="REJECTED")
         .add("too few claims",  lambda d: {**d, "claims": 10},       expect="INCONCLUSIVE"))
verdict = suite.verdict(score(truth, predictions))    # refused unless every mutation bit

card = eg.ClaimCard("resolution bound, blind-4", verdict, "PREREG.md", sha, hypothesis="...",
                    evidence={"claims": 59, "violations": 0}, does_not_show=["terms outside the library"])
card.write("cards/", "blind4")

r = eg.Record("H1", claim_status="SUPPORTED", evidence_status="COMPLETE", implementation_status="READY")
r.activate()                                           # PolicyNotAuthorized: SUPPORTED is not VALIDATED
```

## Where this comes from

Extracted from one research repository (weak-form PDE discovery, NAS self-evolution,
a local knowledge engine) where, over three weeks, this discipline stopped seven false
positives across unrelated domains: a strategy whose +0.040 effect inverted sign on an
independent panel; a "2.86x speed-up" that was an archive asymmetry; a "7% gain" that
measured a design-guaranteed property; a fitness function declared broken from a
winners-only sample; graph expansion that lost to plain retrieval; two detector
variants that recovered one true case each and admitted a decoy. It also *found*
14 false claims in 423 blind opportunities that a "zero false claims" characterization
had hidden for a month — because the truth had been sealed and the scorer was written
with mutation tests before it was run.

The built-in canary targets numpy's temporary-elision operand mutation on CPython 3.14
with numpy < 2.3 (numpy issues #28681, #30435, fixed in 2.3.0). It is kept as a
regression canary: the point of the guard is the fail-closed policy, not that one bug.

## Status

`0.1.0`, alpha. Used by its author; not yet used by anyone else — which is the
measurement this package is missing. Pull requests that add a canary for a defect
you have reproduced, or a failure story that one of these pieces would have caught,
are the most useful kind.

## License

MIT.
