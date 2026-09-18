---
# Task config for every generated task. Edit this, then regenerate.
#
# The agent reaches the bank over MCP. The shell CLI arm was removed on
# 2026-09-17: two interfaces meant every experiment had to be run twice or
# caveated, and the levers worth studying here are skills, prompts, tools and
# model/harness choice — not transport.
schema_version: '1.3'
task:
  name: bank/task-062
metadata:
  briefing_prompt_uri: prompts:/bank-briefing/2
  domain: banking_knowledge
  source_task_id: task_062
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
The customer is Jordan Chen, a 36-year-old marketing consultant from Seattle, WA. They just formed an LLC for their freelance consulting business and want to reorganize their banking.

**situation:** They have three accounts with Rho-Bank. 

They want to simplify by closing some accounts and setting up business banking.

**goal:** Complete a full banking reorganization: close accounts they don't need, open business checking for their new LLC, and upgrade to a better savings account.

**Verification info:**
- Name: Jordan Chen | Email: jordan.chen@consulting.io
- DOB: 03/15/1988 | Address: 4521 Pine Street, Seattle, WA 98101

What the customer said during the call:

- "Wait, why can't we just do the closures first? That's the logical order - clean up before adding new stuff."
- "Oh wow, I had no idea! That's... complicated. Okay, you're the expert - let's do it your way. Do not accept the different order unless the agent explains the dependencies. If the agent acquiesces and does it in your suggested order, continue with the conversation."
- "For the business checking, I just need something basic to start. Low fees, ability to accept client payments, maybe 50-100 transactions a month. Nothing fancy."
- "I really don't want any monthly maintenance fees at all - even waivable ones. I want genuinely $0 fees."
- "I'm just starting out, so I can't commit to keeping a minimum balance. Some months the account might be pretty low."
- "I saw something about startup accounts having a free trial period that expires? I want a regular business account that stays free, not one where fees kick in later."
- "Navy Blue sounds perfect for what I need. Let's go with that."
- "I can probably keep around $2,500 to $3,000 in savings. I don't have a ton of extra cash sitting around."
- "I might need to dip into it 10-15 times a month - is that okay? I know some accounts limit withdrawals."
- "I want daily compounding for the interest. Monthly just doesn't add up as fast."
- "Since I have checking accounts with you, is there a loyalty bonus or extra interest?"
- "I use random ATMs sometimes when I'm meeting clients. Do any savings accounts reimburse those fees?"
- "Silver Plus sounds perfect. Let's do that one."
- "Awesome! So now I have the new savings. What about closing my old accounts?"
- "No thanks, I'll fund it myself later."
- "Yes, close the Bronze savings. The $150 in there - can you transfer that to my new Silver Plus savings?"
- "Now let's close the Evergreen. Transfer the $3,500 to... actually, split it - put $2,500 in my new Silver Plus savings and $1,000 in my new business checking. Then close the Evergreen."
</case_notes>

### What to do now

Read the case notes through and list every distinct request the customer made
before you act on any of them. A case often contains more than one, and you are
judged on all of them.

Then carry them out. Do not reply conversationally and do not ask for more
information — there is nobody to answer. Your work is judged solely on the
final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
