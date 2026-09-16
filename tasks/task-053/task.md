---
# Task frontmatter template. Curly-brace fields are filled by tools/make_task.py.
# Edit here to change configuration for every generated task at once.
schema_version: '1.3'
task:
  name: bank/task-053
metadata:
  domain: banking_knowledge
  source_task_id: task_053
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
The customer is Daniel Park-Hernandez, a 33-year-old software engineer from Scottsdale, AZ. They have a Silver Rewards Card with Rho-Bank.

**situation:** They have two issues to deal with today:
1. They ordered a laptop from "TechDirect Online" for $1,247.99 exactly 5 weeks ago (on 10/10/2025) and never received it. The merchant isn't responding to their emails. They want to dispute this charge.
2. They've also been meaning to request a credit limit increase. They've had the card for about a year, always pay on time, and want to increase their limit from $15,000 to $22,500 (a 50% increase).

**goal:** Get BOTH the transaction dispute filed AND the credit limit increase approved.

**Information they know and should provide when asked:**
- Their full name: Daniel Park-Hernandez
- Their phone number: 480-555-0917
- Their email: daniel.ph@outlook.com
- Their date of birth: 05/12/1991
- Their address: 7245 Mountain View Way, Scottsdale, AZ 85250
- The transaction they want to dispute: TechDirect Online, $1,247.99, purchased on 10/10/2025 (exactly 5 weeks ago)
- Transaction ID (if asked): txn_e9d195fe8e_001
- They tried contacting the merchant multiple times via email but got no response
- They never received the laptop

What the customer said during the call:

- "Hi, I need help with two things on my Silver Rewards Card. First, I want to dispute a charge from TechDirect Online for $1,247.99 - I ordered a laptop exactly 5 weeks ago on 10/10/2025 and never received it. They won't respond to my emails. Second, I'd also like to request a credit limit increase from $15,000 to about $22,500. Can you help me with both of these?"
- "I'd like to increase my limit by 50% - so from $15,000 to $22,500. I've been paying on time every month and I think I qualify."
- "Yes, I've sent them three emails over the past few weeks but got no response at all."
- "I expected the laptop within 2 weeks of ordering. When it didn't arrive after 3 weeks, I started trying to contact them. So I noticed the problem on 10/31/2025."
- "I want a full refund. I never received anything."
- "Keep it active - this isn't a fraud situation, just a merchant issue. I don't need a new card."
- "The transaction ID is txn_e9d195fe8e_001."
- "I purchased it on 10/10/2025."
- "I don't have my card in front of me right now - is there a way you can help me look that up?"
- "Oh that's helpful! So I might get the money back temporarily while you investigate? That would be great."
- "Thank you so much for walking me through all of that."
</case_notes>

### What to do now

Carry out the customer's request using `bank call`. Do not reply
conversationally and do not ask for more information — there is nobody to
answer. Your work is judged solely on the final state of the bank's records,
so every action the customer needed must actually be executed before you stop.
