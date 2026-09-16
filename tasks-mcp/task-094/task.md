---
# Frontmatter variant: tools delivered over MCP instead of the shell CLI.
# Phase 3 of docs/realism-roadmap.md.
#
# Generate this arm with:
#   BANK_FRONTMATTER=frontmatter-mcp.yaml python tools/make_task.py <ids> --out tasks-mcp
#
# Same tasks, same scoring, one variable — so tasks/ vs tasks-mcp/ is a clean
# comparison of shell-JSON friction against structured tool calls.
schema_version: '1.3'
task:
  name: bank-mcp/task-094
metadata:
  domain: banking_knowledge
  source_task_id: task_094
  reward_basis: DB
  requestor: assistant
  tool_interface: mcp
agent:
  timeout_sec: 900.0
verifier:
  type: test-script
  timeout_sec: 300.0
sandbox:
  workdir: /app
  network_mode: public
  build_timeout_sec: 1800.0
  mcp_servers:
    - name: bank
      transport: stdio
      command: python
      args: ['/opt/bank/vendor/bank_mcp.py']
      env:
        BANK_DB: /data/db.json
---

## prompt

You are a customer service agent at Rho-Bank. Handle the customer enquiry below.

### Your tools

The bank's systems are available to you as tools. The core toolkit is already
loaded.

The bank runs many more operations than are loaded — use **bank_search** to find
the one you need by describing what you want to do (for example, "close
account"). Run a found operation with **bank_call_operation**, passing its name
and its arguments.

Finding an operation does not tell you how to use it correctly. Eligibility
rules, fees, and policy live in the bank's internal documentation at
`/data/documents`; search it (`rg`, `grep`) and follow the procedure it
describes.

### Bank policy

Verify the customer's identity before disclosing or changing account
information, and record it with `log_verification`. Never reveal information
belonging to any other customer. Only state fees, rates, or terms that appear
in the documentation.

If the documentation describes an exception procedure that applies to this
case, follow the documentation.

### Case notes

The call has already taken place. Everything the customer said is recorded
below, written from their point of view. Read it as a transcript summary, not
as a live conversation — **the customer has hung up and cannot answer further
questions.** Work only from what is here plus what you can look up.

<case_notes>
The customer is Wei-Ting Lin, a 38-year-old financial analyst living in San Francisco. The customer is frustrated because they believe their savings account interest is much lower than it should be. Based on their own research, the Gold Account base rate is 5.0% and the Green checking account gives a 1.0% boost. 

**Verification info:**
- Name: Wei-Ting Lin | Phone: 415-555-0863 | Email: weiting.lin@gmail.com
- DOB: 03/22/1987 | Address: 1628 Pacific Heights Blvd, Apt 8A, San Francisco, CA 94115

What the customer said during the call:

- "Hi, I need to dispute my interest payment. I have a Gold savings account with about $96,000 and I only received $408 in interest this month. The base rate is 5.0% and my checking account gives me a 1% boost, so I should be at 6.0% APY. That's $480 a month - you're shorting me $72! And if there are any other boosts that I'm missing, I want that addressed now too!"
- "I have a Gold savings account with around $96,000. I also have a Green checking account."
- "Yes, I have the Platinum Rewards Card, the Gold Rewards Card, and the EcoCard."
- "Yes, please apply that credit."
- "Yes, please do that. I don't want this happening again next month."
- "Thank you for correcting my assumptions and finding even more money owed to me. I really need to review the actual rate documentation!"
</case_notes>

### What to do now

Carry out the customer's request. Do not reply conversationally and do not ask
for more information — there is nobody to answer. Your work is judged solely on
the final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
