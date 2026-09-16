#!/bin/sh
# Reference solution: the gold actions, driven through the same CLI
# the agent uses. Proves the task is reachable via the agent interface.
set -eu

bank call log_verification '{"name": "Marcus Chen-Williams", "user_id": "mc80w7k3x9", "address": "2934 Queen Anne Avenue North, Unit 8B, Seattle, WA 98109", "email": "marcus.chenwilliams@gmail.com", "phone_number": "206-555-4729", "date_of_birth": "07/18/1980", "time_verified": "2025-11-14 03:40:00 EST"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847", "arguments": "{\"user_id\": \"mc80w7k3x9\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173", "arguments": "{\"account_id\": \"sav_mc80w7k3x9_silver\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173", "arguments": "{\"account_id\": \"sav_mc80w7k3x9_platinum\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173", "arguments": "{\"account_id\": \"sav_mc80w7k3x9_diamond\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173", "arguments": "{\"account_id\": \"sav_mc80w7k3x9_silverplus\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "apply_savings_account_credit_6831"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "apply_savings_account_credit_6831", "arguments": "{\"account_id\": \"sav_mc80w7k3x9_silver\", \"amount\": 220.84, \"credit_type\": \"interest_correction\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "apply_savings_account_credit_6831", "arguments": "{\"account_id\": \"sav_mc80w7k3x9_platinum\", \"amount\": 67.08, \"credit_type\": \"interest_correction\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "apply_savings_account_credit_6831", "arguments": "{\"account_id\": \"sav_mc80w7k3x9_diamond\", \"amount\": 70.00, \"credit_type\": \"interest_correction\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "apply_savings_account_credit_6831", "arguments": "{\"account_id\": \"sav_mc80w7k3x9_silverplus\", \"amount\": 12.00, \"credit_type\": \"interest_correction\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "submit_interest_discrepancy_report_7294"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "submit_interest_discrepancy_report_7294", "arguments": "{\"account_id\": \"sav_mc80w7k3x9_silver\", \"user_id\": \"mc80w7k3x9\", \"expected_apy\": 6.65, \"actual_apy\": 4.0, \"amount_difference\": 220.84}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "submit_interest_discrepancy_report_7294", "arguments": "{\"account_id\": \"sav_mc80w7k3x9_platinum\", \"user_id\": \"mc80w7k3x9\", \"expected_apy\": 7.65, \"actual_apy\": 6.5, \"amount_difference\": 67.08}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "submit_interest_discrepancy_report_7294", "arguments": "{\"account_id\": \"sav_mc80w7k3x9_diamond\", \"user_id\": \"mc80w7k3x9\", \"expected_apy\": 8.2, \"actual_apy\": 7.5, \"amount_difference\": 70.00}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "submit_interest_discrepancy_report_7294", "arguments": "{\"account_id\": \"sav_mc80w7k3x9_silverplus\", \"user_id\": \"mc80w7k3x9\", \"expected_apy\": 5.3, \"actual_apy\": 4.5, \"amount_difference\": 12.00}"}'
