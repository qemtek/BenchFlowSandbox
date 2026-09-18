#!/usr/bin/env python3
"""Evidence for 09-overfitting.md.

Two ways of tuning a configuration against a fixed set of tasks, where every
change tried is in truth worth nothing. Each section is seeded separately, so
changing one does not shift the figures in another.

    python docs/learnings/scripts/overfitting_simulation.py
"""

import random
import statistics

TASKS = 48      # tasks in the set being tuned against
QUALITY = 0.50  # the configuration's true pass rate, unchanged by every variant
CHURN = 0.10    # share of tasks a proposed change moves
RUNS = 4000     # simulated tuning sessions per row


def fresh_score(rng: random.Random) -> float:
    """Pass rate on tasks the configuration was never tuned against."""
    return rng.binomialvariate(TASKS, QUALITY) / TASKS


def sequential(rng: random.Random, rounds: int,
               drift: float = 0.0) -> tuple[float, float]:
    """Propose a change, keep it if the set scores better, repeat.

    A change worth nothing still moves some tasks, because the agent is not
    deterministic. Keeping only the changes that scored better walks the
    configuration uphill on this set.

    `drift` is what each accepted change does to true quality. At 0 the tuning
    is harmless everywhere but the set. Below 0 it models a change that fits
    these tasks by specialising, which costs performance on everything else.
    """
    quality = QUALITY
    outcomes = [rng.random() < quality for _ in range(TASKS)]
    for _ in range(rounds):
        proposal = [
            (rng.random() < quality) if rng.random() < CHURN else keep
            for keep in outcomes
        ]
        if sum(proposal) > sum(outcomes):
            outcomes = proposal
            quality = max(0.0, quality + drift)
    return sum(outcomes) / TASKS, rng.binomialvariate(TASKS, quality) / TASKS


def best_of(rng: random.Random, variants: int) -> tuple[float, float]:
    """Try several changes at once and keep the one that scored highest."""
    best = None
    for _ in range(variants):
        score = rng.binomialvariate(TASKS, QUALITY) / TASKS
        if best is None or score > best:
            best = score
    return best, fresh_score(rng)


def set_size_report(seed: int) -> None:
    """A larger set to tune against slows the climb without stopping it."""
    global TASKS
    print("\nC. Twenty rounds of tuning, against sets of different sizes")
    original = TASKS
    for size in (48, 192, 768):
        TASKS = size
        rng = random.Random(seed + size)
        tuned = [sequential(rng, 20)[0] for _ in range(RUNS)]
        gain = (statistics.mean(tuned) - QUALITY) * 100
        print(f"   {size:4d} tasks tuned against   apparent gain {gain:+5.1f}pp")
    TASKS = original


def drift_report(seed: int) -> None:
    """The same tuning, when fitting the set costs general performance."""
    print("\nD. Tuning that specialises: each kept change costs 1 point "
          "of true quality")
    for rounds in (0, 5, 10, 20, 50):
        rng = random.Random(seed + rounds)
        tuned, fresh = zip(*(sequential(rng, rounds, drift=-0.01)
                             for _ in range(RUNS)))
        on_set = statistics.mean(tuned) * 100
        on_fresh = statistics.mean(fresh) * 100
        print(f"   {rounds:2d}   tuned set {on_set:5.1f}%   "
              f"fresh tasks {on_fresh:5.1f}%   "
              f"gap {on_set - on_fresh:5.1f}pp")


def report(label: str, fn, counts, seed: int) -> None:
    print(f"\n{label}")
    baseline = QUALITY * 100
    for count in counts:
        rng = random.Random(seed + count)
        tuned, fresh = zip(*(fn(rng, count) for _ in range(RUNS)))
        on_set = statistics.mean(tuned) * 100
        on_fresh = statistics.mean(fresh) * 100
        print(f"   {count:2d}   tuned set {on_set:5.1f}%   "
              f"fresh tasks {on_fresh:5.1f}%   "
              f"apparent gain {on_set - baseline:+5.1f}pp")


if __name__ == "__main__":
    print(f"Every change tried is worth nothing: the true pass rate stays "
          f"{QUALITY:.0%} throughout.")
    report("A. Rounds of tuning, each improvement kept", sequential,
           (0, 5, 10, 20, 50), seed=91)
    report("B. Variants tried at once, the best one kept", best_of,
           (1, 5, 10, 20, 50), seed=97)
    set_size_report(seed=103)
    drift_report(seed=109)
