#!/bin/sh
# Reference solution: the gold actions, driven through the same CLI
# the agent uses. Proves the task is reachable via the agent interface.
set -eu

bank call log_verification '{"name": "Sofia Papadopoulos", "user_id": "584f9c5d00", "address": "1456 Astoria Boulevard, Queens, NY 11102", "email": "sofia.p@outlook.com", "phone_number": "347-555-0387", "date_of_birth": "01/25/1986", "time_verified": "2025-11-14 03:40:00 EST"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "submit_credit_limit_increase_request_7392"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "submit_credit_limit_increase_request_7392", "arguments": "{\"credit_card_account_id\": \"cc_584f9c5d00_gold\", \"user_id\": \"584f9c5d00\", \"requested_increase_amount\": 2500}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_user_dispute_history_7291"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_user_dispute_history_7291", "arguments": "{\"user_id\": \"584f9c5d00\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_pending_replacement_orders_5765"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_pending_replacement_orders_5765", "arguments": "{\"credit_card_account_id\": \"cc_584f9c5d00_gold\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_credit_limit_increase_history_4829"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_credit_limit_increase_history_4829", "arguments": "{\"credit_card_account_id\": \"cc_584f9c5d00_gold\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_payment_history_6183"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_payment_history_6183", "arguments": "{\"credit_card_account_id\": \"cc_584f9c5d00_gold\", \"months\": 3}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "approve_credit_limit_increase_5847"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "approve_credit_limit_increase_5847", "arguments": "{\"credit_card_account_id\": \"cc_584f9c5d00_gold\", \"user_id\": \"584f9c5d00\", \"new_credit_limit\": 7500}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "order_replacement_credit_card_7291"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "order_replacement_credit_card_7291", "arguments": "{\"credit_card_account_id\": \"cc_584f9c5d00_gold\", \"user_id\": \"584f9c5d00\", \"shipping_address\": \"1456 Astoria Boulevard, Queens, NY 11102\", \"reason\": \"fraud_suspected\", \"expedited_shipping\": true}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "file_credit_card_transaction_dispute_4829"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "file_credit_card_transaction_dispute_4829", "arguments": "{\"transaction_id\": \"txn_584f9c5d00_001\", \"card_action\": \"cancel_and_reissue\", \"card_last_4_digits\": \"7823\", \"full_name\": \"Sofia Papadopoulos\", \"user_id\": \"584f9c5d00\", \"phone\": \"347-555-0387\", \"email\": \"sofia.p@outlook.com\", \"address\": \"1456 Astoria Boulevard, Queens, NY 11102\", \"contacted_merchant\": false, \"purchase_date\": \"11/11/2025\", \"issue_noticed_date\": \"11/12/2025\", \"dispute_reason\": \"unauthorized_fraudulent_charge\", \"resolution_requested\": \"full_refund\", \"eligible_for_provisional_credit\": true}"}'
