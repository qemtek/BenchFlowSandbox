# Learnings

Short pages on things worth understanding before believing a number this
project produces.
Each one exists because getting it wrong produced, or would have produced, a
confident conclusion that was not true.

Distinct from the guides in `docs/`: those tell you how to change something,
these tell you how to know whether the change did anything.

| | Page | The mistake it prevents |
|---|---|---|
| 01 | [How much a pass rate moves](01-standard-error.md) | reading a 6-point difference as an improvement |
| 02 | [Reducing variance](02-paired-comparison.md) | comparing overall pass rates, or expecting pairing to cancel agent noise |
| 03 | [Where the interval comes from](03-bootstrapping.md) | trusting a narrow interval, or calling "not shown" a proven absence of effect |

`pairing_simulation.py` and `interval_simulation.py` back the numbers in pages 02 and 03. They are documentation evidence,
not part of the evaluation code.
