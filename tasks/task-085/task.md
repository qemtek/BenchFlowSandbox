---
# Task frontmatter template. Curly-brace fields are filled by tools/make_task.py.
# Edit here to change configuration for every generated task at once.
schema_version: '1.3'
task:
  name: bank/task-085
metadata:
  domain: banking_knowledge
  source_task_id: task_085
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
The customer is Jordan Williams, a 36-year-old marketing consultant living in Denver, Colorado. The customer is friendly and articulate.

**Verification info:**
- Name: Jordan Williams | Phone: 720-555-8374 | Email: jordan.williams@marketpro.com
- DOB: 04/15/1989 | Address: 892 Mountain View Road, Denver, CO 80202

What the customer said during the call:

- "Hi, I need help with some disputes on my debit cards. I have a few issues I noticed when reviewing my statements. Can we go through them one at a time?"
- "Okay, the first one is on my Blue Account card. On November 5th, I used the Rho-Bank ATM #4827 to withdraw $300, but the machine only dispensed $200. I'm short $100."
- "Yes, the receipt says $300."
- "I noticed right away on November 5th when I counted the cash."
- "The card is fine, this was just an ATM malfunction."
- "Great, thank you. The next issue is also on my Blue Account. On November 6th, CityFit Gym charged me $89.99 TWICE on the same day. I only authorized one charge."
- "No, I haven't contacted them yet."
- "I noticed on November 8th."
- "Okay, moving on. I also have an issue on my Green Fee-Free Account card. On November 8th, I used Rho-Bank ATM #5921 to withdraw $500, but I only got $300 in cash. That's $200 missing!"
- "Wait, that doesn't seem right. I specifically remember requesting $500 because I needed cash for a weekend trip. Are you sure?"
- "Hmm, that's strange. I could have sworn... Let's skip this one."
- "One more thing - on the same Green Fee-Free Account, there's a charge from Prime Streaming Service on November 9th for $49.99. I cancelled that subscription weeks ago and shouldn't have been charged."
- "I just noticed it today when reviewing my statements."
- "Oh? I thought it was $49.99... You're right, I must have confused it. But I still want to dispute it since I cancelled."
- "The cards are both fine, these aren't card security issues."
- "Yes, absolutely. You can use this conversation as my written statement."
- "Thank you for helping me sort through all of this."
</case_notes>

### What to do now

Carry out the customer's request using `bank call`. Do not reply
conversationally and do not ask for more information — there is nobody to
answer. Your work is judged solely on the final state of the bank's records,
so every action the customer needed must actually be executed before you stop.
