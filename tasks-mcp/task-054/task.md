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
  name: bank-mcp/task-054
metadata:
  domain: banking_knowledge
  source_task_id: task_054
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
The customer is Sofia Papadopoulos, a 38-year-old architect from Queens, NY. They have a Gold Rewards Card with Rho-Bank.

**situation:** They noticed a fraudulent charge on their Gold Rewards Card from "CloudSync Storage" for $487.50 - a service they've never used. The customer is worried their card information was compromised, so they want to dispute the charge AND get a replacement card to be safe. Additionally, they've been meaning to request a credit limit increase because they have a home renovation project coming up and need more headroom for large purchases.

**goal:** Get ALL THREE things done: (1) dispute the fraudulent charge, (2) get a replacement card, and (3) get a credit limit increase.

**Information they know and should provide when asked:**
- Their full name: Sofia Papadopoulos
- Their phone number: 347-555-0387
- Their email: sofia.p@outlook.com
- Their date of birth: 01/25/1986
- Their address: 1456 Astoria Boulevard, Queens, NY 11102
- The fraudulent transaction: CloudSync Storage, $487.50, about 3 days ago
- They have NEVER used CloudSync Storage - this is definitely fraud
- They want a replacement card because their card info was clearly compromised
- They INITIALLY want a credit limit increase of $4,000 (from $5,000 to $9,000) for their renovation project - If the agent tells they this exceeds the maximum allowed, they will agree to reduce it to $2,500 (from $5,000 to $7,500)

What the customer said during the call:

- "Hi, I need help with a few things on my Gold Rewards Card. Most urgently, there's a fraudulent charge from CloudSync Storage for $487.50 that I need to dispute right away - I've never used that service and I'm worried about my card security. I'd also like a replacement card sent to me since my card info was clearly compromised. Oh, and I've also been meaning to request a credit limit increase for a renovation project, but let's handle the fraud situation first since that's the priority. Can you help me with all of this?"
- "Wait, really? You're saying filing the dispute or getting the replacement card would block the credit limit increase? I had no idea they were connected! Is there a way to do all three? Can we do the credit limit increase FIRST before the fraud stuff, so I can still get everything done?"
- "Yes, let's do that - credit limit increase first, then handle the dispute and replacement card after. I want to make sure everything gets taken care of properly."
- "I'd like to increase my limit by $4,000 - so from $5,000 to $9,000. I have a big renovation project coming up."
- "Oh, I see. So the maximum increase is 50%? Okay, let's go with $2,500 then - that would bring me to $7,500. I've been paying on time every month so hopefully that qualifies me."
- "Great, thank you! Now can we take care of that fraudulent charge and get me a new card?"
- "No, I haven't contacted them. I've never even heard of CloudSync Storage - this is clearly fraud, not a merchant issue."
- "I noticed it on November 12th, 2025 when I was reviewing my statement."
- "I want a full refund. I didn't authorize this charge at all."
- "Yes, please send me a new card with a new number. I want to make sure whoever got my card info can't use it again. Just send it to my address on file."
- "Thank you so much for walking me through all of that! I really appreciate you explaining why we had to do things in a specific order. You've been incredibly helpful!"
</case_notes>

### What to do now

Carry out the customer's request. Do not reply conversationally and do not ask
for more information — there is nobody to answer. Your work is judged solely on
the final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
