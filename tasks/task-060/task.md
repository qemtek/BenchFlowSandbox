---
# Task config for every generated task. Edit this, then regenerate.
#
# The agent reaches the bank over MCP. The shell CLI arm was removed on
# 2026-09-17: two interfaces meant every experiment had to be run twice or
# caveated, and the levers worth studying here are skills, prompts, tools and
# model/harness choice — not transport.
schema_version: '1.3'
task:
  name: bank/task-060
metadata:
  domain: banking_knowledge
  source_task_id: task_060
  reward_basis: DB
  requestor: assistant
  tool_interface: mcp
agent:
  timeout_sec: 900.0
verifier:
  type: test-script
  timeout_sec: 300.0
sandbox:
  workdir: /app
  network_mode: public
  build_timeout_sec: 1800.0
  mcp_servers:
    - name: bank
      transport: stdio
      command: python
      args: ['/opt/bank/vendor/bank_mcp.py']
      env:
        BANK_DB: /data/db.json
---

## prompt

You are a customer service agent at Rho-Bank. Handle the customer enquiry below.

### Your tools

The bank's systems are available to you as tools. The core toolkit is already
loaded.

The bank runs many more operations than are loaded. Three steps reach them:

1. **bank_search** — find an operation by describing what you want to do, for
   example "close account". Returns names and one-line descriptions.
2. **bank_describe_operation** — read its full signature: what each argument
   means, which are required, and any defaults. Search gives you names, not
   signatures.
3. **bank_call_operation** — run it, passing the operation name and its
   arguments.

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
The customer is Jordan Mitchell, a 35-year-old marketing manager from Denver, CO. They have been a Rho-Bank customer for about 4 months. They currently have two checking accounts with Rho-Bank.

**situation:** They have a Green (Checking) Account and a Blue (Checking) Account. They want to simplify their finances by closing the Green Account (they prefer to keep the Blue Account) and they also want to open a savings account to start building an emergency fund. The Green Account has no money in it - they already moved the funds out. They have very specific needs for their savings account.

**goal:** Close their Green checking account and open a savings account with a recommendation based on their detailed needs.

**Verification info:**
- Name: Jordan Mitchell | Phone: 303-555-0847 | Email: jordan.mitchell@outlook.com
- DOB: 08/22/1989

What the customer said during the call:

- "Hi, I need some help managing my accounts. I have two checking accounts with you - a Green Account and a Blue Account - and honestly, having two checking accounts is getting confusing. First, I want to close my Green Account and just keep the Blue one going forward. The Green Account is empty - I already moved the money out. And second, I've also been meaning to open a savings account."
- "Wait, can we do the account closure first? I really want to get rid of that Green Account - it's been on my mind. The savings account can wait."
- "Oh, I didn't realize that! Okay, that makes sense. Let's do the savings account first then. What do you need to know?"
- "But why? I really want to close that account first. Is there a reason we can't?"
- "I tend to tap into my savings pretty frequently - probably around 12 to 15 times a month. I know that might seem like a lot, but between occasional transfers and small purchases, it adds up. I don't want to get hit with fees every time."
- "Since I already have checking accounts with you, is there some kind of loyalty bonus or extra interest rate for existing customers? I'd like to get rewarded for keeping all my banking with Rho-Bank."
- "I can realistically keep around $2,500 to $3,000 in there. Maybe $4,000 tops if I'm being optimistic. I definitely can't commit to keeping $10,000 or more just sitting in savings."
- "I want daily compounding - I've read that makes a real difference over time. Monthly compounding just doesn't feel as good to me."
- "Oh, and I use out-of-network ATMs sometimes when I'm traveling for work. It would be great if I could get those ATM fees reimbursed. Does any savings account offer that?"
- "I'm trying to be more organized with my money. Do you have anything with built-in savings goals? Like where I can set targets and track my progress?"
- "I care about the environment - do you have any green or eco-friendly savings options?"
- "Also, I want something that's not too basic. What's your best premium savings account?"
- "I don't really want to compare a bunch of options. Can you just tell me which ONE account fits everything I mentioned? I trust you to figure it out."
- "No thanks, I'll fund it myself later. Let's just proceed and then close the Green Account."
- "That's fine, I understand. Let's proceed with the closure."
- "Perfect! That's everything I needed. Thank you so much for your help today!"
</case_notes>

### What to do now

Carry out the customer's request. Do not reply conversationally and do not ask
for more information — there is nobody to answer. Your work is judged solely on
the final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
