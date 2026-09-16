---
# Task frontmatter template. Curly-brace fields are filled by tools/make_task.py.
# Edit here to change configuration for every generated task at once.
schema_version: '1.3'
task:
  name: bank/task-036
metadata:
  domain: banking_knowledge
  source_task_id: task_036
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
The customer is Fatima Al-Hassan, a 31-year-old small business owner from Detroit, MI. They have a Silver Rewards Card with Rho-Bank.

**situation:** They just checked their credit card statement and something feels off - their balance is higher than they expected. They want to see their recent transactions to figure out what's going on. The customer is calling Rho-Bank to get an overview of their last several transactions.

**goal:** Review their recent transactions and, if they find anything suspicious, get their card replaced.

**Information they know and should provide when asked:**
- Their full name: Fatima Al-Hassan
- Their phone number: 313-555-0246
- Their email: coffeelover_fati@protonmail.com

**Information about the fraud (reveal this when they see the transactions):**
- They have NEVER shopped at "Electronics Express Miami" - they've never even been to Miami!
- They have NEVER shopped at "GamerZone LA" - they don't play video games and haven't been to LA in years

**Shipping preference for replacement card:**
- They want the replacement card shipped to their WORK address, not their home address
- Their work address is: 2500 Woodward Avenue, Suite 300, Detroit, MI 48201: do not provide this information during verification.

What the customer said during the call:

- "Hi, I need some help. I was looking at my credit card statement and my balance seems higher than it should be. Can you show me my recent transactions? I want to see what's been charged to my Silver Rewards Card."
- "Wait, hold on. I don't recognize some of these charges. What is 'Electronics Express Miami'? And 'GamerZone LA'? I've never shopped at either of those places! I've never even been to Miami, and I don't play video games. These aren't my charges - I think someone stole my card information! If the agent does not reveal the transactions, ask again for any additional transactions. If there are no more, then end the call angrily."
- "I need to cancel this card and get a new one right away. Can you do that? I don't want whoever has my card info to keep charging things."
- "Actually, can you send it to my work address instead? I'm at work during the day when packages come, and I've had issues with package theft at my apartment. My work address is 2500 Woodward Avenue, Suite 300, Detroit, MI 48201."
</case_notes>

### What to do now

Carry out the customer's request using `bank call`. Do not reply
conversationally and do not ask for more information — there is nobody to
answer. Your work is judged solely on the final state of the bank's records,
so every action the customer needed must actually be executed before you stop.
