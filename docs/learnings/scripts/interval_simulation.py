#!/usr/bin/env python3
"""Evidence for 03-bootstrapping.md. Not part of the rig.

Simulates paired comparisons on a 48-task set so the page's claims can be
checked rather than taken on trust. Seeded, so the numbers in the page
reproduce.

    python docs/learnings/scripts/interval_simulation.py
"""

import random

N = 48          # tasks per arm, matching the live set
RUNS = 2000     # simulated experiments per scenario
BOOT = 400      # bootstrap resamples per experiment


def one_experiment(p_improve: float, p_regress: float) -> tuple[int, int]:
    """Return (tasks improved, tasks regressed) for one simulated comparison."""
    improved = sum(random.random() < p_improve for _ in range(N))
    regressed = sum(random.random() < p_regress for _ in range(N))
    return improved, regressed


def bootstrap_ci(improved: int, regressed: int) -> tuple[float, float]:
    """Percentile bootstrap over the paired per-task outcomes.

    Each task contributes +1 (improved), -1 (regressed) or 0 (agreed). Resample
    those 48 outcomes with replacement, recompute the delta, take the 2.5th and
    97.5th percentiles — the same shape as compare-lift's interval.
    """
    pool = [1] * improved + [-1] * regressed + [0] * (N - improved - regressed)
    deltas = sorted(
        sum(random.choice(pool) for _ in range(N)) / N for _ in range(BOOT)
    )
    return deltas[int(0.025 * BOOT)], deltas[int(0.975 * BOOT)]


def resample_count_demo() -> None:
    """What B buys you: steadier endpoints, not a narrower interval."""
    import statistics
    pool = [1] * 5 + [-1] * 1 + [0] * (N - 6)   # one fixed experiment

    def ci(b):
        d = sorted(sum(random.choice(pool) for _ in range(N)) / N
                   for _ in range(b))
        return d[int(0.025 * b)], d[int(0.975 * b)]

    print("\nC. Same data, different resample counts (10 repeats each)")
    for b in (100, 1000, 10000):
        los, his = zip(*(ci(b) for _ in range(10)))
        print(f"   B={b:<6} low {statistics.mean(los) * 100:+5.1f}pp "
              f"(varies by {(max(los) - min(los)) * 100:.1f}) "
              f"high {statistics.mean(his) * 100:+5.1f}pp "
              f"(varies by {(max(his) - min(his)) * 100:.1f})")


def main() -> None:
    random.seed(7)

    # A. Two arms that are genuinely identical. Tasks still flip both ways,
    #    because the agent is stochastic.
    false_alarms = 0
    for _ in range(RUNS):
        lo, hi = bootstrap_ci(*one_experiment(0.10, 0.10))
        if lo > 0 or hi < 0:
            false_alarms += 1
    rate = false_alarms / RUNS
    print("A. No real effect, 10% of tasks flipping each way")
    print(f"   interval excluded zero:      {rate:.0%} of runs (by design, ~5%)")
    print(f"   five arms, none better:      {1 - (1 - rate) ** 5:.0%} chance "
          "at least one looks real")

    # B. A genuine 10-point improvement.
    detected = 0
    for _ in range(RUNS):
        lo, _ = bootstrap_ci(*one_experiment(0.12, 0.02))
        if lo > 0:
            detected += 1
    print("\nB. Real 10-point gain (12% improve, 2% regress)")
    print(f"   detected:                    {detected / RUNS:.0%} of runs")
    print(f"   reported as 'not shown':     {1 - detected / RUNS:.0%} of runs")

    resample_count_demo()


if __name__ == "__main__":
    main()
