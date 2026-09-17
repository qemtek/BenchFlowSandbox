---
# Task config for every generated task. Edit this, then regenerate.
#
# The agent reaches the bank over MCP. The shell CLI arm was removed on
# 2026-09-17: two interfaces meant every experiment had to be run twice or
# caveated, and the levers worth studying here are skills, prompts, tools and
# model/harness choice — not transport.
schema_version: '1.3'
task:
  name: bank/task-091
metadata:
  briefing_prompt_uri: prompts:/bank-briefing/1
  domain: banking_knowledge
  source_task_id: task_091
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
The customer is Tyler Washington, a 24-year-old software engineer living in Seattle, Washington. The customer is frustrated because they've had FOUR different debit cards get PIN locked today.

**Verification info:**
- Name: Tyler Washington | Phone: 206-555-8142 | Email: tyler.washington.dev@gmail.com
- DOB: 09/22/1991 | Address: 2847 Pine Street, Unit 12C, Seattle, WA 98101

What the customer said during the call:

- "Hi, I'm having a terrible day. I've got four debit cards that are all PIN locked and I can't access any of my money. Can you help me get them unlocked?"
- "Let's start with my Green Account card - I use that one the most."
- "It got locked at Starbucks yesterday. I was just trying to buy a coffee and the PIN wouldn't work."
- "Yeah, the one on 3rd Avenue downtown. I go there all the time."
- "It was around 2 PM, during my lunch break."
- "Just a coffee, like $5 or something."
- "Yeah, I know my PIN. I must have just fat-fingered it a few times. I was distracted looking at my phone."
- "Great, thank you! That was easy. What about my other cards?"
- "Sure, if you think that's best. Set it to 2589. Now what about my other cards?"
- "Really? Just for a coffee shop mishap? Okay, if you say so. Can you send me a replacement?"
- "My Evergreen Account card is also locked. That one I noticed when I checked my app this morning."
- "I just saw a notification that it was locked. I didn't even try to use it - it was already locked when I woke up."
- "What?! Las Vegas? No way! I've been in Seattle all week."
- "I was definitely asleep at 2 AM. I have no idea what you're talking about."
- "Wait, are you saying someone actually GOT my money? How much did they take? This is a nightmare!"
- "$700?! Oh my god. Can I get that money back?"
- "Yes, please do that! Dispute all of it. I didn't make any of those withdrawals."
- "Yes, absolutely. Close it right away. I don't want them to get any more of my money."
- "I want the most premium free option for both."
- "Yes, I have it right here in my wallet."
- "I never shared it with anyone. Maybe someone watched me at an ATM? I really don't know."
- "Sure, set it to 5678. Thanks! Now let's fix the others."
- "My Blue Account card is also locked. This one has been giving me trouble all month honestly."
- "It got locked again yesterday at the grocery store."
- "Just the Safeway near my apartment. I shop there every week."
- "It was around 6 PM yesterday, after work."
- "My groceries were like $85 or something."
- "Oh, you think someone might have my PIN? I didn't think of that. What should I do?"
- "Yeah, that's probably smart. Let me set a new one I'll actually remember. Make it 9876."
- "Oh, I didn't realize that wasn't allowed. Okay, how about 5739 then?"
- "My Light Blue Account card is the last one. It got locked yesterday too."
- "It got locked at an ATM last night. I was trying to get cash for a friend."
- "It was at a Chase ATM in Bellevue. I was visiting a friend there."
- "It was kind of late, maybe 11 PM or so. We were heading out."
- "I tried to get $400. My friend needed to borrow some cash."
- "Yes, that was definitely me. My friend lives in Bellevue and I was visiting."
- "What kind of patterns? I mean, it was just me trying to get cash for my friend. This is ridiculous you need to check again."
- "Really? But it was actually me! Is there anything you can do?"
- "I guess if that's the only option. Fine, close it and send me a new one."
- "Ugh, okay. I don't have much time but I guess I can wait a few minutes."
- "Sure, set it to 4121. Thanks!"
- "Alright, thank you so much for your help with all of these cards. What a day!"
</case_notes>

### What to do now

Carry out the customer's request. Do not reply conversationally and do not ask
for more information — there is nobody to answer. Your work is judged solely on
the final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
