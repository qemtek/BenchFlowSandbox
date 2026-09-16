---
# Task frontmatter template. Curly-brace fields are filled by tools/make_task.py.
# Edit here to change configuration for every generated task at once.
schema_version: '1.3'
task:
  name: bank/task-089
metadata:
  domain: banking_knowledge
  source_task_id: task_089
  reward_basis: DB
  requestor: assistant
agent:
  timeout_sec: 900.0
verifier:
  type: test-script
  timeout_sec: 300.0
sandbox:
  workdir: /app
  # no-network would arm BenchFlow's egress firewall, which shells out to
  # iptables and needs NET_ADMIN — unavailable under Docker Desktop. Nothing
  # in the task reaches out: the knowledge base is local files.
  network_mode: public
  build_timeout_sec: 1800.0
---

## prompt

You are a customer service agent at Rho-Bank. Handle the customer enquiry below.

### Your tools

    bank list                          the core toolkit
    bank search <words>                find an operation by what it does
    bank <operation> --help            its flags
    bank <operation> --flag value      run it

The bank runs many more operations than `bank list` shows. Use `bank search` to
find the one you need — for example `bank search close account` — then
`bank <operation> --help` to see its flags. For example:

    bank change-user-email --user-id 123 --new-email new@example.com

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
The customer is David Martinez, a 42-year-old accountant living in Denver, Colorado. The customer is a terse person. The customer is frustrated because they just had THREE debit cards declined at the ATM - their Green Account card, their Blue Account card, and their 16-year-old daughter Sofia's Light Green Account (teen) card.

**Verification info:**
- Name: David Martinez | Phone: 303-555-7294 | Email: david.martinez.cpa@gmail.com
- DOB: 06/18/1983 | Address: 4521 Mountain View Drive, Denver, CO 80203

---

What the customer said during the call:

- "Hi, I need help. I'm at an ATM right now and I've had THREE different debit cards decline on me. My Green Account card, my Blue Account card, and my daughter's teen account card. I really need cash - my car broke down and I need to pay the tow truck driver who only takes cash!"
- "The screen just said 'transaction declined' or something like that. I don't remember seeing a specific code - I was too flustered to pay attention to the details."
- "Whichever one you can fix fastest - I just need cash! Maybe start with my Green Account card since that's my main one?"
- "I tried to get $550 from that one. I know I have plenty of money in the account, so I don't understand why it declined."
- "Wait, there's a daily limit? I had no idea. How much have I already taken out today?"
- "Oh right, I did hit up a few ATMs earlier today. I was running errands and grabbing cash here and there - didn't realize it all adds up against some limit."
- "So I can only get that much more? But I need $550 for the tow truck! This is awful. Is there anything you can do to help me get more today?"
- "Yes, please do that!"
- "Fine, I'll try that. What about my other cards?"
- "I tried to get $300 from that one."
- "Can you increase that one too?"
- "Ah, that's annoying. Okay, what about my daughter's card?"
- "Great, thanks. What about my daughter's card?"
- "That's my daughter Sofia's card - she's 16. It's a Light Green Account, the teen checking account."
- "She tried to get $100 for school supplies."
- "Can you increase hers too?"
- "Okay, I guess I'll just give her cash from my card then."
- "---

### CLOSING THE CONVERSATION

**Once all three cards have been addressed:**"
</case_notes>

### What to do now

Carry out the customer's request using `bank call`. Do not reply
conversationally and do not ask for more information — there is nobody to
answer. Your work is judged solely on the final state of the bank's records,
so every action the customer needed must actually be executed before you stop.
