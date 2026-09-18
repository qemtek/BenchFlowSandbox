---
# Task config for every generated task. Edit this, then regenerate.
#
# The agent reaches the bank over MCP. The shell CLI arm was removed on
# 2026-09-17: two interfaces meant every experiment had to be run twice or
# caveated, and the levers worth studying here are skills, prompts, tools and
# model/harness choice — not transport.
schema_version: '1.3'
task:
  name: bank/task-086
metadata:
  briefing_prompt_uri: prompts:/bank-briefing/2
  domain: banking_knowledge
  source_task_id: task_086
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
The customer is Camila Reyes, a 42-year-old restaurant owner living in Phoenix, Arizona. The customer is stressed because they've discovered multiple issues across their debit cards.

**Verification info:**
- Name: Camila Reyes | Phone: 602-555-0847 | Email: camila.reyes@saboresdelsol.com
- DOB: 09/22/1983 | Address: 4725 Camelback Road, Phoenix, AZ 85018
- Work address: 1520 East McDowell Road, Phoenix, AZ 85006 (Sabores del Sol restaurant)

What the customer said during the call:

- "Hi, I need help with several disputed transactions. I've got problems on two of my debit cards - my Green Fee-Free card ending in 4738 and my Evergreen Account card ending in 9251. There are three issues on each card."
- "I withdrew $300 but the machine only gave me $200."
- "I ordered restaurant supplies but they never arrived."
- "I have no idea what this is - never signed up for any crypto service."
- "Wait, there's a limit? So I can't file all three right now?"
- "The ATM shortage and the supplies are more urgent. I can come back for the crypto charge later."
- "My receipt shows $89.50 but they charged $289.50 - overcharged by $200!"
- "I've never been to Miami! I was in Phoenix that whole week."
- "I deposited $500 in cash but only $300 was credited - missing $200!"
- "Hmm... Actually, I might be mixing it up with another deposit. If your records show that, then I'll go with what you have."
- "I understand. So my liability could be up to $500 since it's been over 2 days? That's still better than losing the full $625."
- "Oh right, I do have that other dispute from last week still open. I forgot about that one."
- "Yes, please replace it since the Miami charge is definitely fraud."
- "Can you send it to my restaurant instead? 1520 East McDowell Road, Phoenix, AZ 85006."
- "Just give me the best free options available for my tier."
- "Yes, you can use this conversation as my written statement."
- "Thanks for all that, I think I'm good for now."
</case_notes>

### What to do now

Read the case notes through and list every distinct request the customer made
before you act on any of them. A case often contains more than one, and you are
judged on all of them.

Then carry them out. Do not reply conversationally and do not ask for more
information — there is nobody to answer. Your work is judged solely on the
final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
