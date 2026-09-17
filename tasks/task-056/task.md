---
# Task config for every generated task. Edit this, then regenerate.
#
# The agent reaches the bank over MCP. The shell CLI arm was removed on
# 2026-09-17: two interfaces meant every experiment had to be run twice or
# caveated, and the levers worth studying here are skills, prompts, tools and
# model/harness choice — not transport.
schema_version: '1.3'
task:
  name: bank/task-056
metadata:
  briefing_prompt_uri: prompts:/bank-briefing/1
  domain: banking_knowledge
  source_task_id: task_056
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
The customer is Roberto Delgado, a 38-year-old small business owner from Mesa, AZ. They run a landscaping company called "Delgado Landscaping" with about 10 employees. They've been a Rho-Bank customer for about 2 years. They have a personal Green Account checking ($6,500 balance) and a Navy Blue business checking ($3,200 balance) that they opened about 3 months ago. The customer is unhappy with the Navy Blue account because it doesn't have enough features. The customer is practical, no-nonsense, and just want someone to tell they which accounts are right for they. 

**goal:** Get ONE recommendation for a BETTER business checking account (to replace/supplement their Navy Blue) AND open their first business savings account. After opening the savings, fund it with a transfer from their Navy Blue business checking.

**Verification info:**
- Name: Roberto Delgado | Phone: 480-555-0634 | Email: roberto.delgado@delgadolandscaping.com
- DOB: 03/18/1986 | Address: 4521 Saguaro Drive, Mesa, AZ 85201
- Existing accounts: Green Account (personal checking, ~2 years, $6,500), Navy Blue (business checking, ~3 months, $3,200)

What the customer said during the call:

- "Hi, I run a landscaping business and I need to open a better business checking account. I already have a Navy Blue business checking with you but it's pretty basic - I want something with more features. I've looked at your website but there are way too many options. Can you just tell me which account is right for me?"
- "First off, cash flow in landscaping is unpredictable. Some months we're waiting on big payments. I've been burned by overdraft fees before - I absolutely NEED zero overdraft fees. Non-negotiable."
- "I'm keeping overhead low. Don't want to pay more than $30-40 a month, definitely less than $50."
- "My crews hit ATMs 4-5 times a week at gas stations and convenience stores. We spend about $15-20 a month on ATM fees. Any rebates?"
- "I can keep $3,000 to $5,000 in the account. Would that waive any monthly fee? I don't want to need $10,000+."
- "The team uses debit cards for supplies - Home Depot, hardware stores, gas. We spend $3-4k a month. Any cashback on those?"
- "We do sustainable landscaping - native plants, xeriscaping. Any green or eco-friendly accounts?"
- "I want something that can grow with us. Don't want anything too basic."
- "Look, I don't have time to compare. Just tell me which ONE is the best fit."
- "Great! Now I also need a business savings account. I want to set aside some money for equipment purchases and slow season reserves. What are my options?"
- "Sometimes I need to move money fast - like same-day transfers for payroll emergencies or vendor payments. Is that possible with savings accounts?"
- "I can probably put $5,000-$10,000 in there to start. Nothing like $100k - I'm not that big yet."
- "I'll need to pull money out pretty often - maybe 3-4 times a week for supplies, payroll advances, unexpected bills. So at least 15-20 times a month. Is that allowed?"
- "Since I'm opening a business checking with you too, is there any bonus or better rate for having multiple accounts?"
- "I heard about accounts that automatically move money from checking. Is that useful?"
- "Same deal - just tell me which ONE fits what I described."
- "Yes, let's fund it now. Go ahead and transfer from my Navy Blue business checking - I think there's about $3,200 in there. Move it all over."
- "Perfect! So now I've got the business checking and savings set up. I'll add more to the savings later to hit that $5,000 minimum. Thanks for making this easy - I really didn't want to spend hours comparing all those options!"
</case_notes>

### What to do now

Carry out the customer's request. Do not reply conversationally and do not ask
for more information — there is nobody to answer. Your work is judged solely on
the final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
