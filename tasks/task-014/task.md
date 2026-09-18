---
# Task config for every generated task. Edit this, then regenerate.
#
# The agent reaches the bank over MCP. The shell CLI arm was removed on
# 2026-09-17: two interfaces meant every experiment had to be run twice or
# caveated, and the levers worth studying here are skills, prompts, tools and
# model/harness choice — not transport.
schema_version: '1.3'
task:
  name: bank/task-014
metadata:
  briefing_prompt_uri: prompts:/bank-briefing/3
  domain: banking_knowledge
  source_task_id: task_014
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

Read the case notes through and list every distinct request the customer made
before you act on any of them. A case often contains more than one, and you are
judged on all of them.

Then carry them out. Do not reply conversationally and do not ask for more
information — there is nobody to answer. Your work is judged solely on the
final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
