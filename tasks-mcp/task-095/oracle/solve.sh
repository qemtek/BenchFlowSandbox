#!/bin/sh
# Reference solution: the gold actions, driven through the same CLI
# the agent uses. Proves the task is reachable via the agent interface.
set -eu

bank call log_verification '{"name": "Lachlan Murray", "user_id": "lm83h7k2p5", "address": "47 Bondi Road, Unit 12B, Bondi Beach, NSW 2026", "email": "lachlan.murray@gmail.com", "phone_number": "0412-555-947", "date_of_birth": "08/14/1983", "time_verified": "2025-11-14 03:40:00 EST"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847", "arguments": "{\"user_id\": \"lm83h7k2p5\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173", "arguments": "{\"account_id\": \"sav_lm83h7k2p5_gold\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "apply_savings_account_credit_6831"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "apply_savings_account_credit_6831", "arguments": "{\"account_id\": \"sav_lm83h7k2p5_gold\", \"amount\": 98.00, \"credit_type\": \"interest_correction\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "submit_interest_discrepancy_report_7294"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "submit_interest_discrepancy_report_7294", "arguments": "{\"account_id\": \"sav_lm83h7k2p5_gold\", \"user_id\": \"lm83h7k2p5\", \"expected_apy\": 6.85, \"actual_apy\": 5.625, \"amount_difference\": 98.00}"}'
