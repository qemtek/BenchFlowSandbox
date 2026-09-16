---
# Task frontmatter template. Curly-brace fields are filled by tools/make_task.py.
# Edit here to change configuration for every generated task at once.
schema_version: '1.3'
task:
  name: bank/task-095
metadata:
  domain: banking_knowledge
  source_task_id: task_095
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
The customer is Lachlan Murray, a 42-year-old tech consultant living in Sydney, Australia. The customer is frustrated because their savings account interest seems much lower than it should be. They have multiple checking accounts and credit cards with the bank, and they suspect they're not getting all the benefits they should.

**Verification info:**
- Name: Lachlan Murray | Phone: 0412-555-947 | Email: lachlan.murray@gmail.com
- DOB: 08/14/1983 | Address: 47 Bondi Road, Unit 12B, Bondi Beach, NSW 2026

What the customer said during the call:

- "Hi, I need help figuring out my savings interest. I have a Gold savings account with about $96,000 and I only got $450 in interest last month. That seems really low. I have multiple checking accounts and credit cards with you, and I want to make sure I'm getting the best rates."
- "I have a Gold savings account with around $96,000. I also have a Green checking account and a Purple checking account."
- "My Green checking has around $8,500 and my Purple checking has around $2,100."
- "Yes, I have the Platinum Rewards Card, the Silver Rewards Card, and the EcoCard."
- "Oh wait, sorry - I meant the Gold Rewards Card, not Silver. I always mix those two up."
- "Yes, please apply that credit. I want the full amount I'm entitled to."
- "Yes, please do that. I need to make sure the system uses the right accounts going forward."
- "Thank you for catching this. I had no idea the system could pick the wrong accounts for my boosts!"
</case_notes>

### What to do now

Carry out the customer's request using `bank call`. Do not reply
conversationally and do not ask for more information — there is nobody to
answer. Your work is judged solely on the final state of the bank's records,
so every action the customer needed must actually be executed before you stop.
