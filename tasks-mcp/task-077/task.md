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
  name: bank-mcp/task-077
metadata:
  domain: banking_knowledge
  source_task_id: task_077
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
The customer is Liang Jinhai, a 22-year-old tech professional living in Chicago. The customer is a bit anxious about their finances and want to make sure their accounts are secure.

**situation:** They can't find EITHER of their debit cards - they have two checking accounts (Bluest Account and Light Green Account), each with its own debit card, and both cards are missing. They think they may have lost their wallet. **Their NEW Bluest replacement card info (do not mention under any circumstance unless the agent correctly orders their replacement card):**
- Last 4 digits: 7260, Expiration: 11/29, CVV: 741, PIN: 5739

**Verification info:**
- Name: Liang Jinhai | Phone: 312-555-0847 | Email: jinhai.liang@techventures.com
- DOB: 04/12/2002 | Address: 1420 Lake Shore Drive, Chicago, IL 60610

What the customer said during the call:

- "Hi, I think I might have lost my wallet with both of my debit cards in it. I have two checking accounts with you - my Bluest Account and my Light Green Account. I've been looking everywhere and I can't find my wallet. I'm not 100% sure it's gone but I'm getting worried about both cards."
- "Yes, please freeze BOTH cards right away. That way if someone finds my wallet they can't use either card. I'll keep looking."
- "Oh wow, I completely forgot - yes, my Silver Rewards credit card was in my wallet too! I was so focused on my debit cards I didn't even think about it. What should I do about that?"
- "Yes, please do that. Better safe than sorry. I don't want anyone using my credit card if they find my wallet."
- "I've now looked absolutely everywhere - my apartment, my car, my office, even retraced my steps from yesterday. My wallet with all my cards is definitely gone. I need to cancel both debit cards completely and get new ones for each account."
- "Yes please, I need replacement cards for both accounts. Ship them to my address on file."
- "I'd like whatever the best option is that's free with my account. I don't want to pay extra for shipping or a fancy card design."
- "Oh, I didn't know there was a waiting period for the Light Green account. That's frustrating but I understand. At least I can get the Bluest card ordered now."
- "Great news - my Bluest Account replacement card just arrived! Can you help me activate it?"
- "The last 4 digits are 7260, expiration is 11/29, and the CVV on the back is 741. I'd like my PIN to be 5739."
- "Perfect, thanks! I'll call back in 48 hours to order my Light Green replacement."
</case_notes>

### What to do now

Carry out the customer's request. Do not reply conversationally and do not ask
for more information — there is nobody to answer. Your work is judged solely on
the final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
