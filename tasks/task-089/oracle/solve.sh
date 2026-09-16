#!/bin/sh
# Reference solution: the gold actions, driven through the same CLI
# the agent uses. Proves the task is reachable via the agent interface.
set -eu

bank call log_verification '{"name": "David Martinez", "user_id": "dm42f8c3a7", "address": "4521 Mountain View Drive, Denver, CO 80203", "email": "david.martinez.cpa@gmail.com", "phone_number": "303-555-7294", "date_of_birth": "06/18/1983", "time_verified": "2025-11-14 03:40:00 EST"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847", "arguments": "{\"user_id\": \"dm42f8c3a7\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_debit_cards_by_account_id_7823"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_debit_cards_by_account_id_7823", "arguments": "{\"account_id\": \"chk_dm42f8c3a7_green\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173", "arguments": "{\"account_id\": \"chk_dm42f8c3a7_green\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "request_temporary_debit_card_limit_increase_8374"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "request_temporary_debit_card_limit_increase_8374", "arguments": "{\"card_id\": \"dbc_2f8a7c3d1e9b\", \"limit_type\": \"atm\", \"new_limit\": 900}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_debit_cards_by_account_id_7823", "arguments": "{\"account_id\": \"chk_dm42f8c3a7_blue\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173", "arguments": "{\"account_id\": \"chk_dm42f8c3a7_blue\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_debit_cards_by_account_id_7823", "arguments": "{\"account_id\": \"chk_sm16d4e9b2_lightgreen\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173", "arguments": "{\"account_id\": \"chk_sm16d4e9b2_lightgreen\"}"}'
