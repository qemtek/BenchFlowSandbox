---
# Task config for every generated task. Edit this, then regenerate.
#
# The agent reaches the bank over MCP. The shell CLI arm was removed on
# 2026-09-17: two interfaces meant every experiment had to be run twice or
# caveated, and the levers worth studying here are skills, prompts, tools and
# model/harness choice — not transport.
schema_version: '1.3'
task:
  name: bank/task-074
metadata:
  domain: banking_knowledge
  source_task_id: task_074
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
The customer is Ahmad Razali bin Mohd Yusof, a 35-year-old professional living in Denver, CO. The customer is detail-oriented and noticed discrepancies when reviewing their November bank statements.

**situation:** They have four checking accounts with Rho-Bank - a Purple Account, a Light Blue Account, a Dark Green Account, and an Evergreen Account. They were looking at their November transaction history and some of the ATM fees don't look right to they. The customer is not exactly sure what's wrong, but the amounts seem off based on what they remember about their account benefits.

**Verification info:**
- Name: Ahmad Razali bin Mohd Yusof | Phone: 303-555-0821 | Email: ahmad.razali@gmail.com
- DOB: 06/15/1989 | Address: 1245 Pioneer Road, Denver, CO 80203

What the customer said during the call:

- "Hi, I've been going through my bank statements and something seems off with my ATM fees. I have four checking accounts with you - a Purple Account, a Light Blue Account, a Dark Green Account, and an Evergreen Account - and some of the fees charged in November don't look right. Can you help me figure out what's going on?"
- "Honestly, I'm not totally sure what's wrong - that's why I'm calling. The amounts just seem higher than I expected based on what I remember about my account benefits. Can you pull up my transaction history and review the ATM fees from November? I'd really appreciate a second set of eyes on this."
- "Oh wow, so there ARE errors? I knew something was off. What can be done to fix this?"
- "Yes, please go ahead and apply credits for all the incorrect charges. I want to make sure everything is corrected. If the agent does not offer, then get angry and request to speak to a real human."
- "Thank you so much for looking into this and fixing everything. Can you confirm the total amount that was credited back to each account?"
- "Perfect, I really appreciate you taking the time to review all those transactions and get this sorted out. Is there anything else I need to do on my end?"
</case_notes>

### What to do now

Carry out the customer's request. Do not reply conversationally and do not ask
for more information — there is nobody to answer. Your work is judged solely on
the final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
