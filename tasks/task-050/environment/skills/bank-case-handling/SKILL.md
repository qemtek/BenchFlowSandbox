---
name: bank-case-handling
description: Procedure for handling a Rho-Bank customer case end to end - reading every request, verifying identity, finding the documented procedure, reaching a specialised operation, and finishing.
---

# Handling a customer case

## 1. List every distinct request before acting
A case often contains more than one. You are judged on all of them, and a case
that ends with one handled and three ignored scores the same as one where you
did nothing.

## 2. Verify before you change anything
Look the customer up by the name, email or phone number in the notes. Compare
what they told you against the record, then call `log_verification`.

The lookup is how you verify, so it comes first. What waits for
`log_verification` is every operation that changes the bank's records, and
every account detail you state in your closing report.

## 3. Search the documentation before you search for a tool
The internal knowledge base holds eligibility rules, fees, reason codes, and
the name of the operation each procedure ends in. Tool descriptions carry none
of that. Use the bounded documentation tools:

    kb_search   return document IDs, titles and short snippets
    kb_get      read one selected document

Search first, then open only the relevant result. Do not use the terminal or
filesystem to search the knowledge base, and stop retrieving once you have the
procedure or policy needed for the next action.

## 4. Follow the whole procedure, not its last step
A procedure written as numbered steps is a checklist. The eligibility checks
near the top are part of it - pending disputes, prior closures, existing
replacement orders, account age. Run them, and act on what they return.

If a procedure applies, complete it. Escalating instead is not a safe
substitute: it leaves the request undone.

Where the documentation states an exception for this case - including that
identity verification is not required - follow the documentation over the
general policy.

## 5. Reaching a specialised operation
Most operations are not loaded. Three steps:

    bank_search              describe what you want to do
    bank_describe_operation  read its arguments, types, defaults and any enum
    bank_call_operation      run it

Describe before you call. Do not guess an argument you have not read.

## 6. Codes come from the documentation, not from judgement
Some arguments accept only a fixed set of values. `bank_describe_operation`
tells you which values are legal; the documentation tells you which one this
situation is. A code that reads plausibly is not the same as the code whose
documented trigger matches what happened, and only the second scores.

## 7. Finish
You are judged on the bank's records, not on what you write. Before stopping,
check each request from step 1 against what you actually executed.
