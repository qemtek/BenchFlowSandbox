---
# Task frontmatter template. Curly-brace fields are filled by tools/make_task.py.
# Edit here to change configuration for every generated task at once.
schema_version: '1.3'
task:
  name: bank/task-070
metadata:
  domain: banking_knowledge
  source_task_id: task_070
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
The customer is Yuki Nakamura, a 34-year-old owner of a small digital marketing agency called "Brightwave Digital" based in Portland, OR. They've had a personal Green Account with Rho-Bank for about 3 years and have roughly $2,850 in it. Their business has grown and they need to separate personal and business finances. The customer is practical and want the agent to just tell they what to do.

**goal:** Get ONE recommendation for a business checking account that meets all their requirements. They want the agent to recommend a single account - not give they options to choose from.

**Verification info:**
- Name: Yuki Nakamura | Phone: 503-555-0842 | Email: yuki.nakamura@simba.com
- DOB: 05/12/1991 | Address: 3421 Sakura Avenue, Portland, OR 97205
- Existing account: Green Account (personal checking, balance ~$2,850)

What the customer said during the call:

- "Hi there! I run a small digital marketing agency and I'm looking to open a business checking account that is the easiest to use and gives me the most perks. I also want stuff like no overdraft fees as well as some other requirements and I'm hoping you can tell me which account is the right fit for my needs. I don't want to compare a bunch of options - just point me to the one that works best for my situation."
- "So I travel to meet clients pretty regularly and I use ATMs all over the place. I need at least $15 a month in ATM fee rebates - those fees add up fast otherwise."
- "I absolutely cannot have overdraft fees. My cash flow fluctuates with client payments, and I've been burned by overdraft charges before at other banks. Zero overdraft fees is non-negotiable for me."
- "I'm a small agency, not some huge corporation. I can't commit to keeping $10,000 or more in the account at all times. If there's a minimum balance requirement, it needs to be reasonable - under ten grand."
- "I'd also like to earn decent interest on whatever I keep in there. At least 1% APY would be nice - I know it's a checking account, but every bit helps."
- "Look, I appreciate the thoroughness, but I really don't want to compare options. You know more about these accounts than I do. Which ONE account best fits everything I just told you? Just give me your recommendation and I'll go with it."
- "Perfect, thanks for making that easy. I think I'm all set for now!"
</case_notes>

### What to do now

Carry out the customer's request using `bank call`. Do not reply
conversationally and do not ask for more information — there is nobody to
answer. Your work is judged solely on the final state of the bank's records,
so every action the customer needed must actually be executed before you stop.
