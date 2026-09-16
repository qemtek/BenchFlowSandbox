"""Which tools each experiment arm exposes to the agent.

This is the whole tool-selection mechanism. Add a named set, then select it for
a run with the BANK_TOOLSET environment variable:

    --config-override '{"sandbox":{"env":{"BANK_TOOLSET":"no_discovery"}}}'

`None` means every tool the domain defines. Otherwise give `exclude` (drop these
from the full set) or `include` (allow only these). Names are the ones printed
by `bank list`; see docs/tools.md for the full inventory with descriptions and
source locations.

The tool implementations live in the vendored tau2 domain — 14 directly callable
tools plus 44 discoverable ones the agent must find in the knowledge base. To
change what a tool DOES, edit it there (docs/tools.md gives the file and line)
and rebuild. To change which tools EXIST, edit this file.
"""

TOOLSETS = {
    # Everything: the baseline arm.
    "default": None,

    # Withhold the knowledge-base tool-discovery mechanism. The agent keeps the
    # ordinary banking tools but can no longer unlock the 44 specialised ones,
    # so this measures what discovery is worth.
    "no_discovery": {
        "exclude": {
            "unlock_discoverable_agent_tool",
            "call_discoverable_agent_tool",
            "list_discoverable_agent_tools",
            "give_discoverable_user_tool",
        }
    },

    # Read-only: no state changes possible. Every task should fail, which makes
    # this a useful sanity check that the verifier is actually discriminating
    # rather than passing things by accident.
    "read_only": {
        "include": {
            "get_current_time",
            "get_user_information_by_id",
            "get_user_information_by_name",
            "get_user_information_by_email",
            "get_credit_card_accounts_by_user",
            "get_credit_card_transactions_by_user",
            "get_referrals_by_user",
        }
    },
}


def allowed(name: str | None, every_tool: set[str]) -> set[str]:
    """Resolve a toolset name against the domain's full tool list."""
    spec = TOOLSETS.get(name or "default")
    if spec is None:
        return set(every_tool)
    if "include" in spec:
        return set(spec["include"]) & set(every_tool)
    return set(every_tool) - set(spec.get("exclude") or ())
