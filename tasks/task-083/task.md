---
# Task frontmatter template. Curly-brace fields are filled by tools/make_task.py.
# Edit here to change configuration for every generated task at once.
schema_version: '1.3'
task:
  name: bank/task-083
metadata:
  domain: banking_knowledge
  source_task_id: task_083
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
The customer is Diana Kowalski, a 38-year-old freelance photographer living in Austin, Texas. They manage their business finances through Rho-Bank and keep careful track of all transactions.

**situation:** They've discovered FOUR problematic transactions across TWO of their debit cards this week. Each has different circumstances and they want to dispute all of them.

**Verification info:**
- Name: Diana Kowalski | Phone: 512-555-0734 | Email: diana.kowalski@photoworks.com
- DOB: 06/14/1987 | Address: 2901 South Lamar Blvd, Austin, TX 78704

**YOUR TWO DEBIT CARDS:**
1. Blue Account debit card (card_id: dbc_dk83f5c2a1_blue, ending 5291) - They have this card
2. Green Fee-Free Account debit card (card_id: dbc_dk83f5c2a1_gff, ending 8463) - They have this card

**THE FOUR DISPUTED TRANSACTIONS:**

**Card 1 (Blue Account):**
1. **Third-Party ATM Cash Discrepancy** - $250.00 at "QUICKCASH ATM #7749" on 11/08/2025. They requested $250 but the machine only gave they $100. This was NOT a Rho-Bank ATM - it was a third-party ATM at a convenience store. They noticed immediately when the cash came out short. They have the card, PIN was used (not compromised). They have not contacted anyone about this yet.

2. **Goods/Services Not Received** - $189.50 at "Premium Photo Frames Online" on 11/02/2025. They ordered custom frames for a client project but they never arrived. They contacted the merchant on 11/10/2025 - they claimed they shipped but couldn't provide tracking. They refused to refund. They still have the card, PIN not involved (online purchase).

**Card 2 (Green Fee-Free Account):**
3. **Duplicate Charge** - Two charges of $67.25 at "Austin Coffee Roasters" on 11/11/2025. They only made one purchase but their card was charged twice for the same amount at the same merchant. They noticed when reviewing their statement today (11/14/2025). They have the card, this was a signature purchase. They haven't contacted the merchant yet.

4. **Unauthorized Transaction (PIN Shared)** - $475.00 at "GameStop" on 11/09/2025. This is embarrassing, but they let their nephew borrow their card to buy a $50 video game. He took $475 instead without their permission. They trusted him with the card AND the PIN. They discovered this on 11/12/2025. They have the card back now, but they gave him the PIN willingly before this happened. They have NOT filed a police report - he's family and they're hoping to resolve it privately.

What the customer said during the call:

- "Hi, I need help with some disputed transactions. I found four charges across two of my debit cards that I need to address - they're all different situations. One is an ATM that shorted me cash, one is something I ordered but never received, one is a duplicate charge, and one is... well, a family situation where someone I trusted took more than I authorized."
- "On my Blue Account card ending in 5291, I used an ATM on November 8th at a QuickCash ATM - the one inside the 7-Eleven on Barton Springs Road. I requested $250 but it only gave me $100. I noticed right away. The receipt says $250 though."
- "No, it wasn't a Rho-Bank ATM. It was one of those independent ATMs at a convenience store."
- "I used my PIN normally, it's not compromised or anything."
- "An affidavit? Okay, I can sign whatever paperwork you need. Just email it to me."
- "Also on my Blue Account, there's a charge from Premium Photo Frames Online for $189.50 from November 2nd. I ordered custom frames for a client but they never showed up."
- "Yes, I called them on November 10th. They said they shipped it but couldn't give me any tracking number. When I asked for a refund they refused."
- "No PIN involved, it was online."
- "On my Green Fee-Free card ending in 8463, Austin Coffee Roasters charged me twice on November 11th - two charges of $67.25 for the same purchase. I only bought one thing."
- "It was a signature purchase, I just swiped and signed."
- "No, I haven't called them yet. Should I?"
- "I can try to reach them, but I wanted to file the dispute first in case they don't cooperate."
- "This last one is awkward... On my Green Fee-Free card, there's a $475 charge at GameStop from November 9th. I let my nephew use my card to buy a video game - I said he could spend $50. But he charged $475 instead without my permission."
- "I have the card back now. I took it back when I saw what he did."
- "Yes... I gave him my PIN. He was supposed to just buy one game. I trusted him."
- "I know, I shouldn't have given him my PIN. But I didn't authorize him to spend $475."
- "No, I haven't filed a police report. He's my sister's kid, and I'm hoping to handle this as a family matter. Filing charges would destroy our relationship."
- "I understand. Even if I can't get the money back through the bank, I still want this documented."
- "For the Green Fee-Free card... I guess I should get a new card number since my nephew knows the PIN. But I don't need to cancel the whole account."
- "I understand each situation is different. Can you walk me through what to expect for each one?"
- "I figured that might be an issue since I gave him the PIN. I still want to file the dispute for the record, even if I don't get provisional credit."
- "Yes, absolutely. You can use this conversation as my written statement."
- "Thank you for handling all of this. So I have four disputes filed - even though some might have different outcomes. Can you summarize what I should expect for each?"
</case_notes>

### What to do now

Carry out the customer's request using `bank call`. Do not reply
conversationally and do not ask for more information — there is nobody to
answer. Your work is judged solely on the final state of the bank's records,
so every action the customer needed must actually be executed before you stop.
