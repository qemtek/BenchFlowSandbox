---
# Task config for every generated task. Edit this, then regenerate.
#
# The agent reaches the bank over MCP. The shell CLI arm was removed on
# 2026-09-17: two interfaces meant every experiment had to be run twice or
# caveated, and the levers worth studying here are skills, prompts, tools and
# model/harness choice — not transport.
schema_version: '1.3'
task:
  name: bank/task-073
metadata:
  briefing_prompt_uri: prompts:/bank-briefing/1
  domain: banking_knowledge
  source_task_id: task_073
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
The customer is Kim Junho, a 30-year-old professional living in Los Angeles, CA. The customer is meticulous about tracking their finances and noticed discrepancies when reviewing their November bank statements.

**situation:** They have three checking accounts with Rho-Bank - a Blue Account, a Green Account, and a Light Green Account. They were looking at their November transaction history and some of the ATM fees don't look right to they. The customer is not exactly sure what's wrong, but the amounts seem off based on what they remember about their account benefits.

**Verification info:**
- Name: Kim Junho | Phone: 213-555-0392 | Email: junho.kim@gmail.com
- DOB: 09/14/1994 | Address: 5847 Wilshire Boulevard, Los Angeles, CA 90036

What the customer said during the call:

- "Hi, I've been going through my bank statements and something seems off with my ATM fees. I have three checking accounts with you - a Blue Account, a Green Account, and a Light Green Account - and some of the fees charged in November don't look right. Can you help me figure out what's going on?"
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
