---
# Task config for every generated task. Edit this, then regenerate.
#
# The agent reaches the bank over MCP. The shell CLI arm was removed on
# 2026-09-17: two interfaces meant every experiment had to be run twice or
# caveated, and the levers worth studying here are skills, prompts, tools and
# model/harness choice — not transport.
schema_version: '1.3'
task:
  name: bank/task-096
metadata:
  domain: banking_knowledge
  source_task_id: task_096
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

The bank runs many more operations than are loaded. Three steps reach them:

1. **bank_search** — find an operation by describing what you want to do, for
   example "close account". Returns names and one-line descriptions.
2. **bank_describe_operation** — read its full signature: what each argument
   means, which are required, and any defaults. Search gives you names, not
   signatures.
3. **bank_call_operation** — run it, passing the operation name and its
   arguments.

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
The customer is Naomi Ishikawa, a 52-year-old financial planner living in San Francisco. The customer is frustrated because the interest on BOTH of their savings accounts seems much lower than it should be. They have multiple checking accounts and credit cards with the bank, and they suspect they're not getting all the benefits they should.

**Verification info:**
- Name: Naomi Ishikawa | Phone: 415-555-8293 | Email: naomi.ishikawa@outlook.com
- DOB: 03/22/1973 | Address: 1847 Pacific Heights Boulevard, Apt 14C, San Francisco, CA 94115

What the customer said during the call:

- "Hi, I need help understanding the interest on my savings accounts. I have a Bronze savings with about $30,000 and a Gold Plus savings with around $60,000. I got $64 on the Bronze and only $328 on the Gold Plus last month. Both seem really low for accounts with these balances."
- "I have a Bronze savings account with around $30,000 and a Gold Plus savings with around $60,000. For checking, I have a Bluest Account, a Gold Years Account, and a Green Fee-Free Account."
- "Bluest has about $85,000, Gold Years has around $12,000, and Green Fee-Free has about $1,800."
- "Yes, I have four cards: the Platinum Rewards Card, the Gold Rewards Card, the Diamond Elite Card, and the Crypto-Cash Back Card."
- "Yes, please apply those credits to both accounts. I want the full amounts I'm entitled to."
- "Yes, please submit reports for both accounts. I need to make sure the system uses the right accounts going forward for both of my savings."
</case_notes>

### What to do now

Carry out the customer's request. Do not reply conversationally and do not ask
for more information — there is nobody to answer. Your work is judged solely on
the final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
