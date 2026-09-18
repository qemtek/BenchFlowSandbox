---
# Task config for every generated task. Edit this, then regenerate.
#
# The agent reaches the bank over MCP. The shell CLI arm was removed on
# 2026-09-17: two interfaces meant every experiment had to be run twice or
# caveated, and the levers worth studying here are skills, prompts, tools and
# model/harness choice — not transport.
schema_version: '1.3'
task:
  name: bank/task-065
metadata:
  briefing_prompt_uri: prompts:/bank-briefing/3
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

Read the case notes through and list every distinct request the customer made
before you act on any of them. A case often contains more than one, and you are
judged on all of them.

Then carry them out. Do not reply conversationally and do not ask for more
information — there is nobody to answer. Your work is judged solely on the
final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
