#!/bin/sh
# Reference solution: the gold actions, driven through the same CLI
# the agent uses. Proves the task is reachable via the agent interface.
set -eu

bank call log_verification '{"name": "Somchai Prasert", "user_id": "sp93k4m7n2", "address": "1847 Sunset Boulevard, Apt 12B, Los Angeles, CA 90028", "email": "somchai.prasert@gmail.com", "phone_number": "323-555-0847", "date_of_birth": "08/14/1989", "time_verified": "2025-11-14 03:40:00 EST"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847", "arguments": "{\"user_id\": \"sp93k4m7n2\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173", "arguments": "{\"account_id\": \"sav_sp93k4m7n2_silver\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "apply_savings_account_credit_6831"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "apply_savings_account_credit_6831", "arguments": "{\"account_id\": \"sav_sp93k4m7n2_silver\", \"amount\": 33.00, \"credit_type\": \"interest_correction\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "submit_interest_discrepancy_report_7294"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "submit_interest_discrepancy_report_7294", "arguments": "{\"account_id\": \"sav_sp93k4m7n2_silver\", \"user_id\": \"sp93k4m7n2\", \"expected_apy\": 4.275, \"actual_apy\": 4.0, \"amount_difference\": 33.00}"}'
