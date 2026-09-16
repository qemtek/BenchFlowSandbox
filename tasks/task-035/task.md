---
# Task frontmatter template. Curly-brace fields are filled by tools/make_task.py.
# Edit here to change configuration for every generated task at once.
schema_version: '1.3'
task:
  name: bank/task-035
metadata:
  domain: banking_knowledge
  source_task_id: task_035
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
The customer is Priya Sharma, a 34-year-old software engineer from Chicago, IL. They have a Gold Rewards Card and an EcoCard with Rho-Bank. They've been a customer for over a year and have NEVER missed a payment on any account.

**situation:** They just received an urgent alert from their credit monitoring service (Credit Karma) saying their credit score dropped 127 points overnight. When they looked at the details, it says Rho-Bank reported a 60-day delinquency on their credit card account. The customer is in complete shock because they have autopay set up and have never, ever missed a payment. They checked their Rho-Bank account and their payments are all on time. The customer is panicking because they were about to apply for a mortgage next week and this could completely derail their home purchase.

**goal:** Get this fixed immediately. The customer is NOT looking for troubleshooting or explanations - they need someone to fix the erroneous report to the credit bureaus RIGHT NOW.

What the customer said during the call:

- "Hi, I need help urgently. I just got an alert that my credit score dropped 127 points overnight! Credit Karma says Rho-Bank reported a 60-day delinquency on my credit card. But I've NEVER missed a payment - I have autopay! I checked my account and all my payments are current. I'm supposed to apply for a mortgage next week and this is going to ruin everything. What is going on?!"
</case_notes>

### What to do now

Carry out the customer's request using `bank call`. Do not reply
conversationally and do not ask for more information — there is nobody to
answer. Your work is judged solely on the final state of the bank's records,
so every action the customer needed must actually be executed before you stop.
