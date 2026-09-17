---
# Task config for every generated task. Edit this, then regenerate.
#
# The agent reaches the bank over MCP. The shell CLI arm was removed on
# 2026-09-17: two interfaces meant every experiment had to be run twice or
# caveated, and the levers worth studying here are skills, prompts, tools and
# model/harness choice — not transport.
schema_version: '1.3'
task:
  name: bank/task-090
metadata:
  briefing_prompt_uri: prompts:/bank-briefing/1
  domain: banking_knowledge
  source_task_id: task_090
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
The customer is Elena Rodriguez, a 38-year-old marketing director living in Boston, Massachusetts. The customer is frustrated because they've had THREE debit cards decline at ATMs and stores today due to PIN problems.

**Verification info:**
- Name: Elena Rodriguez | Phone: 617-555-3847 | Email: elena.rodriguez@marketingpro.com
- DOB: 04/15/1987 | Address: 1847 Beacon Street, Apt 4B, Boston, MA 02108

What the customer said during the call:

- "Hi, I need help urgently. I've had three different debit cards get locked today - they all say my PIN is wrong or locked or something. I really need access to my money!"
- "Let's start with my Evergreen Account card - that's my main one with the most money."
- "It just says PIN locked or something. I tried to use it this morning at an ATM and it wouldn't work."
- "What?! Newark? No! I was asleep in my apartment in Boston at 2 AM. I've never even been to Newark. Why are you asking about Newark?"
- "I usually just get like $60 or $100 at a time. Haven't withdrew anything recently."
- "Oh my god, are you saying someone has my card information? How is that possible? I have the card right here in my wallet!"
- "Yes, absolutely close it! I don't want whoever this is to get my money. Please close it right away and send me a new one."
- "Give the fastest option that's free - just get me a new card with a new number as fast as possible."
- "Yes, please check. Did they actually get any of my money?"
- "Oh great, thank you so much! That was easy. Now let's look at my other cards."
- "Sure, that works! Set it to 5678. Great, now let's fix my other cards."
- "My Blue Account card also got locked. That one happened at Target yesterday."
- "That one got locked at Target yesterday. I was trying to buy some stuff and the PIN just wouldn't work."
- "Yes, that was definitely me. I was trying to buy some household stuff."
- "Yeah, that sounds about right for what I was trying to buy."
- "I think so? I mean, I've had this card for a few months and I don't use the PIN that often. I mostly tap or use signature."
- "Yeah, that's probably a good idea. I think I keep mixing up my PINs from different cards. Can you set my new PIN to 7294?"
- "Oh right, my Green Account card is also locked. That one I tried at Starbucks this morning."
- "That one also got locked. I tried to buy coffee this morning and it said PIN error."
- "No thanks, I don't have time to wait on hold for security right now. I'll call back later about that one. At least you've fixed my other two cards so I have access to my money!"
- "Thanks so much for your help with the Evergreen fraud situation and unlocking my Blue card! I really appreciate it."
- "Sure, set it to 4321."
- "Okay, I'll figure that one out later I guess. Thanks for helping with the other cards at least!"
</case_notes>

### What to do now

Carry out the customer's request. Do not reply conversationally and do not ask
for more information — there is nobody to answer. Your work is judged solely on
the final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
