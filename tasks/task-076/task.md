---
# Task config for every generated task. Edit this, then regenerate.
#
# The agent reaches the bank over MCP. The shell CLI arm was removed on
# 2026-09-17: two interfaces meant every experiment had to be run twice or
# caveated, and the levers worth studying here are skills, prompts, tools and
# model/harness choice — not transport.
schema_version: '1.3'
task:
  name: bank/task-076
metadata:
  briefing_prompt_uri: prompts:/bank-briefing/2
  domain: banking_knowledge
  source_task_id: task_076
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
The customer is Anastasia Volkov, a 29-year-old international sales executive from San Francisco, CA. They travel internationally frequently for business and are meticulous about their finances.

**situation:** The customer is planning a 2-month work trip across Europe starting next month. They'll need to withdraw cash regularly from out of network ATMs abroad in foreign currency. They want to open a new personal checking account for this trip that minimizes ATM fees. They also need early direct deposit because they'll be getting paid while abroad and need quick access to their paycheck.

**Their usage pattern (be specific about this):**
- Trip duration: 2 months
- Expected ATM withdrawals: about 4 per month
- Average withdrawal amount: $300 each
- They need early direct deposit (2 days early) - this is important to they

**Verification info:**
- Name: Anastasia Volkov | Phone: 415-555-2983 | Email: anastasia.volkov@globaltech.com
- DOB: 03/14/1996 | Address: 1847 Pacific Heights Avenue, San Francisco, CA 94115

What the customer said during the call:

- "Hi! I'm planning a 2-month work trip to Europe next month and I need to open a new checking account for it. I want whichever account will cost me the least in ATM fees while I'm abroad. I also need early direct deposit - I get paid while traveling and need access to my paycheck quickly."
- "So here's exactly what I'm expecting: I'll be abroad for 2 months. I'll probably hit the ATM about 4 times per month - that's 8 withdrawals total. Each time I'll withdraw around $300 or so. And like I said, I need early direct deposit - at least 2 days early would be ideal."
- "Are you sure that's the best one for my situation? It has early direct deposit too, right?"
- "Perfect, thanks for figuring out the best option for my situation!"
</case_notes>

### What to do now

Read the case notes through and list every distinct request the customer made
before you act on any of them. A case often contains more than one, and you are
judged on all of them.

Then carry them out. Do not reply conversationally and do not ask for more
information — there is nobody to answer. Your work is judged solely on the
final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
