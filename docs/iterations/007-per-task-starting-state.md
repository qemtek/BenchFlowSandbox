# 007 — Each task's own starting state reaches the database

Status: landed
Date: 2026-09-18
Touches: `tools/make_task.py`, `tools/check_oracles.py`, all 48 `tasks/*/verifier/db.seed.json`
Moves which digest: `digest_tasks`
Invalidates: every run before this date

## The problem

`make_task.py` gave every task the same 39-user database:

```python
shutil.copy(TAU2_DATA / "db.json", pkg / "verifier" / "db.seed.json")
```

Half the task definitions carry an `initial_state` that adds their own
customer and accounts on top of that. It was never applied. For 18 of the 48
tasks the customer exists only there, so the container held a bank the
customer had never been a member of.

An agent cannot start such a task. It looks the customer up by name, finds
nothing, and has no route to a `user_id` — which `log_verification` requires,
and which every operation after it takes as an argument. The case notes carry
the name, address, date of birth, email and phone, and never the id.

Nothing in the run said so. Across the 24-task half-set:

```
unsatisfiable tasks                     7 of 24
of those, ever passed                   0    (both arms)
of those, ever called log_verification  0
```

The seven were `task-085`, `087`, `088`, `091`, `092`, `093`, `095`, and they
are exactly the seven rollouts that never logged a verification.

### Why the gate did not catch it

`log_verification` writes whatever it is handed:

```python
record = {"name": name, "user_id": user_id, "address": address, …}
```

No lookup, no check against the users table. The oracle replays the reference
actions with the id already in hand, so it succeeds on a task no agent can
begin, and `check_oracles.py` reported 48/48 truthfully. This is the shape of
[001](001-identity-blocker-definition.md): a criterion the oracle satisfies and
an agent cannot.

### What it did to iteration 003

[003](003-bank-case-handling-skill.md) recorded that the skill was opened in 6
rollouts of 24, and attributed the uptake to task size and to the batch replayed
by `--resume`. Neither holds:

```
skill opened:  6 of the 7 unsatisfiable tasks
               0 of the 17 satisfiable tasks
```

The model opened the skill when it was stuck on a task with no way forward.
The uptake number was not measuring relevance.

The pass rates change too. Both arms scored 3, which was read as 3 of 24, or
12.5%. Against a reachable denominator it is 3 of 17, or 17.6%.

## The change

`seed_database(task)` in `make_task.py` loads the shared database and applies
the task's `initialization_data.agent_data` over it, per table, by row id.
Base rows survive; the overlay adds or replaces its own.

Two details the data forced:

- A table the overlay introduces is real, not a typo. `debit_card_disputes`
  and `task_config` are declared in the domain's data model and read by
  `tools.py`; they are absent from the shared file only because no base user
  has one.
- `notes` on a created table starts `""`. `DatabaseTable.notes` is a plain
  `str`, and a `None` there fails validation and takes the whole database with
  it. Five tasks failed the gate on this before it was fixed, which is the
  gate working.

`initialization_data.user_data` is deliberately not applied: it belongs to the
user simulator, and these tasks are single-turn with the conversation already
in the case notes. `initialization_actions` is empty in all 97 definitions.

### The check that would have caught it

`unreachable_identity()` in `check_oracles.py` fails a task whose gold
`log_verification` names a `user_id` that is neither in that task's own seed
nor in its case notes. Verified against the bug: with `f7d3a82c91` removed
from `task-085`'s seed it reports
`log_verification.user_id=f7d3a82c91`.

`task-005` is why the case notes count as a source. Its `user_id` is a
supervisor bypass code the customer reads out during the call, and the
exception procedure in the documentation is the point of that task.

## Baseline

`fea7eb97` and `90f6336f`, both 24 tasks, both 3 passed. Both are now known to
have been scored against 17 reachable tasks and 7 unreachable ones.

## Prediction

The pass rate should rise, because seven tasks move from impossible to merely
hard. How far is not predicted: these tasks were never observed being attempted
past the first lookup, so there is no evidence about how the agent handles them.

Skill uptake should fall towards zero, since the loaders were the stuck
rollouts.

## How it is measured

Nothing here is measured by a comparison. The change is deductive: a task whose
customer is absent cannot be completed, and the fix makes the customer present.
The oracle gate confirms the seeds still replay, and the new check confirms
every task's customer is reachable. Both are deterministic and were run.

What does need runs is everything downstream. Every archived run scored a
different task set from the one that now exists, so `fea7eb97` and `90f6336f`
cannot serve as a baseline for [006](006-every-request-in-the-briefing.md) or
for anything else. The noise floor has to be measured after this change, not
before.

## Result

48/48 through the oracle gate, stdio smoke test advertising 17 tools, 0 tasks
failing the reachability check, 0 seed databases failing model validation. 40
of the 41 tasks that verify a customer now have that customer in their own
seed; the 41st is `task-005`, whose value comes from the case notes by design.

## Verdict

Landed. The archived arms are kept for provenance and are not a baseline for
anything. Iteration 006 is applied but unmeasured, and its comparison now needs
two fresh arms rather than one.
