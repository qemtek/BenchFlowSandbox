#!/bin/sh
# Reference solution: the gold actions, driven through the same CLI
# the agent uses. Proves the task is reachable via the agent interface.
set -eu

bank call log_verification '{"name": "Yuki Nakamura", "user_id": "224959b99e", "address": "3421 Sakura Avenue, Portland, OR 97205", "email": "yuki.nakamura@simba.com", "phone_number": "503-555-0842", "date_of_birth": "05/12/1991", "time_verified": "2025-11-14 03:40:00 EST"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_user_dispute_history_7291"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_user_dispute_history_7291", "arguments": "{\"user_id\": \"224959b99e\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_pending_replacement_orders_5765"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_pending_replacement_orders_5765", "arguments": "{\"credit_card_account_id\": \"cc_224959b99e_plat\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847", "arguments": "{\"user_id\": \"224959b99e\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "pay_credit_card_from_checking_9182"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "pay_credit_card_from_checking_9182", "arguments": "{\"user_id\": \"224959b99e\", \"checking_account_id\": \"05\", \"credit_card_account_id\": \"cc_224959b99e_plat\", \"amount\": 75.0}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_closure_reason_history_8293"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_closure_reason_history_8293", "arguments": "{\"credit_card_account_id\": \"cc_224959b99e_plat\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "log_credit_card_closure_reason_4521"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "log_credit_card_closure_reason_4521", "arguments": "{\"credit_card_account_id\": \"cc_224959b99e_plat\", \"user_id\": \"224959b99e\", \"closure_reason\": \"annual_fee\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "apply_credit_card_account_flag_6147"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "apply_credit_card_account_flag_6147", "arguments": "{\"credit_card_account_id\": \"cc_224959b99e_plat\", \"user_id\": \"224959b99e\", \"flag_type\": \"annual_fee_waived\", \"expiration_date\": \"11/14/2026\", \"reason\": \"loyalty_benefit\"}"}'
