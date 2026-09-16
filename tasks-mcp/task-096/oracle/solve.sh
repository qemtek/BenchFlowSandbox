#!/bin/sh
# Reference solution: the gold actions, driven through the same CLI
# the agent uses. Proves the task is reachable via the agent interface.
set -eu

bank call log_verification '{"name": "Naomi Ishikawa", "user_id": "ni73k9m4p2", "address": "1847 Pacific Heights Boulevard, Apt 14C, San Francisco, CA 94115", "email": "naomi.ishikawa@outlook.com", "phone_number": "415-555-8293", "date_of_birth": "03/22/1973", "time_verified": "2025-11-14 03:40:00 EST"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847", "arguments": "{\"user_id\": \"ni73k9m4p2\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173", "arguments": "{\"account_id\": \"sav_ni73k9m4p2_bronze\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173", "arguments": "{\"account_id\": \"sav_ni73k9m4p2_goldplus\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "apply_savings_account_credit_6831"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "apply_savings_account_credit_6831", "arguments": "{\"account_id\": \"sav_ni73k9m4p2_bronze\", \"amount\": 17.50, \"credit_type\": \"interest_correction\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "apply_savings_account_credit_6831", "arguments": "{\"account_id\": \"sav_ni73k9m4p2_goldplus\", \"amount\": 15.00, \"credit_type\": \"interest_correction\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "submit_interest_discrepancy_report_7294"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "submit_interest_discrepancy_report_7294", "arguments": "{\"account_id\": \"sav_ni73k9m4p2_bronze\", \"user_id\": \"ni73k9m4p2\", \"expected_apy\": 3.25, \"actual_apy\": 2.55, \"amount_difference\": 17.50}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "submit_interest_discrepancy_report_7294", "arguments": "{\"account_id\": \"sav_ni73k9m4p2_goldplus\", \"user_id\": \"ni73k9m4p2\", \"expected_apy\": 6.85, \"actual_apy\": 6.55, \"amount_difference\": 15.00}"}'
