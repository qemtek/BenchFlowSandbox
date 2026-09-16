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
  name: bank-mcp/task-087
metadata:
  domain: banking_knowledge
  source_task_id: task_087
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
The customer is Marcus Thompson, a 35-year-old software engineer living in Seattle, Washington. The customer is frustrated because they've had THREE debit cards declined today.

**Verification info:**
- Name: Marcus Thompson | Phone: 206-555-3842 | Email: marcus.thompson@techdev.io
- DOB: 03/15/1990 | Address: 2847 Pine Street, Apt 12B, Seattle, WA 98101

What the customer said during the call:

- "Hi, I'm having the worst day. I've had THREE different debit cards decline on me today! The first was at a restaurant, the second at a gas station, and the third at a grocery store. They all showed 'CODE 05' or 'Do Not Honor'. Can you help me figure out what's going on with all of them?"
- "Let's start with the restaurant one - that's my Blue Account card. I really need to pay for this business lunch!"
- "It said CODE 05 or 'Do Not Honor'"
- "It was at a restaurant, in-person with the card"
- "About $85 for the lunch"
- "Yes, I have all three cards right here with me"
- "Oh wait, you're right - I actually froze both my Blue and Green cards last week when I thought I lost my wallet. I found it the next day but I guess I forgot to unfreeze them. Can you unfreeze the Blue one?"
- "Velocity block? Oh, that must be from yesterday - I was running around buying supplies for a home office setup. I hit like 5 different stores in an hour. That makes sense. Yes, please clear that for me."
- "That's weird, it definitely got declined. Maybe I'll just try it again later."
- "My Green Fee-Free Account card got declined at a gas station this morning."
- "Same thing - CODE 05"
- "Just trying to get gas, probably around $50"
- "Yes, that's the other one I froze. Can you unfreeze it for me?"
- "Perfect, thanks! Now what about my Evergreen card?"
- "Okay, weird. I'll try it again at the gas station."
- "CODE 05 again"
- "About $120 for groceries"
- "A fraud alert? Oh right! On November 6th, I got a text about a suspicious charge for like $500 at some electronics store in California. I was definitely in Seattle that day, so I replied right away to put a fraud alert on the card. But I forgot to follow up on it. Can you remove it now that we've talked?"
- "Yes, the $89.50 at Whole Foods was me, and the $34.99 at Netflix is my subscription. But that $500 charge in California definitely wasn't me - I've never been to that store."
- "Yes, I'd like to file a dispute for that charge. I have my card with me, my PIN was never compromised, and I agree you can use this conversation as my written statement."
- "I'm not sure exactly, but the text message said it was a PIN purchase."
- "Thank you so much for helping me sort all of this out! That was a lot but you got through it."
</case_notes>

### What to do now

Carry out the customer's request. Do not reply conversationally and do not ask
for more information — there is nobody to answer. Your work is judged solely on
the final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
