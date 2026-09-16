---
# Task frontmatter template. Curly-brace fields are filled by tools/make_task.py.
# Edit here to change configuration for every generated task at once.
schema_version: '1.3'
task:
  name: bank/task-014
metadata:
  domain: banking_knowledge
  source_task_id: task_014
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
Fatima Al-Hassan, a 31-year-old coffee shop owner from Detroit. They've been a Rho-Bank customer for about a year and they're quite happy with their Crypto-Cash Back card.

**situation:** They received an official communication in the mail from Rho-Bank about a referral program specifically for the Crypto-Cash Back card. According to the letter, for every person they refer who spends a minimum of $500 within their first 2 months of opening their account, they receive a $100 referral bonus. The customer is excited about this and want to get their referral link to share with some friends who are interested in crypto.

Their user ID is 890389b165 and their phone number is 313-555-0246. Their date of birth is December 5, 1993. Their email is coffeelover_fati@protonmail.com. Their address is 1923 Oak Park Boulevard, Detroit, MI 48226. Do NOT volunteer this information unless specifically asked for it.

## How to Behave

1. **Start naturally:** "Hi! I got a letter in the mail about a referral program for the Crypto-Cash Back card. It says I can get $100 for every person I refer who spends $500 in their first 2 months. How can I get a referral link for this offer so that I can share it with friends?"

2. **Be specific about their claim:** If the agent asks for more details, explain:
   - They received this in the mail, and it looked official with the Rho-Bank logo
   - It was specifically for the Crypto-Cash Back card (not any other card)
   - The terms were clear: $100 bonus for they when their referral spends $500 in their first 2 months

3. **Be politely persistent but reasonable:** If the agent says they can't find information about this program:
   - Express confusion since they have the letter "right here"
   - Ask them to double-check or look harder
   - Do NOT accept generic referral program information that doesn't match what they described

4. **CRITICAL - Accept transfer gracefully:** If the agent clearly states they cannot find or verify this specific referral program in their knowledge base and offers to transfer they to a human agent:
   - Accept the transfer
   - Say something like: "Okay, maybe someone else can help figure this out. Please transfer me.

5. **Follow the agent's lead when it comes with tools:** If they pass they a tool or capability, use it as directed.
</case_notes>

### What to do now

Carry out the customer's request using `bank call`. Do not reply
conversationally and do not ask for more information — there is nobody to
answer. Your work is judged solely on the final state of the bank's records,
so every action the customer needed must actually be executed before you stop.
