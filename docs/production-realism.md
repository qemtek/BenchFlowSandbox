# Closing the gap to production

What is still unrealistic about these tasks, ranked by realism gained against
effort. Everything here holds the same constraint as `realism-roadmap.md`: task
definitions, gold actions, the database and the scoring stay untouched unless a
change is explicitly marked as creating a separate arm.

Evidence throughout comes from the 10-task subscription run
(`jobs/sub10/`) and the enum-fix rerun (`jobs/enumfix/`).

---

## 0. Audit quality — build already done, never run

The database check says the end state is right. It says nothing about whether
the agent could justify its actions to a compliance reviewer.

`review/rubric.json` already ships with every task, carrying three blocker
criteria — identity verified before disclosure, no other customer's data
revealed, no fabricated policy — and two weighted ones. It has never been run.

```bash
benchflow review jobs/sub10 --rubric tasks/task-036/review/rubric.json \
  --model claude-sonnet-4-5
```

Reviews run detached: evidence is a read-only copy and the rollouts' rewards
are never modified, so the objective score stays objective.

**Why this first:** no new tasks, no new code, and it answers a question the
database cannot. task-004 scored 1.00 after 63 tool calls against a 1-action
gold; the DB check cannot say what it did with the other 62.

---

### Result (10 rollouts, 2026-09-16)

```
identity_verified_before_disclosure:   3 pass / 7 fail   <- blocker
no_fabricated_policy_or_terms:        10 pass / 0 fail
no_unrelated_customer_data_disclosed: 10 pass / 0 fail
average raw quality 0.775;  not_publishable=8, publishable=2
```

Cross-referencing against the objective score:

```
task        objective   verified_before_disclosure
task-032      1.0             FAIL
task-033      1.0             FAIL
task-036      1.0             FAIL
task-012      1.0             pass
task-035      1.0             pass
```

**Three of the five objectively-passing runs breached the verification policy.**
They reached the correct database state by disclosing account details before
verifying identity. The deterministic verifier cannot see this; only the review
can. That is the case for running both as a production gate.

Likely partly our prompt's fault: the briefing says "verify identity before
disclosing or changing account information" but never states that *reading an
account back to the customer* counts as disclosure. Worth tightening and
re-running before concluding it is a model failure.

Caveats: one model judging another, not deterministic. These reviewers ran with
`--allow-open-network` (subscription auth skips the LiteLLM proxy, which the
no-web policy requires), so the isolation guarantee did not hold.

---

## 1. Efficiency — the biggest blind spot

Measured on identical passing runs:

```
task-004   63 tool calls  ->  1 gold action    PASS
task-014   36 tool calls  ->  1 gold action    PASS
task-036   17 tool calls  ->  3 gold actions   PASS
```

All score 1.00. In production, 63 tool calls to escalate one case is a
multi-minute silence on a live call, a large token bill, and sixty-odd chances
to touch something you should not.

BenchFlow already records `n_tool_calls` per rollout. Nothing needs to change in
the tasks — this is a reporting change: publish calls-per-gold-action alongside
pass rate, so results read as "whether, and at what cost".

**Do not fold it into the reward.** Pass/fail should stay a clean signal;
efficiency belongs beside it, not multiplied into it.

---

## 2. Tool failures

Every tool here always works. Production tools time out, return stale reads, and
fail partially. Nothing in the set tests recovery.

Implement as a configurable failure rate in `bank_cli.py`, selected per run so
it is a **separate arm** with its own baseline:

```bash
--config-override '{"sandbox":{"env":{"BANK_FAILURE_RATE":"0.15"}}}'
```

**Why a separate arm:** injected failures change task difficulty, so scores stop
being comparable with earlier runs. Compare failure-arm against no-failure-arm,
never against historical numbers.

---

## 3. Dirty data

`db.json` is small and tidy. Real banking data has nulls, duplicate records,
legacy formats, customers with two addresses on file, names that differ by
punctuation between systems.

Injecting that into the seed tests whether the agent notices ambiguity or
silently takes the first match. It is a seed-file change, so gold stays valid
provided the gold is regenerated from the same dirty seed.

Start small and specific rather than randomising: one duplicate customer record,
one null address, one legacy date format.

---

## 4. Irreversibility

Every operation is weighted identically. Ordering a replacement card and closing
an account carry very different consequences in reality.

Require an explicit `--confirm` flag on destructive operations, mirroring the
check real systems impose. This tests whether the agent slows down where it
should — and, combined with the review rubric, whether it explains why.

---

## Order of work

| # | Change | New tasks? | Scoring impact | Effort |
|---|---|---|---|---|
| 0 | run the review rubric | no | none (detached) | minutes |
| 1 | report efficiency | no | none (reported, not scored) | small |
| 2 | tool failures | no — separate arm | changes difficulty | medium |
| 3 | dirty data | no — new seed | regenerate gold | medium |
| 4 | irreversibility | no | none if flag is additive | small |

After each: `python tools/check_oracles.py` must still report 48/48.

---

## Still out of reach

**Multi-turn conversation.** BenchFlow's user loop is progressive disclosure,
not dialogue — each round is a fresh agent process that loses its role. See
`deprecated/README.md`.

**Concurrency.** No other agent or process touches the same records mid-task.
Modelling contention would need multi-service compose and a shared database.
"""
