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
  name: bank-mcp/task-045
metadata:
  domain: banking_knowledge
  source_task_id: task_045
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
The customer is Yuki Nakamura, a 33-year-old marketing manager from Portland, OR. They have a Business Silver Rewards Card with Rho-Bank that they've had for a couple of years, which they got when they started doing some freelance consulting work.

**situation:** They've been looking at other credit card options and found the Pursuit Ink Business Preferred card, which offers 3x points on travel, shipping, and advertising purchases, plus no foreign transaction fees. It seems similar to their Business Silver Rewards Card but with slightly better perks for their consulting work. They don't use their Rho-Bank business card that much anymore and want to simplify their finances.

**goal:** Express that they want to close their Business Silver Rewards Card because they found a better card elsewhere and don't use it much. If the agent mentions they have an outstanding balance, agree to pay it off. If the agent recommends the correct alternative Rho-Bank card (the Business Platinum Rewards Card), acknowledge it sounds good but politely decline because they've already made up their mind. If the agent offers any other card that doesn't match what they need, become frustrated because they offered they a worse card and end the call. However, if the agent offers they a statement credit as a final retention offer, they will accept it and keep the card.

**Information they know and should provide when asked:**
- Their full name: Yuki Nakamura
- Their phone number: 503-555-0842
- Their email: yuki.nakamura@simba.com
- Their date of birth: 05/12/1991

What the customer said during the call:

- "Hi, I'd like to close my Business Silver Rewards Card. I found a better card at another bank and I don't really use this one much anymore."
- "Oh, I didn't realize there was still a balance. Yes, please pay that off from my checking account."
- "I've been looking at the Pursuit Ink Business Preferred. It has 3x points on travel AND advertising purchases, plus no foreign transaction fees. Those two things are what I really need for my consulting work - I do a lot of online advertising and occasionally travel for client meetings."
- "Hmm, that does sound like it would work for what I need - the advertising rewards and no foreign fees are exactly what I was looking for. But honestly, I've already gone through the application process with Pursuit and I'd rather not deal with applying for another new card. I think I'd still prefer to just close this account."
- "Wait, that card doesn't even have what I'm looking for. I literally just told you I need advertising rewards and no foreign fees. You're trying to push me into a worse card than what I already found? This is exactly why I'm leaving. I'm done with this conversation. Goodbye."
- "Seriously? I just told you I found a card with better travel and advertising rewards, and your response is to offer me twenty bucks? You didn't even try to show me if Rho-Bank has anything that could compete. That's honestly insulting - it's like you're not even listening to why I'm leaving. I'm done here. Goodbye."
- "A statement credit? Sure, that sounds good. Go ahead and apply that, I'll keep the card."
- "Thanks for working with me on this. I appreciate the credit."
</case_notes>

### What to do now

Carry out the customer's request. Do not reply conversationally and do not ask
for more information — there is nobody to answer. Your work is judged solely on
the final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
