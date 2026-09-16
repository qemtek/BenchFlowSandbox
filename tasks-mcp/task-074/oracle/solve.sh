#!/bin/sh
# Reference solution: the gold actions, driven through the same CLI
# the agent uses. Proves the task is reachable via the agent interface.
set -eu

bank call log_verification '{"name": "Ahmad Razali bin Mohd Yusof", "user_id": "ar72c5d8e3", "address": "1245 Pioneer Road, Denver, CO 80203", "email": "ahmad.razali@gmail.com", "phone_number": "303-555-0821", "date_of_birth": "06/15/1989", "time_verified": "2025-11-14 03:40:00 EST"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847", "arguments": "{\"user_id\": \"ar72c5d8e3\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173", "arguments": "{\"account_id\": \"chk_ar72c5d8e3_1\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173", "arguments": "{\"account_id\": \"chk_ar72c5d8e3_2\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173", "arguments": "{\"account_id\": \"chk_ar72c5d8e3_3\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173", "arguments": "{\"account_id\": \"chk_ar72c5d8e3_4\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "apply_checking_account_credit_5829"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "apply_checking_account_credit_5829", "arguments": "{\"account_id\": \"chk_ar72c5d8e3_1\", \"amount\": 27.00, \"credit_type\": \"fee_refund\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "apply_checking_account_credit_5829", "arguments": "{\"account_id\": \"chk_ar72c5d8e3_2\", \"amount\": 14.50, \"credit_type\": \"fee_refund\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "apply_checking_account_credit_5829", "arguments": "{\"account_id\": \"chk_ar72c5d8e3_3\", \"amount\": 4.75, \"credit_type\": \"fee_refund\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "apply_checking_account_credit_5829", "arguments": "{\"account_id\": \"chk_ar72c5d8e3_4\", \"amount\": 3.70, \"credit_type\": \"fee_refund\"}"}'
