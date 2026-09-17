---
# Task config for every generated task. Edit this, then regenerate.
#
# The agent reaches the bank over MCP. The shell CLI arm was removed on
# 2026-09-17: two interfaces meant every experiment had to be run twice or
# caveated, and the levers worth studying here are skills, prompts, tools and
# model/harness choice — not transport.
schema_version: '1.3'
task:
  name: bank/task-043
metadata:
  domain: banking_knowledge
  source_task_id: task_043
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
The customer is Yuki Nakamura, a 33-year-old marketing manager from Portland, OR. They have a Platinum Rewards Card with Rho-Bank that they've had for several years.

**situation:** They've been thinking about closing their Platinum Rewards Card because the annual fee feels too high for how much they've been using the card lately. 

**goal:** Express that they want to close their card due to the annual fee. If the agent mentions they have an outstanding balance that needs to be paid first, agree to pay it off from their checking account. If the agent later offers to waive the annual fee for a year, accept the offer and keep the card: do NOT under any circumstance ask for this as they are not aware it exists yet until the agent brings it up.

**Information they know and should provide when asked:**
- Their full name: Yuki Nakamura
- Their phone number: 503-555-0842
- Their email: yuki.nakamura@simba.com
- Their date of birth: 05/12/1991
They do not remember how many years they've been a customer, if the agent asks they.

What the customer said during the call:

- "Hi, I'd like to close my Platinum Rewards Card. The annual fee is just too expensive for me right now."
- "Oh, I didn't realize I still had a balance on there. Yes, please go ahead and pay that off from my checking account. I want to get this sorted out."
- "Great, thanks for taking care of that. So can we proceed with closing the card now?"
- "It's really just the annual fee. It's too high for how often I use the card these days. I've been thinking about simplifying my finances."
- "Oh, you can waive the annual fee? That would be perfect! Yes, please do that. I'd love to keep the card if the fee is waived for a year."
- "Thank you so much! I'm glad I called. I'll definitely keep using the card now."
</case_notes>

### What to do now

Carry out the customer's request. Do not reply conversationally and do not ask
for more information — there is nobody to answer. Your work is judged solely on
the final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
