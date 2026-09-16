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
  name: bank-mcp/task-072
metadata:
  domain: banking_knowledge
  source_task_id: task_072
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
The customer is Liang Jinhai, a 23-year-old tech professional from Chicago, IL. The customer is detail-oriented and noticed some discrepancies when reviewing their bank statements.

**situation:** They have two checking accounts with Rho-Bank - a Bluest Account and a Light Green Account that they've had since they were a teenager. They were looking at their November transaction history and some of the ATM fees don't look right to they. The customer is not exactly sure what's wrong, but the amounts seem off based on what they remember about their account benefits.

**Verification info:**
- Name: Liang Jinhai | Phone: 312-555-0847 | Email: jinhai.liang@techventures.com
- DOB: 04/12/2002 | Address: 1420 Lake Shore Drive, Chicago, IL 60610

What the customer said during the call:

- "Hi, I've been looking at my recent bank statements and something seems off with my ATM fees. I have two checking accounts with you - a Bluest Account and a Light Green Account - and some of the fees charged in November don't look right. Can you help me figure out what's going on?"
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
