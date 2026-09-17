#!/usr/bin/env python3
"""Evidence for 02-paired-comparison.md. Not part of the rig.

Shows what pairing does and does not remove, by isolating the two sources of
variation separately. Seeded, so the numbers in the page reproduce.

    python docs/learnings/pairing_simulation.py
"""

import random
import statistics

N = 48        # tasks per arm, matching the live set
RUNS = 4000   # simulated experiments
POP = 2000    # population of tasks the 48 are drawn from


def task_sampling() -> None:
    """Variation from WHICH tasks you drew. Pairing removes most of it."""
    random.seed(5)
    # Each task is near-deterministic: a configuration either solves it or not.
    base = [random.random() < 0.55 for _ in range(POP)]
    treat = [s or (random.random() < 0.18) for s in base]   # fixes 18% of failures
    true_lift = (sum(treat) - sum(base)) / POP

    same, different = [], []
    for _ in range(RUNS):
        idx = [random.randrange(POP) for _ in range(N)]
        same.append(sum(treat[i] for i in idx) / N
                    - sum(base[i] for i in idx) / N)
        other = [random.randrange(POP) for _ in range(N)]
        different.append(sum(treat[i] for i in other) / N
                         - sum(base[i] for i in idx) / N)

    se_same, se_diff = statistics.stdev(same), statistics.stdev(different)
    print("A. Variation from which tasks you drew")
    print(f"   true lift                    {true_lift * 100:+.1f}pp")
    print(f"   same 48 tasks   (paired)     SE {se_same * 100:5.2f}pp   "
          f"detects {2.8 * se_same * 100:.0f}pp")
    print(f"   a different 48  (unpaired)   SE {se_diff * 100:5.2f}pp   "
          f"detects {2.8 * se_diff * 100:.0f}pp")
    print(f"   reduction from pairing       {(1 - se_same / se_diff) * 100:.0f}%")


def agent_stochasticity() -> None:
    """Variation from the agent itself. Pairing removes none of it.

    Here the task set is fixed and only the agent varies. Its randomness is
    independent between arms, so there is nothing shared to cancel.
    """
    random.seed(5)
    difficulty = [random.betavariate(0.25, 0.25) for _ in range(N)]
    deltas = []
    for _ in range(RUNS):
        base = [random.random() < d for d in difficulty]
        treat = [random.random() < min(1.0, d + 0.08) for d in difficulty]
        deltas.append(sum(t - b for t, b in zip(treat, base)) / N)
    print("\nB. Variation from the agent, on a fixed task set")
    print(f"   paired SE                    "
          f"{statistics.stdev(deltas) * 100:5.2f}pp")
    print("   pairing cannot reduce this — the two arms' randomness is")
    print("   independent, so there is nothing common to subtract out.")


if __name__ == "__main__":
    task_sampling()
    agent_stochasticity()
