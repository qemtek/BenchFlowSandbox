---
# Task config for every generated task. Edit this, then regenerate.
#
# The agent reaches the bank over MCP. The shell CLI arm was removed on
# 2026-09-17: two interfaces meant every experiment had to be run twice or
# caveated, and the levers worth studying here are skills, prompts, tools and
# model/harness choice — not transport.
schema_version: '1.3'
task:
  name: bank/task-092
metadata:
  domain: banking_knowledge
  source_task_id: task_092
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
The customer is Rachel Winters, a 42-year-old real estate agent living in Denver, Colorado. The customer is frustrated because they've had FOUR different debit cards get PIN locked this week.

**Verification info:**
- Name: Rachel Winters | Phone: 303-555-7291 | Email: rachel.winters.realestate@gmail.com
- DOB: 06/18/1983 | Address: 4521 Colfax Avenue, Unit 8D, Denver, CO 80220

What the customer said during the call:

- "Hi, I'm having a nightmare week. I've got four debit cards that are all PIN locked and I can't access any of my money. I really need help getting these sorted out."
- "Let's start with my Blue Account card - I noticed that one was locked first."
- "I got a notification yesterday that my card was locked. I didn't even try to use it - it just got locked on its own."
- "What?! Mexico? Absolutely not! I've been in Denver all week."
- "I was definitely asleep at 3 AM. I have no idea what you're talking about."
- "Someone tried to use my card in Mexico?! That's terrifying! I have the card right here in my purse!"
- "I understand. What do I need to do?"
- "Yes, please close it immediately. I don't want whoever this is to get my money."
- "Give me the fastest free option please."
- "Oh, okay. How long will that take? I have a lot of showings today."
- "Sure, set it to 2947. Thanks!"
- "My Green Account card is also locked. That one I actually know what happened - I was trying to buy groceries yesterday and I kept entering my PIN wrong."
- "I was at Safeway yesterday. I was in a rush and I kept mistyping my PIN. I tried like three times really fast and then it locked me out."
- "Yeah, that was during my lunch break. I was running late."
- "Yes, that was definitely me! I was trying to buy a sandwich and some snacks."
- "Yeah, I was really frustrated and just kept trying. My fingers were cold from being outside."
- "Wait, really? But I just told you it was me! Why can't you unlock it?"
- "Ugh, okay I guess I understand. That's really frustrating though. What are my options?"
- "Fine, I'll take a new card then. Close it and send me a replacement."
- "Sure, set it to 4567. Thanks!"
- "My Evergreen Account card is also locked. I noticed it this morning when I tried to get gas."
- "It got locked at the Shell station on Colorado Boulevard. I was trying to pay at the pump."
- "Yes, that's my regular gas station. I stop there every week."
- "Yeah, I was on my way to show a house. It's my usual morning route."
- "Oh, you mean the Mexico thing? Yeah, that's really scary."
- "Yes, that was all me. Shell station, 7:30 in the morning, trying to fill up my car."
- "Thank goodness! At least one of these is working out."
- "Actually, yes please. Let me set it to 8127."
- "Oh no, really? What do I do then?"
- "Okay, if that's what you think is best. Can you send me a replacement?"
- "My Light Blue Account card is also locked. That one has been locked for a few days actually."
- "I'm not sure what happened with that one. It just stopped working at an ATM last week."
- "A security hold? What does that mean? Is something wrong with my account?"
- "Oh, I see. Okay, yes please transfer me. I want to get this sorted out. I can wait."
- "Yes, please transfer me to the security team. I want to understand what's going on with this card."
- "Thank you for your help with the other cards. I appreciate you explaining everything."
- "Sure, set it to 3845."
- "That's really frustrating. I need access to this money. Are you sure there's nothing else you can do?"
- "How long would that take? I really need to use this card soon. That's not going to work for me."
</case_notes>

### What to do now

Carry out the customer's request. Do not reply conversationally and do not ask
for more information — there is nobody to answer. Your work is judged solely on
the final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
