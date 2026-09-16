#!/bin/sh
# Reference solution: the gold actions, driven through the same CLI
# the agent uses. Proves the task is reachable via the agent interface.
set -eu

bank call log_verification '{"name": "Fatima Al-Hassan", "user_id": "890389b165", "address": "1923 Oak Park Boulevard, Detroit, MI 48226", "email": "coffeelover_fati@protonmail.com", "phone_number": "313-555-0246", "date_of_birth": "12/05/1993", "time_verified": "2025-11-14 03:40:00 EST"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "order_replacement_credit_card_7291"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "order_replacement_credit_card_7291", "arguments": "{\"credit_card_account_id\": \"cc_890389b165_silver\", \"user_id\": \"890389b165\", \"shipping_address\": \"2500 Woodward Avenue, Suite 300, Detroit, MI 48201\", \"reason\": \"fraud_suspected\", \"expedited_shipping\": true}"}'
