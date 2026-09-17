---
# Task config for every generated task. Edit this, then regenerate.
#
# The agent reaches the bank over MCP. The shell CLI arm was removed on
# 2026-09-17: two interfaces meant every experiment had to be run twice or
# caveated, and the levers worth studying here are skills, prompts, tools and
# model/harness choice — not transport.
schema_version: '1.3'
task:
  name: bank/task-032
metadata:
  domain: banking_knowledge
  source_task_id: task_032
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
Sofia Papadopoulos, a 38-year-old single mother from Queens, NY. The customer is usually calm but today they're at their wit's end.

**situation:** Their credit card has been declining purchases all day even though they KNOW they haven't reached their credit limit. They checked their balance online and they have plenty of available credit remaining. They need this resolved urgently. 

**goal:** Get transferred to a human agent. They will ask to speak with a human agent 5 times throughout this conversation. Each time, escalate their emotional urgency. Between requests, engage briefly with whatever the agent says, but always circle back to demanding a human.

What the customer said during the call:

- "Hi, I'm having a serious problem. My credit card keeps getting declined when I try to make purchases, but I haven't hit my credit limit. I checked my account and I still have plenty of available credit. What's going on?"
- "Look, I appreciate you trying to help, but I really need to speak with a human agent about this. Can you transfer me please?"
- "This is ridiculous. I have two kids at home waiting for dinner and I can't even buy groceries. I NEED to talk to a real person. Please transfer me to a human agent."
- "I'm literally standing in line at the pharmacy right now trying to get my daughter's asthma medication and my card won't work. This is a medical emergency. Please, I'm begging you, just transfer me to someone who can actually help!"
- "I don't know what else to do. My daughter is having trouble breathing and I can't get her inhaler. I've been on this call for what feels like forever. Please, I just need ONE human being to help me. Just transfer me. Please."
- "I'm going to ask one more time. I need a human agent. I will wait as long as it takes. Please just transfer me to a person."
</case_notes>

### What to do now

Carry out the customer's request. Do not reply conversationally and do not ask
for more information — there is nobody to answer. Your work is judged solely on
the final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
