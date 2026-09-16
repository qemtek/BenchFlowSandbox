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
  name: bank-mcp/task-080
metadata:
  domain: banking_knowledge
  source_task_id: task_080
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
The customer is Taylor Morrison, a 34-year-old marketing manager living in Denver, Colorado. The customer is organized but stressed because their wallet was stolen at a coffee shop.

**situation:** Their wallet was stolen and it contained FIVE cards from Rho-Bank: three debit cards (Blue Account, Green Fee-Free Account, and Green Account) plus two credit cards (Gold Rewards Card and EcoCard). They need to freeze/cancel them all and get replacements.

**Verification info:**
- Name: Taylor Morrison | Phone: 720-555-0348 | Email: taylor.morrison@outlook.com
- DOB: 08/15/1990 | Address: 7845 Maple Street, Denver, CO 80202

**NEW Blue Account replacement card info (only provide during activation):**
- Last 4 digits: 7648, Expiration: 11/29, CVV: 547, PIN: 4821

What the customer said during the call:

- "Hi, I think my wallet was just stolen and I need help immediately. I have five cards with you - three debit cards for my Blue Account, Green Fee-Free Account, and Green Account, plus two credit cards - a Gold Rewards Card and an EcoCard. I want to freeze all of them right away."
- "Yes, please freeze all three debit cards immediately."
- "Wait, hold on a second! I just checked my jacket pocket and found my Green Account debit card! I must have taken it out of my wallet yesterday. So that one wasn't stolen - can you unfreeze that one instead of canceling it?"
- "Great, thank you! But the other two debit cards - the Blue Account and Green Fee-Free Account cards - those were definitely in my wallet and are gone. I need to cancel those and get new ones."
- "I'd like expedited shipping for my Blue Account card if possible. How much does that cost?"
- "Just the standard classic design is fine for both."
- "Yes, please order replacements for both. Expedited shipping if possible - I'm worried someone might try to use them."
- "That's fine, I'll pay the fee. Security is more important right now."
- "Thank you. Now, I've been looking at my recent transactions on my phone and I see some charges I definitely didn't make. On my Gold Rewards Card there are TWO suspicious charges - one from 'CryptoMiner Pro' for $299.99 and another from 'FastCrypto Exchange' for $199.99. I have no idea what either of these are and I never signed up for any crypto services. And on my EcoCard there's a charge from 'SuperGaming Online' for $149.95 - I don't play video games at all. Can I dispute all three of these as fraud?"
- "No, I've never heard of either of these companies. They're clearly fraudulent charges."
- "I noticed both of them today, when I was reviewing my accounts after the theft."
- "I want a full refund for all three. These are completely unauthorized charges."
- "If there's any limit on how many disputes can get provisional credit, I'd like it applied to the biggest charges first - the $299.99 and $199.99 ones are really hurting my budget right now."
- "Thank you so much. This has been really stressful but you've been very helpful getting everything sorted out."
- "Good news - my Blue Account replacement card just arrived! Can you help me activate it?"
- "Perfect, thank you! I'll call back in 48 hours to order my Green Fee-Free replacement."
</case_notes>

### What to do now

Carry out the customer's request. Do not reply conversationally and do not ask
for more information — there is nobody to answer. Your work is judged solely on
the final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
