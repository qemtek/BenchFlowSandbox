#!/bin/sh
# Reference solution: the gold actions, driven through the same CLI
# the agent uses. Proves the task is reachable via the agent interface.
set -eu

bank call log_verification '{"name": "Daniel Park-Hernandez", "user_id": "e9d195fe8e", "address": "7245 Mountain View Way, Scottsdale, AZ 85250", "email": "daniel.ph@outlook.com", "phone_number": "480-555-0917", "date_of_birth": "05/12/1991", "time_verified": "2025-11-14 03:40:00 EST"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_user_dispute_history_7291"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_user_dispute_history_7291", "arguments": "{\"user_id\": \"e9d195fe8e\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_pending_replacement_orders_5765"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_pending_replacement_orders_5765", "arguments": "{\"credit_card_account_id\": \"cc_e9d195fe8e_silver\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_credit_limit_increase_history_4829"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_credit_limit_increase_history_4829", "arguments": "{\"credit_card_account_id\": \"cc_e9d195fe8e_silver\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_payment_history_6183"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_payment_history_6183", "arguments": "{\"credit_card_account_id\": \"cc_e9d195fe8e_silver\", \"months\": 3}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "submit_credit_limit_increase_request_7392"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "submit_credit_limit_increase_request_7392", "arguments": "{\"credit_card_account_id\": \"cc_e9d195fe8e_silver\", \"user_id\": \"e9d195fe8e\", \"requested_increase_amount\": 7500}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "approve_credit_limit_increase_5847"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "approve_credit_limit_increase_5847", "arguments": "{\"credit_card_account_id\": \"cc_e9d195fe8e_silver\", \"user_id\": \"e9d195fe8e\", \"new_credit_limit\": 22500}"}'
bank call give_discoverable_user_tool '{"discoverable_tool_name": "get_card_last_4_digits"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "file_credit_card_transaction_dispute_4829"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "file_credit_card_transaction_dispute_4829", "arguments": "{\"transaction_id\": \"txn_e9d195fe8e_001\", \"card_action\": \"keep_active\", \"card_last_4_digits\": \"2791\", \"full_name\": \"Daniel Park-Hernandez\", \"user_id\": \"e9d195fe8e\", \"phone\": \"480-555-0917\", \"email\": \"daniel.ph@outlook.com\", \"address\": \"7245 Mountain View Way, Scottsdale, AZ 85250\", \"contacted_merchant\": true, \"purchase_date\": \"10/10/2025\", \"issue_noticed_date\": \"10/31/2025\", \"dispute_reason\": \"goods_services_not_received\", \"resolution_requested\": \"full_refund\", \"eligible_for_provisional_credit\": true}"}'
