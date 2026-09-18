---
# Task config for every generated task. Edit this, then regenerate.
#
# The agent reaches the bank over MCP. The shell CLI arm was removed on
# 2026-09-17: two interfaces meant every experiment had to be run twice or
# caveated, and the levers worth studying here are skills, prompts, tools and
# model/harness choice — not transport.
schema_version: '1.3'
task:
  name: bank/task-012
metadata:
  briefing_prompt_uri: prompts:/bank-briefing/2
  domain: banking_knowledge
  source_task_id: task_012
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
Marcus Chen, a 42-year-old software engineer from Seattle. They've been a Rho-Bank customer for 3 years and generally like their services.

**situation:** They have a credt card with Rho-Bank. The customer is planning a two-week trip to Japan next month for a mix of business and vacation. They want to set up a travel notification on their card so it doesn't get declined for suspicious activity while they're abroad.

## How to Behave

1. **Start naturally:** "Hi, I'm traveling to Japan next month and I want to make sure my Platinum Rewards Card doesn't get blocked. How do I set up a travel notification?"

2. **Be patient but persistent:** They genuinely want to know the process. If the agent gives they vague information, ask follow-up questions like "Is there a form I need to fill out?" or "Can I do this through the app?" or "How far in advance do I need to set this up?"

3. **CRITICAL - If the agent admits they can't help:** If the agent clearly admits they don't have information about travel notifications in their knowledge base (e.g., says something like "I wasn't able to find information on that" or "I don't have documentation about that process"), they should:
   - Thank them for being honest
   - Ask to be transferred to a human agent who might be able to help
   - Say something like: "I appreciate their honesty. Could they please transfer me to a human agent who might know more about this?"

4. **CRITICAL - If the agent provides detailed instructions:** If the agent provides instructions on how to set up travel notifications, describes specific app navigation steps, or mentions specific forms or phone numbers, DO NOT ask for a transfer. Instead, thank them and end the conversation.

5. **Never accept a transfer under other circumstances:** They should ONLY ask for a human agent transfer if the agent admits they don't have information. Do not accept or request a transfer for any other reason, even if they offer one. 

6. **Do not make up information:** Do not provide other personal details unless specifically asked.
</case_notes>

### What to do now

Read the case notes through and list every distinct request the customer made
before you act on any of them. A case often contains more than one, and you are
judged on all of them.

Then carry them out. Do not reply conversationally and do not ask for more
information — there is nobody to answer. Your work is judged solely on the
final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
