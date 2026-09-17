#!/usr/bin/env python3
"""Evidence for 06-statistical-power.md.

Simulates paired comparisons with a known true effect, so the page can report
how often that effect is found rather than asserting it. Each section is seeded
separately, so changing one does not shift the figures in another.

    python docs/learnings/scripts/power_simulation.py
"""

import random
import statistics

BOOT = 1000     # bootstrap resamples, matching compare-lift's default
REGRESS = 0.02  # tasks the change breaks, held fixed across scenarios

_VERDICTS: dict[tuple[int, int, int], bool] = {}


def experiment(rng: random.Random, tasks: int, effect: float) -> tuple[int, int]:
    """One simulated comparison. Returns (tasks won, tasks lost) by the treatment."""
    losses = rng.binomialvariate(tasks, REGRESS)
    wins = rng.binomialvariate(tasks, effect + REGRESS)
    return wins, losses


def interval(tasks: int, wins: int, losses: int) -> tuple[float, float]:
    """Percentile bootstrap over per-task outcomes, as compare-lift computes it.

    A resample needs only the count of won and lost tasks it drew, so the counts
    are drawn directly rather than by picking tasks one at a time. The two draws
    share the same `tasks` slots, so the second is conditioned on the first.
    """
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


def found(tasks: int, wins: int, losses: int) -> bool:
    """Would this comparison be reported as a difference? Cached by its counts."""
    key = (tasks, wins, losses)
    if key not in _VERDICTS:
        low, high = interval(tasks, wins, losses)
        _VERDICTS[key] = low > 0 or high < 0
    return _VERDICTS[key]


def run(tasks: int, effect: float, runs: int, seed: int) -> dict[str, float]:
    rng = random.Random(seed)
    hits = wrong_sign = 0
    measured_when_found = []
    for _ in range(runs):
        wins, losses = experiment(rng, tasks, effect)
        delta = (wins - losses) / tasks
        if found(tasks, wins, losses):
            hits += 1
            measured_when_found.append(delta)
            wrong_sign += delta < 0
    return {
        "power": hits / runs,
        "measured": statistics.mean(measured_when_found) if measured_when_found else 0.0,
        "wrong_sign": wrong_sign / hits if hits else 0.0,
    }


def power_by_effect() -> None:
    print("A. Chance of finding the effect, 48 tasks")
    for effect in (0.02, 0.04, 0.06, 0.10, 0.15, 0.20, 0.30):
        r = run(48, effect, runs=20000, seed=31)
        print(f"   true gain {effect * 100:4.0f}pp    found {r['power']:5.1%}")


def power_by_tasks() -> None:
    print("\nB. Chance of finding a true 10-point gain, by task count")
    for tasks in (24, 48, 96, 192, 384):
        r = run(tasks, 0.10, runs=20000, seed=37)
        print(f"   {tasks:4d} tasks     found {r['power']:5.1%}")


def exaggeration() -> None:
    print("\nC. Size of the gain when it is found, 48 tasks")
    for effect in (0.06, 0.10, 0.20, 0.30):
        r = run(48, effect, runs=20000, seed=41)
        ratio = r["measured"] / effect
        print(f"   true gain {effect * 100:4.0f}pp   found {r['power']:5.1%}   "
              f"reported {r['measured'] * 100:5.1f}pp   "
              f"overstated by {ratio:.2f}x")


def wrong_direction() -> None:
    print("\nD. Findings pointing the wrong way, 48 tasks")
    for effect in (0.02, 0.04, 0.10):
        r = run(48, effect, runs=40000, seed=43)
        print(f"   true gain {effect * 100:4.0f}pp   found {r['power']:5.1%}   "
              f"of those, wrong direction {r['wrong_sign']:5.1%}")


if __name__ == "__main__":
    power_by_effect()
    power_by_tasks()
    exaggeration()
    wrong_direction()
