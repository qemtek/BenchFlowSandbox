#!/usr/bin/env python3
"""Evidence for 07-noise-and-bias.md.

Shows what more tasks do to noise and what they do to bias, by running the
same comparison at several task counts with and without a scoring fault. Each
section is seeded separately, so changing one does not shift the other.

    python docs/learnings/scripts/noise_simulation.py
"""

import random
import statistics

BOOT = 1000     # bootstrap resamples, matching compare-lift's default
RUNS = 4000     # simulated experiments per row

_VERDICTS: dict[tuple[int, int, int], bool] = {}


def comparison(rng: random.Random, tasks: int, fault: float) -> tuple[int, int]:
    """Two arms of equal quality, scored by a verifier that favours one of them.

    Every task is a coin flip in each arm, so the true difference is zero. On a
    `fault` share of tasks the scorer credits the treatment and faults the
    baseline whatever the arms did, which is a fixed error rather than a random
    one: it lands the same way in every run.
    """
    faulted = rng.binomialvariate(tasks, fault) if fault else 0
    rest = tasks - faulted
    # Of the rest, a quarter go to each arm and half come out the same way.
    wins = rng.binomialvariate(rest, 0.25)
    losses = rng.binomialvariate(rest - wins, 0.25 / 0.75) if rest - wins else 0
    return faulted + wins, losses


def interval(tasks: int, wins: int, losses: int) -> tuple[float, float]:
    """Percentile bootstrap over per-task outcomes, as compare-lift computes it."""
    rng = random.Random(1_000_000 * tasks + 1_000 * wins + losses)
    deltas = []
    for _ in range(BOOT):
        drawn_wins = rng.binomialvariate(tasks, wins / tasks)
        remaining = tasks - drawn_wins
        drawn_losses = (
            rng.binomialvariate(remaining, losses / (tasks - wins))
            if remaining and tasks > wins else 0
        )
        deltas.append((drawn_wins - drawn_losses) / tasks)
    deltas.sort()
    return deltas[int(0.025 * (BOOT - 1))], deltas[int(0.975 * (BOOT - 1))]


def declared(tasks: int, wins: int, losses: int) -> bool:
    key = (tasks, wins, losses)
    if key not in _VERDICTS:
        low, high = interval(tasks, wins, losses)
        _VERDICTS[key] = low > 0 or high < 0
    return _VERDICTS[key]


def sweep(label: str, fault: float, seed: int) -> None:
    print(f"\n{label}")
    for tasks in (48, 192, 768, 3072):
        rng = random.Random(seed + tasks)
        deltas, widths, hits = [], [], 0
        for _ in range(RUNS):
            wins, losses = comparison(rng, tasks, fault)
            deltas.append((wins - losses) / tasks)
            low, high = interval(tasks, wins, losses)
            widths.append(high - low)
            hits += declared(tasks, wins, losses)
        print(f"   {tasks:4d} tasks   "
              f"delta {statistics.mean(deltas) * 100:+5.1f}pp   "
              f"interval width {statistics.mean(widths) * 100:5.1f}pp   "
              f"difference declared {hits / RUNS:5.1%}")


if __name__ == "__main__":
    print("Two arms of genuinely equal quality, compared at four task counts.")
    sweep("A. Noise only: the scorer is working correctly", fault=0.0, seed=61)
    sweep("B. Noise plus bias: the scorer credits the treatment on 5% of tasks",
          fault=0.05, seed=67)
