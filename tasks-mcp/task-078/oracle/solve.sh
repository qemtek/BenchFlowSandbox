#!/bin/sh
# Reference solution: the gold actions, driven through the same CLI
# the agent uses. Proves the task is reachable via the agent interface.
set -eu

bank call log_verification '{"name": "Mei-Lin Chen", "user_id": "mc78a5b9d2", "address": "3245 Sunset Boulevard, San Diego, CA 92103", "email": "meiling.chen@outlook.com", "phone_number": "619-555-0284", "date_of_birth": "07/18/1991", "time_verified": "2025-11-14 03:40:00 EST"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847", "arguments": "{\"user_id\": \"mc78a5b9d2\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "freeze_debit_card_3892"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "freeze_debit_card_3892", "arguments": "{\"card_id\": \"dbc_mc78a5b9d2_lb\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "freeze_debit_card_3892", "arguments": "{\"card_id\": \"dbc_mc78a5b9d2_green\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "freeze_debit_card_3892", "arguments": "{\"card_id\": \"dbc_mc78a5b9d2_lg\"}"}'
bank call get_credit_card_accounts_by_user '{"user_id": "mc78a5b9d2"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173", "arguments": "{\"account_id\": \"chk_mc78a5b9d2_1\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173", "arguments": "{\"account_id\": \"chk_mc78a5b9d2_2\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173", "arguments": "{\"account_id\": \"chk_mc78a5b9d2_3\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "unfreeze_debit_card_3893"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "unfreeze_debit_card_3893", "arguments": "{\"card_id\": \"dbc_mc78a5b9d2_lb\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "unfreeze_debit_card_3893", "arguments": "{\"card_id\": \"dbc_mc78a5b9d2_green\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "close_debit_card_4721"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "close_debit_card_4721", "arguments": "{\"card_id\": \"dbc_mc78a5b9d2_lb\", \"reason\": \"lost\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "close_debit_card_4721", "arguments": "{\"card_id\": \"dbc_mc78a5b9d2_green\", \"reason\": \"lost\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_debit_cards_by_account_id_7823"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_debit_cards_by_account_id_7823", "arguments": "{\"account_id\": \"chk_mc78a5b9d2_1\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "order_debit_card_5739"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "order_debit_card_5739", "arguments": "{\"account_id\": \"chk_mc78a5b9d2_2\", \"user_id\": \"mc78a5b9d2\", \"delivery_option\": \"EXPEDITED\", \"delivery_fee\": 15, \"card_design\": \"CLASSIC\", \"design_fee\": 0, \"shipping_address\": \"3245 Sunset Boulevard, San Diego, CA 92103\"}"}'
