# Learnings

Short pages on things worth understanding before believing a number this
project produces. Each one exists because getting it wrong produced, or would
have produced, a confident conclusion that was not true.

Distinct from the guides in `docs/`: those tell you how to change something,
these tell you how to know whether the change did anything.

| | Page | The mistake it prevents |
|---|---|---|
| 01 | [How much a pass rate moves](01-standard-error.md) | reading a 6-point difference as an improvement |
| 02 | [Reducing variance](02-paired-comparison.md) | comparing overall pass rates, or expecting pairing to cancel agent noise |
| 03 | [Confidence intervals](03-bootstrapping.md) | trusting a narrow interval, or reading "we could not tell" as "there was no difference" |

`scripts/` holds the simulations behind the figures in pages 02 and 03. They
are documentation evidence rather than part of the evaluation code, and each is
seeded so the numbers in the pages reproduce.

```bash
python docs/learnings/scripts/pairing_simulation.py
python docs/learnings/scripts/interval_simulation.py
```

---

## Writing a page for this folder

Every rule below comes from a draft that failed on it.

### Before writing

**Check the claim by running it.** These pages make numerical claims, so
simulate before asserting. Two drafts of page 02 explained pairing wrongly, and
both read as plausible; a simulation caught them. Put the script in `scripts/`,
seed it, and quote its output.

**Say what the method cannot do.** Page 02 was only useful once it stated that
pairing does nothing for agent variance. A page that lists only benefits leaves
the reader unable to tell when the method will not help.

### Structure

**Name the subject in the first two sentences.** Not "this page is about the one
method that reduces it" — say which method, and define it there.

**One pass through the subject, then stop.** No conclusion in the middle, no
summary at the end. If a summary feels necessary, the page is too long.

**Headings label their contents.** "How much pairing buys", not "How much it
buys". Never a pronoun with no antecedent, never a thesis statement
("Width matters more than the midpoint").

### Sentences

**Show the arithmetic behind every number.** "The delta is 8.3 percentage
points" leaves the reader stuck. "The treatment passed four more of the 48
tasks, so 4/48, which is 8.3 percentage points" does not. If a number appears
without the operation that produced it, that is a defect.

**Define a term the first time it appears**, including in the title. A reader
may arrive at page 03 first.

**No project-internal references.** Not `task-004`, not "the rig". The reader
may know nothing about this repository.

### Cut on sight

- Short declaratives placed for rhythm: "It is not.", "Neither works alone.",
  "Same delta. Only the second is a result."
- Words doing emphasis instead of work: *actually*, *simply*,
  *counter-intuitively*.
- Instructions on how to read: "Read the width first", "Note that".
- Bold aphorisms: "A narrow interval around a wrong estimate is still wrong."
- Em-dashes beyond two or three per page.

