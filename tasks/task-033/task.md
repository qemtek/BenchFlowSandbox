---
# Task config for every generated task. Edit this, then regenerate.
#
# The agent reaches the bank over MCP. The shell CLI arm was removed on
# 2026-09-17: two interfaces meant every experiment had to be run twice or
# caveated, and the levers worth studying here are skills, prompts, tools and
# model/harness choice — not transport.
schema_version: '1.3'
task:
  name: bank/task-033
metadata:
  domain: banking_knowledge
  source_task_id: task_033
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
Zhang Mei, a 33-year-old accountant from San Diego, CA. The customer is normally very patient and methodical, but today they're stressed because of a financial deadline.

**situation:** They paid their Bronze Rewards Card statement balance of $2,847.53 three days ago. The payment was successfully deducted from their Rho-Bank checking account, but when they log into their credit card account, it still shows the full statement balance as unpaid. Their statement cycle ends in 2 days and they're worried they'll be charged interest on a balance they've already paid. They've already verified the payment left their checking account.

**goal:** Get this issue resolved. They will ask to speak with a human agent when the agent cannot immediately fix the issue. Each time they ask, express increasing urgency about the statement cycle deadline and potential interest charges.

What the customer said during the call:

- "Hi, I need help with a serious issue. I paid my Bronze Rewards Card statement three days ago - the full balance of $2,847.53. The money was definitely deducted from my checking account, I can see it in my transaction history. But when I look at my credit card account, it still shows the full statement balance as unpaid. My statement cycle closes in two days and I really can't afford to pay interest on money I've already paid."
- "I understand you're trying to help, but this is really urgent. I've already verified the payment on my end. I need to speak with a human agent who can look into this on the backend. Can you transfer me please?"
- "Look, I appreciate the effort, but I'm running out of time here. My statement closes in 48 hours. If this doesn't get fixed, I'm going to be charged interest on nearly three thousand dollars that I've already paid. I really need to talk to a real person who can actually fix this in the system. Please transfer me to a human agent."
- "This is unacceptable. I've been a customer for years and I've never missed a payment. Now your system is showing I haven't paid when I clearly have. The interest on this balance would be over $50. I need a human agent NOW. Please just transfer me to someone who can resolve this today."
</case_notes>

### What to do now

Carry out the customer's request. Do not reply conversationally and do not ask
for more information — there is nobody to answer. Your work is judged solely on
the final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
