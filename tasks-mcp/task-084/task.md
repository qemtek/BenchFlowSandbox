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
  name: bank-mcp/task-084
metadata:
  domain: banking_knowledge
  source_task_id: task_084
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
The customer is Valeria Montes, a 34-year-old accountant living in Chicago, Illinois. The customer is very organized and catch discrepancies quickly.

**situation:** They've discovered FOUR problematic transactions across their TWO debit cards that they need to dispute. 

**Verification info:**
- Name: Valeria Montes | Phone: 312-555-7294 | Email: valeria.montes@finmail.com
- DOB: 06/18/1991 | Address: 4521 Lakeview Drive, Chicago, IL 60614

**YOUR TWO DEBIT CARDS:**
1. Evergreen Account debit card 
2. Light Blue Account debit card

What the customer said during the call:

- "Hi, I need to file several disputes on my debit cards."
- "On my Evergreen Account card ending in 3847, there's a duplicate charge from Bella's Bistro."
- "On November 6th, I bought lunch there for $47.50. But I see the exact same charge twice on my statement!"
- "I only ate there once. This is definitely a duplicate."
- "No, I haven't contacted them yet. Should I?"
- "Yes, I used my PIN - it was a PIN transaction."
- "I noticed it on November 10th when reviewing my statement."
- "Also on my Evergreen card, I was overcharged at Whole Foods on November 8th."
- "I bought $89.23 worth of groceries - I have the receipt right here. But my statement shows $189.23!"
- "They charged me exactly $100 more than they should have."
- "This was a signature transaction - I signed the receipt."
- "Yes, I called Whole Foods on November 9th. They said they'd 'look into it' but I haven't heard back."
- "I noticed it November 9th, the day after."
- "On my Light Blue Account card ending in 6129, there's a $275 EveryonePay transfer on November 11th."
- "It says it went to someone called 'Jake'. I have NO idea who that is."
- "I still have my card - someone must have gotten my card number."
- "I saw it today, November 14th."
- "I have no idea how they could have gotten my info. I don't know."
- "There's also an older charge I just discovered on the Light Blue card."
- "On October 5th, there's a $412.88 charge at TechWorld Electronics in Miami."
- "I was in Chicago that whole week! I definitely didn't make this purchase."
- "I know I'm reporting this late - I was doing my year-end financial review and just caught it today."
- "I understand there might be liability implications since it's been over a month."
- "I just discovered it today, November 14th."
- "No, I haven't filed one yet. Should I for this amount?"
- "It looks like it was an in-person purchase at a physical store - someone must have used my card with a PIN."
- "Oh, I do have that other dispute from last week still open. I didn't realize there was a limit."
- "So I can only file one more dispute on that account right now?"
- "The older TechWorld charge is for more money - let's prioritize that one. The EveryonePay one can wait, or maybe I can file it once my other dispute closes?"
- "The card is fine, these are merchant errors not card problems."
- "Should I get the card replaced since there's fraud on it?"
- "I understand. So for the TechWorld charge, my liability could be up to $500 since I'm reporting it after the 2-day window? That's still better than losing the full $412."
- "Yes, absolutely. You can use this conversation as my written statement."
- "Thank you for handling all of this. I'll wait to file the EveryonePay dispute once my other one closes."
</case_notes>

### What to do now

Carry out the customer's request. Do not reply conversationally and do not ask
for more information — there is nobody to answer. Your work is judged solely on
the final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
