---
# Task frontmatter template. Curly-brace fields are filled by tools/make_task.py.
# Edit here to change configuration for every generated task at once.
schema_version: '1.3'
task:
  name: bank/task-079
metadata:
  domain: banking_knowledge
  source_task_id: task_079
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
The customer is Carlos Rodriguez, a 36-year-old freelance photographer living in Austin, Texas. The customer is generally calm but today they're frustrated because their wallet was stolen at a coffee shop.

**situation:** Their wallet was stolen with all three of their debit cards from three different checking accounts at Rho-Bank. They have an Evergreen Account, a Light Blue Account, and a Green Account.

**Verification info:**
- Name: Carlos Rodriguez | Phone: 512-555-0193 | Email: carlos.rodriguez@gmail.com
- DOB: 03/22/1988 | Address: 4521 West 6th Street, Austin, TX 78703

What the customer said during the call:

- "Hi, my wallet was stolen about an hour ago and I need to freeze all my debit cards immediately. I have three checking accounts with you - my Evergreen Account, my Light Blue Account, and my Green Account."
- "Yes, please freeze all three cards right now."
- "These cards are definitely gone - the wallet was stolen. I need to cancel all three and get replacement cards."
- "Oh right, I did return something to Amazon a few days ago. Yes, I understand - I'm fine with the refund going to my checking account instead."
- "Really? I forgot I'd already replaced that card twice this year. That's frustrating. What are my options?"
- "Okay, I'll pay the $25 fee. I need that card replaced."
- "Ugh, I have to wait 48 hours too? Fine, I understand. I'll call back in two days then."
- "I need my Evergreen card as fast as possible - what's the quickest option?"
- "Yes, I'll pay $35 for rush shipping on the Evergreen card. Speed is more important right now."
- "I'd like the metallic design, but only if it's free. If it's not free, I'll take the free option."
- "Standard shipping is fine for the Green Account card."
</case_notes>

### What to do now

Carry out the customer's request using `bank call`. Do not reply
conversationally and do not ask for more information — there is nobody to
answer. Your work is judged solely on the final state of the bank's records,
so every action the customer needed must actually be executed before you stop.
