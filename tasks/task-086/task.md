---
# Task frontmatter template. Curly-brace fields are filled by tools/make_task.py.
# Edit here to change configuration for every generated task at once.
schema_version: '1.3'
task:
  name: bank/task-086
metadata:
  domain: banking_knowledge
  source_task_id: task_086
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

Carry out the customer's request using `bank call`. Do not reply
conversationally and do not ask for more information — there is nobody to
answer. Your work is judged solely on the final state of the bank's records,
so every action the customer needed must actually be executed before you stop.
