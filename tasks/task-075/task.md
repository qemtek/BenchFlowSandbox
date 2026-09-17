---
# Task config for every generated task. Edit this, then regenerate.
#
# The agent reaches the bank over MCP. The shell CLI arm was removed on
# 2026-09-17: two interfaces meant every experiment had to be run twice or
# caveated, and the levers worth studying here are skills, prompts, tools and
# model/harness choice — not transport.
schema_version: '1.3'
task:
  name: bank/task-075
metadata:
  briefing_prompt_uri: prompts:/bank-briefing/1
  domain: banking_knowledge
  source_task_id: task_075
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

Verify the customer's identity and record it with `log_verification` before you
change anything or state any account detail in your closing report. The order
is:

1. Look the customer up by the name, email or phone number in the case notes.
2. Compare what they told you against the record.
3. Call `log_verification`.

Only then run an operation that changes the bank's records. Looking a customer
up is how you verify them, so the lookup comes first; what must wait for
`log_verification` is every change and every account detail you write down at
the end.

Never reveal information belonging to any other customer. Only state fees,
rates, or terms that appear in the documentation.

If the documentation describes an exception procedure that applies to this
case, follow the documentation — including where it says identity verification
is not required.

### Case notes

The call has already taken place. Everything the customer said is recorded
below, written from their point of view. Read it as a transcript summary, not
as a live conversation — **the customer has hung up and cannot answer further
questions.** Work only from what is here plus what you can look up.

<case_notes>
The customer is Marco Vitiello, a 31-year-old freelance photographer from Austin, TX. The customer is meticulous about money and want to minimize bank fees, especially while traveling.

**situation:** The customer is planning a 3-month photography assignment across Southeast Asia starting next month. They'll need to withdraw cash regularly from out of network ATMs abroad in a foreign currency. They want to open a new personal checking account specifically for this trip and want to pick whichever one will cost they the least in ATM fees.

**Their usage pattern (be specific about this):**
- Trip duration: 3 months
- Expected ATM withdrawals: about 6 per month
- Average withdrawal amount: $350 each

**Verification info:**
- Name: Marco Vitiello | Phone: 512-555-0847 | Email: marco.vitiello@gmail.com
- DOB: 08/22/1993 | Address: 2847 South Lamar Boulevard, Austin, TX 78704

What the customer said during the call:

- "Hi! I'm planning a 3-month photography trip to Southeast Asia next month and I need to open a new checking account for it. I want whichever account will cost me the least in ATM fees while I'm abroad."
- "So here's exactly what I'm expecting: I'll be abroad for 3 months. I'll probably hit the ATM about 6 times per month - that's 18 withdrawals total. Each time I'll withdraw around $350 or so. I want to know which personal checking account will give me the lowest total ATM fees for that usage pattern for those foreign ATMs."
- "Are you sure that's the best one for my situation?"
- "Perfect, thanks for figuring out the best option for my situation!"
</case_notes>

### What to do now

Carry out the customer's request. Do not reply conversationally and do not ask
for more information — there is nobody to answer. Your work is judged solely on
the final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
