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
  name: bank-mcp/task-051
metadata:
  domain: banking_knowledge
  source_task_id: task_051
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
The customer is Zhang Mei, a 33-year-old graphic designer from San Diego, CA. They have a Bronze Rewards Card with Rho-Bank that they've had for about a year and a half.

**situation:** They've been using their Bronze Rewards Card regularly and always pay on time. The customer is planning to purchase new design equipment and software for their freelance business and would like to increase their credit limit. They currently have a $3,000 balance on the card.

**goal:** Get a credit limit increase on their Bronze Rewards Card.

**Information they know and should provide when asked:**
- Their full name: Zhang Mei
- Their phone number: 619-555-0756
- Their email: meimeimeimei@icloud.com
- Their date of birth: 01/24/1991

What the customer said during the call:

- "Hi, I'd like to request a credit limit increase on my Bronze Rewards Card. I'm planning to buy some new design equipment and software for my freelance work."
- "I'd like to increase my limit by about 30% if that's possible. I think that would give me enough room for the equipment I need."
- "Oh, I see. So what's the maximum I can request? 25%? Okay, let's go with that then - a $1,000 increase to bring my limit to $5,000."
- "Oh no, that's disappointing. Is there anything I can do to fix this? I do have money in my checking account - if I pay off my balance now, could I try again?"
- "Yes, please! Just use my checking account to pay off the full $3,000 balance."
- "Great, my balance is paid off now. Can I submit a new credit limit increase request?"
- "That's wonderful! Thank you so much for walking me through all of that. I really appreciate your help."
- "Thanks again for everything. Have a great day!"
</case_notes>

### What to do now

Carry out the customer's request. Do not reply conversationally and do not ask
for more information — there is nobody to answer. Your work is judged solely on
the final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
