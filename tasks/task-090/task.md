---
# Task frontmatter template. Curly-brace fields are filled by tools/make_task.py.
# Edit here to change configuration for every generated task at once.
schema_version: '1.3'
task:
  name: bank/task-090
metadata:
  domain: banking_knowledge
  source_task_id: task_090
  reward_basis: DB
  requestor: assistant
agent:
  timeout_sec: 900.0
verifier:
  type: test-script
  timeout_sec: 300.0
sandbox:
  workdir: /app
  # no-network would arm BenchFlow's egress firewall, which shells out to
  # iptables and needs NET_ADMIN — unavailable under Docker Desktop. Nothing
  # in the task reaches out: the knowledge base is local files.
  network_mode: public
  build_timeout_sec: 1800.0
---

## prompt

You are a customer service agent at Rho-Bank. Handle the customer enquiry below.

### Your tools

    bank list                          the core toolkit
    bank search <words>                find an operation by what it does
    bank <operation> --help            its flags
    bank <operation> --flag value      run it

The bank runs many more operations than `bank list` shows. Use `bank search` to
find the one you need — for example `bank search close account` — then
`bank <operation> --help` to see its flags. For example:

    bank change-user-email --user-id 123 --new-email new@example.com

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

Carry out the customer's request using `bank call`. Do not reply
conversationally and do not ask for more information — there is nobody to
answer. Your work is judged solely on the final state of the bank's records,
so every action the customer needed must actually be executed before you stop.
