#!/bin/sh
# Reference solution: the gold actions, driven through the same CLI
# the agent uses. Proves the task is reachable via the agent interface.
set -eu

bank call log_verification '{"name": "Liang Jinhai", "user_id": "lj82d4f1a9", "address": "1420 Lake Shore Drive, Chicago, IL 60610", "email": "jinhai.liang@techventures.com", "phone_number": "312-555-0847", "date_of_birth": "04/12/2002", "time_verified": "2025-11-14 03:40:00 EST"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847", "arguments": "{\"user_id\": \"lj82d4f1a9\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173", "arguments": "{\"account_id\": \"chk_lj82d4f1a9\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173", "arguments": "{\"account_id\": \"chk_538bfb9cba\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "apply_checking_account_credit_5829"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "apply_checking_account_credit_5829", "arguments": "{\"account_id\": \"chk_lj82d4f1a9\", \"amount\": 14.00, \"credit_type\": \"fee_refund\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "apply_checking_account_credit_5829", "arguments": "{\"account_id\": \"chk_538bfb9cba\", \"amount\": 3.50, \"credit_type\": \"fee_refund\"}"}'
