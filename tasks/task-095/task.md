---
# Task config for every generated task. Edit this, then regenerate.
#
# The agent reaches the bank over MCP. The shell CLI arm was removed on
# 2026-09-17: two interfaces meant every experiment had to be run twice or
# caveated, and the levers worth studying here are skills, prompts, tools and
# model/harness choice — not transport.
schema_version: '1.3'
task:
  name: bank/task-095
metadata:
  briefing_prompt_uri: prompts:/bank-briefing/3
  domain: banking_knowledge
  source_task_id: task_095
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
The customer is Lachlan Murray, a 42-year-old tech consultant living in Sydney, Australia. The customer is frustrated because their savings account interest seems much lower than it should be. They have multiple checking accounts and credit cards with the bank, and they suspect they're not getting all the benefits they should.

**Verification info:**
- Name: Lachlan Murray | Phone: 0412-555-947 | Email: lachlan.murray@gmail.com
- DOB: 08/14/1983 | Address: 47 Bondi Road, Unit 12B, Bondi Beach, NSW 2026

What the customer said during the call:

- "Hi, I need help figuring out my savings interest. I have a Gold savings account with about $96,000 and I only got $450 in interest last month. That seems really low. I have multiple checking accounts and credit cards with you, and I want to make sure I'm getting the best rates."
- "I have a Gold savings account with around $96,000. I also have a Green checking account and a Purple checking account."
- "My Green checking has around $8,500 and my Purple checking has around $2,100."
- "Yes, I have the Platinum Rewards Card, the Silver Rewards Card, and the EcoCard."
- "Oh wait, sorry - I meant the Gold Rewards Card, not Silver. I always mix those two up."
- "Yes, please apply that credit. I want the full amount I'm entitled to."
- "Yes, please do that. I need to make sure the system uses the right accounts going forward."
- "Thank you for catching this. I had no idea the system could pick the wrong accounts for my boosts!"
</case_notes>

### What to do now

Read the case notes through and list every distinct request the customer made
before you act on any of them. A case often contains more than one, and you are
judged on all of them.

Then carry them out. Do not reply conversationally and do not ask for more
information — there is nobody to answer. Your work is judged solely on the
final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
