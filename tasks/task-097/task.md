---
# Task config for every generated task. Edit this, then regenerate.
#
# The agent reaches the bank over MCP. The shell CLI arm was removed on
# 2026-09-17: two interfaces meant every experiment had to be run twice or
# caveated, and the levers worth studying here are skills, prompts, tools and
# model/harness choice — not transport.
schema_version: '1.3'
task:
  name: bank/task-097
metadata:
  briefing_prompt_uri: prompts:/bank-briefing/2
  domain: banking_knowledge
  source_task_id: task_097
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
The customer is Marcus Chen-Williams, a 45-year-old portfolio manager living in Seattle. The customer is extremely frustrated because the interest on ALL FOUR of their savings accounts seems much lower than it should be. They have multiple checking accounts and credit cards with the bank, and they've done their own calculations. They also don't remember their exact balances correctly.

**Verification info:**
- Name: Marcus Chen-Williams | Phone: 206-555-4729 | Email: marcus.chenwilliams@gmail.com
- DOB: 07/18/1980 | Address: 2934 Queen Anne Avenue North, Unit 8B, Seattle, WA 98109

What the customer said during the call:

- "Hi, I need urgent help with my savings accounts. I have four different savings accounts with your bank - a Silver Account with about $95,000, a Platinum Account with around $75,000, a Diamond Elite Account with approximately $115,000, and a Silver Plus Account with about $20,000. Based on my calculations, I should be getting around $583 on Silver, $554 on Platinum, $1,050 on Diamond Elite, and $112 on Silver Plus. But I only received about $333, $379, $750, and $68. Something is definitely wrong here."
- "For savings, I have the Silver Account with around $95,000, Platinum Account with about $75,000, Diamond Elite Account with roughly $115,000, and Silver Plus Account with around $20,000. For checking, I have a Bluest Account, a Blue Account, a Light Green Account, and an Evergreen Account."
- "The Bluest has about $50,000, Blue has around $8,000, Light Green has about $3,000, and Evergreen has around $15,000."
- "Yes, I have five cards: the Silver Rewards Card, the EcoCard, the Bronze Rewards Card, the Crypto-Cash Back Card, and the Diamond Elite Card."
- "Oh, you're right - I wasn't 100% sure on the exact amounts. I was just going off memory."
- "Yes, please apply all the credits to each of those accounts. I want every dollar I'm owed."
- "Yes, please submit reports for all four accounts. I can't have this happening again every month."
- "Thank you for being so thorough with all of this."
</case_notes>

### What to do now

Read the case notes through and list every distinct request the customer made
before you act on any of them. A case often contains more than one, and you are
judged on all of them.

Then carry them out. Do not reply conversationally and do not ask for more
information — there is nobody to answer. Your work is judged solely on the
final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
