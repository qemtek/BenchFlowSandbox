# Learnings

Short pages on things worth understanding before reading a number off this rig.
Each one exists because getting it wrong produced, or would have produced, a
confident conclusion that was not true.

Distinct from the guides in `docs/`: those tell you how to change something,
these tell you how to know whether the change did anything.

| | Page | The mistake it prevents |
|---|---|---|
| 01 | [Standard error](01-standard-error.md) | reading a 6-point difference as an improvement |
| 02 | [Paired comparison](02-paired-comparison.md) | comparing aggregate pass rates, or an arm against itself |
| 03 | [Bootstrapping](03-bootstrapping.md) | trusting a narrow interval, or calling "not shown" a proven absence of effect |

`interval_simulation.py` backs the numbers in page 03. It is documentation
evidence, not part of the rig — run it with
`python docs/learnings/interval_simulation.py`.
