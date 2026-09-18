---
# Task config for every generated task. Edit this, then regenerate.
#
# The agent reaches the bank over MCP. The shell CLI arm was removed on
# 2026-09-17: two interfaces meant every experiment had to be run twice or
# caveated, and the levers worth studying here are skills, prompts, tools and
# model/harness choice — not transport.
schema_version: '1.3'
task:
  name: bank/task-082
metadata:
  briefing_prompt_uri: prompts:/bank-briefing/3
  domain: banking_knowledge
  source_task_id: task_082
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
The customer is Marcus Chen, a 41-year-old small business owner living in Seattle, Washington. They run a coffee equipment supply company and have been a Rho-Bank customer for years. The customer is meticulous with finances and review their bank statements weekly.

**situation:** During their weekly statement review, they discovered FOUR suspicious transactions across TWO of their debit cards. 

**Verification info:**
- Name: Marcus Chen | Phone: 206-555-0892 | Email: marcus.chen@seattlebrew.com
- DOB: 03/22/1984 | Address: 1847 Pine Street, Seattle, WA 98101

**YOUR TWO DEBIT CARDS:**
1. Blue Account debit card - They LOST this card 3 days ago but haven't reported it yet
2. Green Fee-Free Account debit card - They still have this card

What the customer said during the call:

- "Hi, I need to speak to a human agent. I reviewed my bank statements today and found four transactions I need to dispute - two on each of my debit cards. Some are unauthorized transactions I never made, one is an ATM error, and one is a subscription that won't stop charging me even after I cancelled."
- "The most concerning one is on my Blue Account card ending in 4827 - I actually lost that card about 3 days ago but hadn't gotten around to reporting it yet. Today I see there's a $347.50 charge at ElectroniX Outlet from November 7th that I definitely didn't make. This is completely unauthorized - I never authorized this transaction."
- "This is embarrassing, but yes, I had my PIN written on a sticky note in my wallet. So whoever has the card probably has the PIN too."
- "No, I don't have the card anymore - it was in my wallet that I lost."
- "No, I haven't contacted them - I don't even know who they are."
- "On that same Blue Account card, there's also a $89.99 charge from FitLife Premium on November 10th. I cancelled that gym membership back in October but they charged me anyway. I called them on November 11th and they said no refunds. Important detail: this charge happened on November 10th, but I didn't lose my card until November 11th or 12th. So I still had the card when FitLife charged me - it was just an automatic recurring charge, no PIN involved."
- "On my Green Fee-Free Account card ending in 7391, I used the Rho-Bank ATM - machine 2847 - on November 9th. I requested $200 but only got $100 in cash. The receipt says $200 though. I noticed right away but wasn't sure what to do."
- "Also on that Green Fee-Free card, there's a charge for $523.17 from something called CryptoGems Store on November 12th. I've never heard of this place and I definitely didn't buy anything from them. This is the biggest charge and it's really worrying me."
- "I still have the card - this must have been someone who got my card number somehow."
- "I haven't filed one yet, but yes, I can file a police report if that would help. It's a lot of money."
- "That card needs to be cancelled anyway since I lost it. Please issue a new one."
- "I'd like to keep using this card but maybe with a new number? Can you reissue it?"
- "I discovered it today, November 14th."
- "I saw the charge on November 11th when I called them to complain."
- "I noticed immediately on November 9th when the cash came out short."
- "I discovered this one today, January 9th."
- "I understand - so since I'm reporting within a few days, I should be protected, right? What about the ATM one since I noticed right away?"
- "That would be really helpful - especially for the bigger amounts. How does that work exactly?"
- "Yes, absolutely. You can use this conversation as my written statement."
</case_notes>

### What to do now

Read the case notes through and list every distinct request the customer made
before you act on any of them. A case often contains more than one, and you are
judged on all of them.

Then carry them out. Do not reply conversationally and do not ask for more
information — there is nobody to answer. Your work is judged solely on the
final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
