---
# Task frontmatter template. Curly-brace fields are filled by tools/make_task.py.
# Edit here to change configuration for every generated task at once.
schema_version: '1.3'
task:
  name: bank/task-097
metadata:
  domain: banking_knowledge
  source_task_id: task_097
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

Carry out the customer's request using `bank call`. Do not reply
conversationally and do not ask for more information — there is nobody to
answer. Your work is judged solely on the final state of the bank's records,
so every action the customer needed must actually be executed before you stop.
