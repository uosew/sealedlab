"""Mutation tests for verdict logic: every gate must be broken on purpose and the
verdict must change. Until that is shown, the analyzer refuses to return a verdict.

    suite = MutationSuite(judge)                       # judge(data) -> verdict string
    suite.add("null_claimed", lambda d: {**d, ...}, expect_not="CONFIRMED")
    verdict = suite.verdict(real_data)                 # raises GateDoesNotBite if any mutation is inert
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable


class GateDoesNotBite(RuntimeError):
    pass


@dataclass
class Mutation:
    name: str
    mutate: Callable[[Any], Any]
    expect: str | None = None          # verdict the mutated data MUST produce
    expect_not: str | None = None      # verdict the mutated data must NOT produce


@dataclass
class MutationSuite:
    judge: Callable[[Any], str]
    baseline: Any = None               # synthetic data on which the mutations are applied
    mutations: list[Mutation] = field(default_factory=list)

    def add(self, name: str, mutate: Callable[[Any], Any], expect: str | None = None, expect_not: str | None = None) -> "MutationSuite":
        if expect is None and expect_not is None:
            raise ValueError("a mutation must declare expect or expect_not")
        self.mutations.append(Mutation(name, mutate, expect, expect_not)); return self

    def run(self) -> dict[str, bool]:
        """Returns {name: bites} without raising."""
        out = {}
        for m in self.mutations:
            v = self.judge(m.mutate(self.baseline))
            ok = (m.expect is None or v == m.expect) and (m.expect_not is None or v != m.expect_not)
            out[m.name] = bool(ok)
        return out

    def verdict(self, data: Any) -> str:
        """The only way to get a verdict: all mutations must bite first."""
        res = self.run()
        dead = [k for k, v in res.items() if not v]
        if dead or not self.mutations:
            raise GateDoesNotBite(f"verdict refused: gates that do not bite: {dead or 'no mutations registered'}")
        return self.judge(data)
