#!/usr/bin/env python3
"""Evidence for 04-mcnemar.md.

Checks the page's claims about comparing two configurations on the same
pass/fail tasks, rather than leaving them to be taken on trust. Each section
is seeded separately, so changing one does not shift the figures in another.

    python docs/learnings/scripts/mcnemar_simulation.py
"""

import random
from math import comb

N = 48          # tasks, matching the live set
RUNS = 20000    # simulated experiments per scenario
BOOT = 1000     # bootstrap resamples, matching compare-lift's default


_BOOT_CACHE: dict[tuple[int, int], bool] = {}


def exact_p(wins: int, losses: int) -> float:
    """Two-sided exact p-value for `wins` heads out of `wins + losses` flips."""
    n = wins + losses
    if n == 0:
        return 1.0
    tail = sum(comb(n, i) for i in range(min(wins, losses) + 1))
    return min(1.0, 2 * tail / 2 ** n)


def bootstrap_excludes_zero(wins: int, losses: int) -> bool:
    """Percentile bootstrap over per-task outcomes, as compare-lift computes it.

    The verdict depends only on how many tasks each arm won, so it is cached:
    the same counts always get the same resampling seed and the same answer.
    """
    cached = _BOOT_CACHE.get((wins, losses))
    if cached is not None:
        return cached
    values = [1] * wins + [-1] * losses + [0] * (N - wins - losses)
    rng = random.Random(1000 * wins + losses)
    means = sorted(
        sum(values[rng.randrange(N)] for _ in range(N)) / N for _ in range(BOOT)
    )
    low = means[int(0.025 * (BOOT - 1))]
    high = means[int(0.975 * (BOOT - 1))]
    verdict = low > 0 or high < 0
    _BOOT_CACHE[(wins, losses)] = verdict
    return verdict


def p_value_table() -> None:
    print("A. Exact p-values by how the disagreements split")
    for wins, losses in ((4, 0), (5, 0), (6, 0), (5, 1), (7, 1),
                         (8, 1), (9, 2), (10, 2), (12, 4)):
        print(f"   {wins:2d} to {losses:<2d} "
              f"({wins + losses:2d} disagreements)   p = {exact_p(wins, losses):.3f}")


def floor_demo() -> None:
    print("\nB. Fewest disagreements that can reach p < 0.05, all one direction")
    for wins in range(1, 8):
        p = exact_p(wins, 0)
        mark = "  <- first below 0.05" if p < 0.05 and exact_p(wins - 1, 0) >= 0.05 else ""
        print(f"   {wins} to 0   p = {p:.3f}{mark}")


def agreement_demo() -> None:
    """How often the two methods reach the same verdict."""
    print("\nC. Verdicts compared, over simulated experiments")
    scenarios = (
        ("no real difference", 0.05, 0.05),
        ("real 4-point gain", 0.06, 0.02),
        ("real 10-point gain", 0.12, 0.02),
    )
    for label, p_improve, p_regress in scenarios:
        rng = random.Random(101)
        boot_hits = mcnemar_hits = mcnemar_only = 0
        for _ in range(RUNS):
            wins = sum(rng.random() < p_improve for _ in range(N))
            losses = sum(rng.random() < p_regress for _ in range(N))
            boot = bootstrap_excludes_zero(wins, losses)
            mcn = exact_p(wins, losses) < 0.05
            boot_hits += boot
            mcnemar_hits += mcn
            mcnemar_only += mcn and not boot
        print(f"   {label:<20} interval {boot_hits / RUNS:5.1%}   "
              f"McNemar {mcnemar_hits / RUNS:5.1%}   "
              f"McNemar without the interval {mcnemar_only / RUNS:5.1%}")


def degenerate_demo() -> None:
    """Page 03's failure case: almost no disagreements."""
    print("\nD. When only one or two tasks disagree")
    for wins in (1, 2):
        values = [1] * wins + [0] * (N - wins)
        rng = random.Random(23)
        means = sorted(
            sum(values[rng.randrange(N)] for _ in range(N)) / N for _ in range(BOOT)
        )
        low = means[int(0.025 * (BOOT - 1))] * 100
        high = means[int(0.975 * (BOOT - 1))] * 100
        print(f"   {wins} to 0   bootstrap {low:+.1f}pp to {high:+.1f}pp   "
              f"McNemar p = {exact_p(wins, 0):.3f}")


if __name__ == "__main__":
    p_value_table()
    floor_demo()
    agreement_demo()
    degenerate_demo()
