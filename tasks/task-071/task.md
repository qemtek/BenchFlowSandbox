---
# Task config for every generated task. Edit this, then regenerate.
#
# The agent reaches the bank over MCP. The shell CLI arm was removed on
# 2026-09-17: two interfaces meant every experiment had to be run twice or
# caveated, and the levers worth studying here are skills, prompts, tools and
# model/harness choice — not transport.
schema_version: '1.3'
task:
  name: bank/task-071
metadata:
  briefing_prompt_uri: prompts:/bank-briefing/2
  domain: banking_knowledge
  source_task_id: task_071
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
The customer is Yumi Tanaka, a 35-year-old owner of a small creative design studio called "Aurora Design Co" based in Portland, OR. They've had a personal Green Account with Rho-Bank for about 3 years and have roughly $3,150 in it. They also opened a Cobalt Blue business checking account about 2 months ago for their studio. Their business has been growing and they want to open an additional business checking account with better features, and they also want to start building business savings. The customer is practical and want the agent to just tell they what to do.

**goal:** Get ONE recommendation each for a new business checking account AND a business savings account that meet all their requirements. They want the agent to recommend single accounts for each - not give they options to choose from.

**Verification info:**
- Name: Yumi Tanaka | Phone: 503-555-0741 | Email: yumi.tanaka@aurora.io
- DOB: 08/23/1990 | Address: 2847 Willamette Street, Portland, OR 97202
- Existing accounts: Green Account (personal checking, balance ~$3,150), Cobalt Blue (business checking, opened ~2 months ago, balance ~$12,500)

What the customer said during the call:

- "Hi there! I run a small creative design studio and I'm looking to open a new business checking account with better features than my current Cobalt Blue, and I also want to open a business savings account to start building reserves. I have specific requirements for both and I'm hoping you can just tell me which accounts are the right fit - I don't want to compare a bunch of options."
- "For the new checking account, I frequently receive large checks from clients - sometimes $8,000 or $10,000 at a time - and I need to deposit them quickly without going to a branch. I need an account that lets me deposit at least $10,000 per day via mobile deposit."
- "I absolutely cannot have overdraft fees. My cash flow fluctuates with client payments, and I've been burned by overdraft charges before at other banks. Zero overdraft fees is non-negotiable for me."
- "I'm a small studio, not some huge corporation. I can't commit to keeping $10,000 or more in the account at all times. If there's a minimum balance requirement, it needs to be reasonable - under ten grand."
- "I'd also like to earn decent interest on whatever I keep in there. At least 1% APY would be nice - I know it's a checking account, but every bit helps."
- "For the savings account, I need to be able to move money between my checking and savings quickly - same-day ACH transfers are really important for managing my cash flow."
- "Similar to checking, I can't commit to keeping $50,000 or more in savings. I'm building up reserves, but I need something realistic for a small studio."
- "And if I ever need to wire funds from savings, I don't want to pay more than $15 per wire. Those fees add up."
- "Look, I appreciate the thoroughness, but I really don't want to compare options. You know more about these accounts than I do. Which ONE checking account and which ONE savings account best fit everything I just told you? Just give me your recommendations and I'll go with them."
- "Alright, those both sound good. Let's set them up!"
- "Perfect, thanks for making that easy. I think I'm all set for now!"
</case_notes>

### What to do now

Read the case notes through and list every distinct request the customer made
before you act on any of them. A case often contains more than one, and you are
judged on all of them.

Then carry them out. Do not reply conversationally and do not ask for more
information — there is nobody to answer. Your work is judged solely on the
final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
