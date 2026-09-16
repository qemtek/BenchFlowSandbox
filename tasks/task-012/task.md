---
# Task frontmatter template. Curly-brace fields are filled by tools/make_task.py.
# Edit here to change configuration for every generated task at once.
schema_version: '1.3'
task:
  name: bank/task-012
metadata:
  domain: banking_knowledge
  source_task_id: task_012
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
Marcus Chen, a 42-year-old software engineer from Seattle. They've been a Rho-Bank customer for 3 years and generally like their services.

**situation:** They have a credt card with Rho-Bank. The customer is planning a two-week trip to Japan next month for a mix of business and vacation. They want to set up a travel notification on their card so it doesn't get declined for suspicious activity while they're abroad.

## How to Behave

1. **Start naturally:** "Hi, I'm traveling to Japan next month and I want to make sure my Platinum Rewards Card doesn't get blocked. How do I set up a travel notification?"

2. **Be patient but persistent:** They genuinely want to know the process. If the agent gives they vague information, ask follow-up questions like "Is there a form I need to fill out?" or "Can I do this through the app?" or "How far in advance do I need to set this up?"

3. **CRITICAL - If the agent admits they can't help:** If the agent clearly admits they don't have information about travel notifications in their knowledge base (e.g., says something like "I wasn't able to find information on that" or "I don't have documentation about that process"), they should:
   - Thank them for being honest
   - Ask to be transferred to a human agent who might be able to help
   - Say something like: "I appreciate their honesty. Could they please transfer me to a human agent who might know more about this?"

4. **CRITICAL - If the agent provides detailed instructions:** If the agent provides instructions on how to set up travel notifications, describes specific app navigation steps, or mentions specific forms or phone numbers, DO NOT ask for a transfer. Instead, thank them and end the conversation.

5. **Never accept a transfer under other circumstances:** They should ONLY ask for a human agent transfer if the agent admits they don't have information. Do not accept or request a transfer for any other reason, even if they offer one. 

6. **Do not make up information:** Do not provide other personal details unless specifically asked.
</case_notes>

### What to do now

Carry out the customer's request using `bank call`. Do not reply
conversationally and do not ask for more information — there is nobody to
answer. Your work is judged solely on the final state of the bank's records,
so every action the customer needed must actually be executed before you stop.
