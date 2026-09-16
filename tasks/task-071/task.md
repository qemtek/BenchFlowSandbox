---
# Task frontmatter template. Curly-brace fields are filled by tools/make_task.py.
# Edit here to change configuration for every generated task at once.
schema_version: '1.3'
task:
  name: bank/task-071
metadata:
  domain: banking_knowledge
  source_task_id: task_071
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

Carry out the customer's request using `bank call`. Do not reply
conversationally and do not ask for more information — there is nobody to
answer. Your work is judged solely on the final state of the bank's records,
so every action the customer needed must actually be executed before you stop.
