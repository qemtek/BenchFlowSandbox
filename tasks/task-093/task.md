---
# Task frontmatter template. Curly-brace fields are filled by tools/make_task.py.
# Edit here to change configuration for every generated task at once.
schema_version: '1.3'
task:
  name: bank/task-093
metadata:
  domain: banking_knowledge
  source_task_id: task_093
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
The customer is Somchai Prasert, a 36-year-old software developer living in Los Angeles. The customer is frustrated because their recent interest payments on their Silver savings account seem lower than they expected. 

**Verification info:**
- Name: Somchai Prasert | Phone: 323-555-0847 | Email: somchai.prasert@gmail.com
- DOB: 08/14/1989 | Address: 1847 Sunset Boulevard, Apt 12B, Los Angeles, CA 90028

What the customer said during the call:

- "Hi, I think there might be something wrong with my interest payments. I have a savings account with you and my monthly interest just seems... low? I'm not sure exactly what I should be getting but it doesn't feel right."
- "I have a Silver savings account. I also have a checking account with you - a Green one I think?"
- "I'm not sure of the exact numbers off the top of my head. Can you look it up?"
- "Yes, please do that."
- "Good, please do that."
- "Okay, thank you for looking into this. I appreciate it."
</case_notes>

### What to do now

Carry out the customer's request using `bank call`. Do not reply
conversationally and do not ask for more information — there is nobody to
answer. Your work is judged solely on the final state of the bank's records,
so every action the customer needed must actually be executed before you stop.
