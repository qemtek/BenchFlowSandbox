#!/bin/sh
# Reference solution: the gold actions, driven through the same CLI
# the agent uses. Proves the task is reachable via the agent interface.
set -eu

bank call log_verification '{"name": "Kim Junho", "user_id": "kj93a7b2e1", "address": "5847 Wilshire Boulevard, Los Angeles, CA 90036", "email": "junho.kim@gmail.com", "phone_number": "213-555-0392", "date_of_birth": "09/14/1994", "time_verified": "2025-11-14 03:40:00 EST"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847", "arguments": "{\"user_id\": \"kj93a7b2e1\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173", "arguments": "{\"account_id\": \"chk_kj93a7b2e1_1\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173", "arguments": "{\"account_id\": \"chk_kj93a7b2e1_2\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173", "arguments": "{\"account_id\": \"chk_kj93a7b2e1_3\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "apply_checking_account_credit_5829"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "apply_checking_account_credit_5829", "arguments": "{\"account_id\": \"chk_kj93a7b2e1_1\", \"amount\": 9.50, \"credit_type\": \"fee_refund\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "apply_checking_account_credit_5829", "arguments": "{\"account_id\": \"chk_kj93a7b2e1_2\", \"amount\": 9.00, \"credit_type\": \"fee_refund\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "apply_checking_account_credit_5829", "arguments": "{\"account_id\": \"chk_kj93a7b2e1_3\", \"amount\": 1.50, \"credit_type\": \"fee_refund\"}"}'
