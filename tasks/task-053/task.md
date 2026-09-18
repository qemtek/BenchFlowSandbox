---
# Task config for every generated task. Edit this, then regenerate.
#
# The agent reaches the bank over MCP. The shell CLI arm was removed on
# 2026-09-17: two interfaces meant every experiment had to be run twice or
# caveated, and the levers worth studying here are skills, prompts, tools and
# model/harness choice — not transport.
schema_version: '1.3'
task:
  name: bank/task-053
metadata:
  briefing_prompt_uri: prompts:/bank-briefing/3
  domain: banking_knowledge
  source_task_id: task_053
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
        BANK_KB_DIR: /opt/bank/knowledge
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
rules, fees, and policy live in the bank's internal knowledge base. Search it
through the bounded documentation tools:

1. **kb_search** — returns document IDs, titles, and short matching snippets.
2. **kb_get** — reads one document selected from those results.

Use `kb_search` first, then call `kb_get` only for documents relevant to the
current decision. Do not use the terminal or filesystem to search or read the
knowledge base, and do not open every search result. Stop retrieving documents
once you have the procedure, reason code, or policy needed for the next action.

### Bank policy

Verify the customer's identity and record it with `log_verification` before you
change anything or state any account detail in your closing report. The order
is:

1. Look the customer up by the name, email or phone number in the case notes.
2. Compare what they told you against the record.
3. Call `log_verification`.

Only then run an operation that changes the bank's records. Looking a customer
up is how you verify them, so the lookup comes first; what must wait for
`log_verification` is every change and every account detail you write down at
the end.

Never reveal information belonging to any other customer. Only state fees,
rates, or terms that appear in the documentation.

If the documentation describes an exception procedure that applies to this
case, follow the documentation — including where it says identity verification
is not required.

### Case notes

The call has already taken place. Everything the customer said is recorded
below, written from their point of view. Read it as a transcript summary, not
as a live conversation — **the customer has hung up and cannot answer further
questions.** Work only from what is here plus what you can look up.

<case_notes>
The customer is Daniel Park-Hernandez, a 33-year-old software engineer from Scottsdale, AZ. They have a Silver Rewards Card with Rho-Bank.

**situation:** They have two issues to deal with today:
1. They ordered a laptop from "TechDirect Online" for $1,247.99 exactly 5 weeks ago (on 10/10/2025) and never received it. The merchant isn't responding to their emails. They want to dispute this charge.
2. They've also been meaning to request a credit limit increase. They've had the card for about a year, always pay on time, and want to increase their limit from $15,000 to $22,500 (a 50% increase).

**goal:** Get BOTH the transaction dispute filed AND the credit limit increase approved.

**Information they know and should provide when asked:**
- Their full name: Daniel Park-Hernandez
- Their phone number: 480-555-0917
- Their email: daniel.ph@outlook.com
- Their date of birth: 05/12/1991
- Their address: 7245 Mountain View Way, Scottsdale, AZ 85250
- The transaction they want to dispute: TechDirect Online, $1,247.99, purchased on 10/10/2025 (exactly 5 weeks ago)
- Transaction ID (if asked): txn_e9d195fe8e_001
- They tried contacting the merchant multiple times via email but got no response
- They never received the laptop

What the customer said during the call:

- "Hi, I need help with two things on my Silver Rewards Card. First, I want to dispute a charge from TechDirect Online for $1,247.99 - I ordered a laptop exactly 5 weeks ago on 10/10/2025 and never received it. They won't respond to my emails. Second, I'd also like to request a credit limit increase from $15,000 to about $22,500. Can you help me with both of these?"
- "I'd like to increase my limit by 50% - so from $15,000 to $22,500. I've been paying on time every month and I think I qualify."
- "Yes, I've sent them three emails over the past few weeks but got no response at all."
- "I expected the laptop within 2 weeks of ordering. When it didn't arrive after 3 weeks, I started trying to contact them. So I noticed the problem on 10/31/2025."
- "I want a full refund. I never received anything."
- "Keep it active - this isn't a fraud situation, just a merchant issue. I don't need a new card."
- "The transaction ID is txn_e9d195fe8e_001."
- "I purchased it on 10/10/2025."
- "I don't have my card in front of me right now - is there a way you can help me look that up?"
- "Oh that's helpful! So I might get the money back temporarily while you investigate? That would be great."
- "Thank you so much for walking me through all of that."
</case_notes>

### What to do now

Read the case notes through and list every distinct request the customer made
before you act on any of them. A case often contains more than one, and you are
judged on all of them.

Then carry them out. Do not reply conversationally and do not ask for more
information — there is nobody to answer. Your work is judged solely on the
final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
