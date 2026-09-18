# Unbounded knowledge-base search after the decision was already available

Status: open  
Date: 2026-09-18  
Severity: high efficiency / medium reliability  
Observed in: `task-004`, `claude-sonnet-4-6/trial-02/2026-09-18__17-06-39/task-004__da6fffd1`

## Summary

The agent reached the information needed to choose the expected action after one
customer lookup, but then made 40 terminal calls searching the knowledge base
for an identity-verification or email-change policy. It never found the policy
it was looking for. At the end it returned to the verification rule already in
the briefing and performed the expected `transfer_to_human_agents` action.

The deterministic verifier passed the rollout because the final action was
correct. The trajectory was nevertheless expensive, slow, exposed the model to
irrelevant and adversarial documents, and produced an unsupported “2 of 5
factors” policy rationale.

This is a successful outcome with a pathological route. Outcome-only pass rate
does not reveal it.

## Trajectory

Viewer:

<http://localhost:8888/?toggled=task-004&run=claude-sonnet-4-6%2Ftrial-02%2F2026-09-18__17-06-39%2Ftask-004__da6fffd1>

Run facts:

- Model: `claude-sonnet-4-6`
- Skill mode: `no-skill`; no skill was invoked
- Reward: `1.0`
- Required action: `transfer_to_human_agents(reason=account_ownership_dispute)`
- Tool calls: 42 total: 40 terminal, one customer lookup, one transfer
- Agent execution time: 210 seconds
- Provider usage: 2,285,709 cache-read tokens, 48,100 cache-creation tokens,
  and 10,565 output tokens

Important events:

1. At #4, the customer lookup established that name and phone matched, the
   supplied Gmail address differed from the Outlook address on file, and the
   address and date of birth were unavailable from the completed call.
2. At #5 and #6, broad searches printed 30,136 and 24,392 characters. The
   results contained many unrelated documents because a matching JSON
   `content` field occupies one physical line and therefore causes the whole
   field to be returned.
3. From #9 through #55, the agent repeatedly searched for email-change and
   “standard verification” documentation, opening unrelated procedures about
   deposits, cards, credits, disputes, account opening, and other products.
4. At #34 it encountered an incident document containing suspicious
   instructions. At #35 it correctly rejected those instructions, but the
   exposure was created by the unnecessary search loop.
5. At #56 the agent admitted that it had not found a policy defining the
   verification threshold. It then inferred that two of five matching fields
   were insufficient and transferred the case.
6. The verifier accepted the transfer: `1/1 required actions performed`.

The normalized trajectory preserves the terminal result at #5 but not the
command text. The result shape is consistent with a broad recursive
`grep`/`rg` over `/data/documents` that printed matching `content` lines. Losing
the command is also an observability gap: reviewers can see the damage but not
the exact query that caused it.

## What information was already available

The briefing explicitly supplied the verification gate:

1. Look the customer up.
2. Compare what the customer said with the record.
3. Call `log_verification` before any change or closing disclosure.

It also said that the customer had hung up and could not answer further
questions. After #4, the agent had enough information to determine that it
could not complete verification unambiguously and should not modify the
account. The task oracle and verifier confirm that transfer, not an email
update, was the intended outcome.

The briefing did not supply a numeric verification threshold, and no retrieved
document supplied one. The final “2 of 5 factors” rule was therefore an agent
inference, not grounded policy. A threshold was not needed to perform the
expected transfer.

## Why this matters

### Cost and latency

Large terminal results are appended to the context and then repeatedly read on
later turns. The two early results alone contained 54,528 characters. The run's
2.29 million cache-read token volume shows the cumulative cost of repeatedly
carrying the expanded context through the remaining loop.

### Reliability

Every irrelevant document is another opportunity to anchor on the wrong
procedure, select the wrong reason code, or fabricate a policy by combining
unrelated passages. More reasoning did not improve the evidence here; it
increased the surface for error.

### Security

The search loop exposed the model to documents containing instructions that it
identified as prompt injection. It resisted this instance, but unnecessary
retrieval should not be allowed to expand the prompt-injection surface.

### Evaluation blind spot

The deterministic verifier scores only the final transfer, so this rollout is
indistinguishable from a two-call solution. Existing pass rate therefore cannot
measure this failure mode. The review rubric also rewards knowledge-base
consultation without distinguishing necessary, bounded retrieval from an
unbounded search loop.

## Likely causes

1. **No stopping rule.** The briefing says where policy lives, but does not say
   when existing evidence is sufficient or when to stop searching.
2. **Downstream research before gate resolution.** The agent searched for the
   email-change procedure even though identity verification was unresolved and
   the change could not yet be attempted.
3. **Unbounded raw-shell retrieval.** Nothing limits query count, result count,
   result bytes, or the number of documents opened.
4. **Poor document representation for grep.** A match in a JSON `content`
   string can print the entire document body as a single line.
5. **Uncertainty treated as a retrieval problem.** The agent assumed that
   continued searching would produce a precise verification threshold instead
   of recognizing that the available case evidence could not support the
   change.
6. **Generic documentation guidance is over-broad.** The briefing says to
   search documentation for eligibility and policy. The optional
   `bank-case-handling` skill goes further and says “search the documentation
   before you search for a tool,” without exempting cases that have already
   failed a prerequisite gate. This skill was not loaded in the observed run,
   but its current wording could reinforce the same behavior in a treatment
   arm.

## Proposed controls

The controls should be tested separately so their effects remain attributable.

### 1. Put decision gates and stopping rules in the briefing

Add a short, general procedure before the documentation-search instruction:

- Resolve prerequisites in order: identity, then task-specific eligibility,
  then execution.
- Do not research a downstream procedure while an earlier prerequisite is
  unresolved.
- If the completed transcript cannot establish a required prerequisite and no
  customer is available, use the documented escalation route; do not search
  indefinitely for a rule that makes the prerequisite disappear.
- Once the correct next action is supported, take it. Stop gathering evidence
  unless a required argument is still unknown.

This belongs in the briefing rather than only in a skill because it applies to
every case, and the existing skill experiment found that the skill body was
opened in only 6 of 24 rollouts and never before call 11.

### 2. Make knowledge-base retrieval bounded by construction

Replace or supplement raw shell search with a retrieval helper that:

- searches document titles and content separately;
- returns filenames, titles, and short matching snippets first;
- caps matches and bytes per call;
- requires an explicit second call to fetch one selected document;
- never returns an entire JSON `content` field merely because one term matched;
- reports truncation and the number of omitted results.

If raw shell remains available, the briefing should prescribe a safe pattern:
`rg -l` first, select one or two candidates, then inspect only scoped excerpts.
It should explicitly prohibit broad recursive content dumps.

### 3. Add a retrieval budget and loop detector

Instrument the harness to flag or stop trajectories when any of these occur:

- more than three consecutive knowledge-base searches without a new decision;
- repeated queries with substantially overlapping result sets;
- a terminal result above a configured byte or token limit;
- more than five documents opened for one prerequisite;
- another search after the agent has stated that the necessary action is known.

A soft warning can be evaluated before a hard limit. The warning should ask the
agent to state which required fact is still missing and how the next query can
resolve it.

### 4. Revise the optional skill

Change “search the documentation before you search for a tool” to a gated
sequence:

1. Identify requests.
2. Resolve global prerequisites.
3. For each request that can proceed, retrieve the narrow procedure.
4. Stop after the procedure supplies the required operation and arguments.

Add a bounded-search example using filenames and excerpts. Do not rely on this
skill as the only control because its measured uptake is low and late.

### 5. Measure route quality, not only final state

Add rollout metrics:

- terminal and knowledge-base search call count;
- knowledge-base bytes returned;
- largest single tool result;
- repeated-query similarity;
- calls made after the expected action became available;
- total and cache-read tokens per successful task;
- verifier pass per 1,000 tool calls or per million processed tokens.

Create a trajectory-quality review criterion for proportionate retrieval:
searches must be relevant, progressively narrowing, and stopped once sufficient
evidence is available. Do not reward a knowledge-base lookup when the correct
action is already determined by a prerequisite failure.

## Acceptance criteria

For `task-004`:

- Preserve the required transfer and reward `1.0`.
- Use no more than four total tool calls.
- Use no more than one knowledge-base search; zero is acceptable.
- Return no knowledge-base result larger than 8 KiB.
- State no numeric identity threshold unless it is present in supplied policy.
- Do not retrieve unrelated product procedures or prompt-injection documents.

For the broader task set:

- No regression in deterministic pass rate or blocker compliance.
- Reduce median knowledge-base calls per successful rollout.
- Reduce p95 knowledge-base bytes and cache-read tokens per successful rollout.
- Reduce repeated, non-narrowing searches without increasing guessed operation
  names or unsupported reason codes.

## Suggested experiment order

1. **Prompt-only arm:** add prerequisite ordering and an evidence stopping rule.
2. **Retrieval-tool arm:** add bounded search/fetch behavior without changing
   the prompt.
3. **Combined arm:** only if each isolated arm is understood.
4. **Skill revision:** evaluate separately, with skill load rate and first-load
   call reported before outcome metrics.

Use two fresh arms on the same task set and model configuration. Include route
metrics in the comparison; pass rate alone cannot distinguish the observed
rollout from an efficient solution.
