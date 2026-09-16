# Deprecated: multi-turn conversational tasks

BenchFlow's user loop is **progressive disclosure, not conversation**. Each round
is a fresh agent process (`connect_as` / `disconnect` per round in
`rollout/_user_loop.py`) that sees only the single string `user.run()` returns.
Workspace and database persist across rounds; the agent's identity, instructions
and conversation memory do not.

We built and ran a multi-turn variant of task_036. The loop worked — three
rounds fired, and withheld facts were released when the agent asked for them —
but the agent lost its role after round 0 and replied:

> I'm OpenCode, a coding assistant... It sounds like you might be trying to
> contact customer support about a credit card.

Rounds 1 and 2 made zero tool calls. Final reward 0.0.

`agent.prompt_prefix` does not fix it: it is applied once to
`self._resolved_prompts` (`rollout/__init__.py:997`), and the user loop bypasses
those entirely (`_user_loop.py:370`). Making this work means authoring each
round's prompt through a `BaseUser` subclass in the SDK, giving up
`benchflow eval run`.

Full analysis: `docs/realism-roadmap.md`, "Multi-turn findings".

These files are kept for reference. The live task set is single-turn only.
