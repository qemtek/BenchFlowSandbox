#!/bin/sh
# Reference solution: the gold actions, driven through the same CLI
# the agent uses. Proves the task is reachable via the agent interface.
set -eu

bank call log_verification '{"name": "Wei-Ting Lin", "user_id": "wl94k7m3p8", "address": "1628 Pacific Heights Blvd, Apt 8A, San Francisco, CA 94115", "email": "weiting.lin@gmail.com", "phone_number": "415-555-0863", "date_of_birth": "03/22/1987", "time_verified": "2025-11-14 03:40:00 EST"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847", "arguments": "{\"user_id\": \"wl94k7m3p8\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173", "arguments": "{\"account_id\": \"sav_wl94k7m3p8_gold\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "apply_savings_account_credit_6831"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "apply_savings_account_credit_6831", "arguments": "{\"account_id\": \"sav_wl94k7m3p8_gold\", \"amount\": 140.00, \"credit_type\": \"interest_correction\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "submit_interest_discrepancy_report_7294"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "submit_interest_discrepancy_report_7294", "arguments": "{\"account_id\": \"sav_wl94k7m3p8_gold\", \"user_id\": \"wl94k7m3p8\", \"expected_apy\": 6.85, \"actual_apy\": 5.10, \"amount_difference\": 140.00}"}'
