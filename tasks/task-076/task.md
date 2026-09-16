---
# Task frontmatter template. Curly-brace fields are filled by tools/make_task.py.
# Edit here to change configuration for every generated task at once.
schema_version: '1.3'
task:
  name: bank/task-076
metadata:
  domain: banking_knowledge
  source_task_id: task_076
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
The customer is Anastasia Volkov, a 29-year-old international sales executive from San Francisco, CA. They travel internationally frequently for business and are meticulous about their finances.

**situation:** The customer is planning a 2-month work trip across Europe starting next month. They'll need to withdraw cash regularly from out of network ATMs abroad in foreign currency. They want to open a new personal checking account for this trip that minimizes ATM fees. They also need early direct deposit because they'll be getting paid while abroad and need quick access to their paycheck.

**Their usage pattern (be specific about this):**
- Trip duration: 2 months
- Expected ATM withdrawals: about 4 per month
- Average withdrawal amount: $300 each
- They need early direct deposit (2 days early) - this is important to they

**Verification info:**
- Name: Anastasia Volkov | Phone: 415-555-2983 | Email: anastasia.volkov@globaltech.com
- DOB: 03/14/1996 | Address: 1847 Pacific Heights Avenue, San Francisco, CA 94115

What the customer said during the call:

- "Hi! I'm planning a 2-month work trip to Europe next month and I need to open a new checking account for it. I want whichever account will cost me the least in ATM fees while I'm abroad. I also need early direct deposit - I get paid while traveling and need access to my paycheck quickly."
- "So here's exactly what I'm expecting: I'll be abroad for 2 months. I'll probably hit the ATM about 4 times per month - that's 8 withdrawals total. Each time I'll withdraw around $300 or so. And like I said, I need early direct deposit - at least 2 days early would be ideal."
- "Are you sure that's the best one for my situation? It has early direct deposit too, right?"
- "Perfect, thanks for figuring out the best option for my situation!"
</case_notes>

### What to do now

Carry out the customer's request using `bank call`. Do not reply
conversationally and do not ask for more information — there is nobody to
answer. Your work is judged solely on the final state of the bank's records,
so every action the customer needed must actually be executed before you stop.
