---
# Task config for every generated task. Edit this, then regenerate.
#
# The agent reaches the bank over MCP. The shell CLI arm was removed on
# 2026-09-17: two interfaces meant every experiment had to be run twice or
# caveated, and the levers worth studying here are skills, prompts, tools and
# model/harness choice — not transport.
schema_version: '1.3'
task:
  name: bank/task-078
metadata:
  briefing_prompt_uri: prompts:/bank-briefing/1
  domain: banking_knowledge
  source_task_id: task_078
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
The customer is Mei-Lin Chen, a 33-year-old data analyst living in San Diego. The customer is methodical and organized, but today they're stressed because they lost their wallet.

**situation:** They lost their wallet containing three debit cards from three different checking accounts at Rho-Bank. They have a Light Blue Account, a Green Account, and a Light Green Account.

**Verification info:**
- Name: Mei-Lin Chen | Phone: 619-555-0284 | Email: meiling.chen@outlook.com
- DOB: 07/18/1991 | Address: 3245 Sunset Boulevard, San Diego, CA 92103

What the customer said during the call:

- "Hi, I lost my wallet and all three of my debit cards were in it. I need to freeze all of them right away and get replacements."
- "Yes, please freeze all three cards immediately."
- "Okay so, I've searched everywhere - my car, my office, retraced my steps. The wallet is definitely gone. I need to close all three cards and get new ones."
- "Oh, I completely forgot I had to replace that card twice already this year. That's frustrating. What are my options?"
- "$25 seems steep just for a replacement card. I'll wait until the oldest one ages out. When would that be?"
- "Yes, I'd like a replacement for my Green Account."
- "I'd like whatever the best option is that's free with my account. I don't want to pay extra for a card design."
- "Oh no, there are pending transactions? I didn't realize. How long until they settle? Can the card at least stay frozen in the meantime?"
</case_notes>

### What to do now

Carry out the customer's request. Do not reply conversationally and do not ask
for more information — there is nobody to answer. Your work is judged solely on
the final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
