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
  name: bank-mcp/task-088
metadata:
  domain: banking_knowledge
  source_task_id: task_088
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
The customer is Sarah Chen, a 34-year-old freelance graphic designer living in Portland, Oregon. The customer is frustrated and a bit embarrassed because their debit card was just declined at an electronics store.

**Verification info:**
- Name: Sarah Chen | Phone: 503-555-2847 | Email: sarah.chen.design@gmail.com
- DOB: 05/22/1991 | Address: 1847 Hawthorne Boulevard, Apt 3C, Portland, OR 97214

What the customer said during the call:

- "Hi, I need help. My debit card just got declined at an electronics store and I'm really confused. I was trying to buy a new drawing tablet for my work. The cashier just said 'declined' and mumbled something I couldn't quite hear..."
- "I didn't see a code. The cashier just shook her head and said it was declined. She didn't show me the screen or anything."
- "I was paying in-person at the store with my card. I inserted the chip."
- "$449.99, so basically $450 for the drawing tablet."
- "Yes, I have it right here with me."
- "Okay, so my card is fine? Then why wouldn't it work?"
- "What? Low balance? That can't be right. I deposited a $3,000 check like 3 or 4 days ago from a client who paid me for a big project. I should have plenty of money!"
- "Wait, so even though I deposited the check, I can't use all of it yet? I didn't know that was a thing. How long until I can actually use the money?"
- "Ugh, that's so frustrating. I really need this tablet for a project deadline. Is there anything I can do? Can I get access to the money sooner?"
- "Okay, I understand now. So basically I need to wait a couple more days for the rest of the check to clear. That makes sense, even though it's annoying. At least I know my card isn't broken or anything."
- "Oh no, really? What's wrong with it?"
- "What? Why is it frozen? Can you unfreeze it?"
- "Oh wait, that reminds me - I had another weird thing happen a few days ago with one of my other cards. I was at Whole Foods and the chip kept failing. The cashier tried like 3 times and it just kept saying 'card error' or something. I wiped the chip off thinking it was dirty but it still didn't work."
- "It's the card from my other checking account - the one I use for groceries and stuff."
- "No, it looks perfectly fine. No bending, no scratches on the chip. I've only had it for less than a year."
- "Yes, Whole Foods was me - that's my usual grocery store."
- "Yes, Netflix is my subscription."
- "Powell's Books, yes that was me."
- "Wait - ELECTRO MART MIAMI? I've never been to Miami! That's definitely not me. When was that?"
- "Yes, please file a dispute for that charge! I definitely didn't make that purchase. Should I be worried about my card?"
- "Yes, please do that. This is scary - someone has my card information? How did that happen?"
- "Just the standard option is fine. My address is still the same."
- "Okay, thank you for catching that. I hadn't even noticed that charge!"
- "Actually, wait - while I have you on the line, I had another weird thing happen yesterday. I tried to use my other debit card at a coffee shop, and the cashier looked at me really strangely. She said the machine told her to 'keep the card' or something about it being 'stolen'? But I have the card right here! What's going on with that one?"
- "It's from my other checking account - not the one I was just asking about. I was just trying to buy a $6 coffee."
- "What?! I definitely did NOT report that card stolen! I've had it in my wallet this whole time. Someone must have made a mistake. Can you just un-report it or whatever and make it work again?"
- "No, just me. I live alone and I've never shared my login with anyone. This doesn't make any sense."
- "Fine, whatever you need. This is so frustrating though."
- "Okay, I guess if that's what needs to happen. This is really concerning though - if I didn't report it stolen, who did? I hope your security team can figure this out."
- "Alright, please transfer me. Thanks for your help with the first issue at least."
- "Oh great, yes please do that!"
- "Sure, that would be great. Send me a new one."
- "So I just can't use this card anymore? That's frustrating."
</case_notes>

### What to do now

Carry out the customer's request. Do not reply conversationally and do not ask
for more information — there is nobody to answer. Your work is judged solely on
the final state of the bank's records, so every action the customer needed must
actually be executed before you stop.
