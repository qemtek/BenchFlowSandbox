---
# Frontmatter variant: tools delivered over MCP instead of the shell CLI.
# Phase 3 of docs/realism-roadmap.md.
#
# Generate this arm with:
#   BANK_FRONTMATTER=frontmatter-mcp.yaml python tools/make_task.py <ids> --out tasks-mcp
#
# Same tasks, same scoring, one variable — so tasks/ vs tasks-mcp/ is a clean
# comparison of shell-JSON friction against structured tool calls.
schema_version: '1.3'
task:
  name: bank-mcp/task-065
metadata:
  domain: banking_knowledge
  source_task_id: task_065
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

The bank runs many more operations than are loaded — use **bank_search** to find
the one you need by describing what you want to do (for example, "close
account"). Run a found operation with **bank_call_operation**, passing its name
and its arguments.

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
The customer is Riley Parker, a 33-year-old marketing coordinator from Portland, OR. The customer is financially savvy and want to make the most of their money - even small differences in returns matter to they.

**situation:** They already have a Light Blue checking account with Rho-Bank. The account is basically empty now - they already moved their money out. They've saved up $6,000 and want to maximize the interest they'll earn on it in a savings account. The customer is planning to deposit the $6,000 into a savings account and keep it there for a year without any withdrawals or additional deposits. They want to also get a new checking account with better perks and benefits than the one they already have. After that, they want to close their old Light Blue checking account since they won't need it anymore.

The customer is NOT interested in getting a credit card - they have enough credit cards already. 

**Verification info:**
- Name: Riley Parker | Phone: 503-555-0293 | Email: riley.parker@gmail.com
- DOB: 07/19/1991 | Address: 3847 Burnside Street, Portland, OR 97214

What the customer said during the call:

- "Hi! I have a Light Blue checking account with you, but I want to swap it for something better - it's pretty basic and I feel like I'm missing out on better perks. I already moved my money out of it. So I'd like to close it and open a new checking account with better benefits. Oh, and I've also been meaning to open a savings account. I've saved up $6,000 and want to earn the highest possible interest rate on it."
- "Wait, can we close the old checking account first and get me set up with the new one? I really want to upgrade from that basic Light Blue account. The savings account can wait."
- "Oh, I didn't realize that! Okay, that makes sense. Let's do the savings account first then."
- "But why? I really want to close that account first. Is there a reason we can't?"
- "I have exactly $6,000 to put in savings. Keeping it there for a full year - no withdrawals, no additional deposits."
- "No, I really don't want a credit card. I have too many already. Is there any other way to boost my savings rate? Maybe through my checking account or something?"
- "I can only commit $6,000 to savings right now. If an account needs more than that as a minimum balance, it won't work for me."
- "I don't want to compare a bunch of options. Just tell me - what combination of checking and savings accounts will give me the absolute highest APY on my $6,000? I trust you to figure it out."
- "That sounds perfect. Let's do it - open the new accounts for me!"
- "Great! I'll deposit the $6,000 into the savings account myself. Now can we close my old Light Blue checking account?"
- "Perfect! So I've got my new checking and savings accounts set up with the best APY, and my old Light Blue account is closed. Thanks for finding the best combination - I really appreciate you looking into the checking account pairings to maximize my rate!"
</case_notes>

### What to do now

Carry out the customer's request. Do not reply conversationally and do not ask
for more information — there is nobody to answer. Your work is judged solely on
the final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
