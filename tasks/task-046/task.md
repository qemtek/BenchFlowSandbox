---
# Task config for every generated task. Edit this, then regenerate.
#
# The agent reaches the bank over MCP. The shell CLI arm was removed on
# 2026-09-17: two interfaces meant every experiment had to be run twice or
# caveated, and the levers worth studying here are skills, prompts, tools and
# model/harness choice — not transport.
schema_version: '1.3'
task:
  name: bank/task-046
metadata:
  briefing_prompt_uri: prompts:/bank-briefing/3
  domain: banking_knowledge
  source_task_id: task_046
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
The customer is Yuki Nakamura, a 33-year-old marketing manager from Portland, OR. They have a Business Silver Rewards Card with Rho-Bank that they've had for a couple of years, which they got when they started doing some freelance consulting work.

**situation:** They've been looking at other credit card options and found the Pursuit Ink Business Preferred card, which offers 3x points on travel, shipping, and advertising purchases, plus no foreign transaction fees. It seems similar to their Business Silver Rewards Card but with slightly better perks for their consulting work. They don't use their Rho-Bank business card that much anymore and want to simplify their finances.

**goal:** Express that they want to close their Business Silver Rewards Card because they found a better card elsewhere and don't use it much. If the agent mentions they have an outstanding balance, agree to pay it off. If the agent recommends the correct alternative Rho-Bank card (the Business Platinum Rewards Card), acknowledge it sounds good but politely decline because they've already made up their mind. If the agent offers any other card that doesn't match what they need, become frustrated because they offered they a worse card and end the call. However, if the agent offers they a statement credit as a final retention offer, they will accept it and keep the card.

**Information they know and should provide when asked:**
- Their full name: Yuki Nakamura
- Their phone number: 503-555-0842
- Their email: yuki.nakamura@simba.com
- Their date of birth: 05/12/1991

What the customer said during the call:

- "Hi, I'd like to close my Business Silver Rewards Card. I found a better card at another bank and I don't really use this one much anymore. Just so you know, I don't have any pending disputes or replacement cards on the way, so I should be good to close it."
- "Oh, I didn't realize there was still a balance. Yes, please pay that off from my checking account."
- "Oh really? I completely forgot about that. So I have to wait for that to be resolved before I can close the card? Okay, I understand. I'll wait until the dispute is resolved and then come back. Thanks for letting me know."
- "I've been looking at the Pursuit Ink Business Preferred. It has 3x points on travel AND advertising purchases, plus no foreign transaction fees. Those two things are what I really need for my consulting work - I do a lot of online advertising and occasionally travel for client meetings."
- "Hmm, that does sound like it would work for what I need - the advertising rewards and no foreign fees are exactly what I was looking for. But honestly, I've already gone through the application process with Pursuit and I'd rather not deal with applying for another new card. I think I'd still prefer to just close this account."
- "Wait, that card doesn't even have what I'm looking for. I literally just told you I need advertising rewards and no foreign fees. You're trying to push me into a worse card than what I already found? This is exactly why I'm leaving. I'm done with this conversation. Goodbye."
- "Seriously? I just told you I found a card with better travel and advertising rewards, and your response is to offer me twenty bucks? You didn't even try to show me if Rho-Bank has anything that could compete. That's honestly insulting - it's like you're not even listening to why I'm leaving. I'm done here. Goodbye."
- "A statement credit? Sure, that sounds good. Go ahead and apply that, I'll keep the card."
- "Thanks for working with me on this. I appreciate the credit."
</case_notes>

### What to do now

Read the case notes through and list every distinct request the customer made
before you act on any of them. A case often contains more than one, and you are
judged on all of them.

Then carry them out. Do not reply conversationally and do not ask for more
information — there is nobody to answer. Your work is judged solely on the
final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
