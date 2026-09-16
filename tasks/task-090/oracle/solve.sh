#!/bin/sh
# Reference solution: the gold actions, driven through the same CLI
# the agent uses. Proves the task is reachable via the agent interface.
set -eu

bank call log_verification '{"name": "Elena Rodriguez", "user_id": "er38a7c9d2", "address": "1847 Beacon Street, Apt 4B, Boston, MA 02108", "email": "elena.rodriguez@marketingpro.com", "phone_number": "617-555-3847", "date_of_birth": "04/15/1987", "time_verified": "2025-11-14 03:40:00 EST"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847", "arguments": "{\"user_id\": \"er38a7c9d2\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_debit_cards_by_account_id_7823"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_debit_cards_by_account_id_7823", "arguments": "{\"account_id\": \"chk_er38a7c9d2_evergreen\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173", "arguments": "{\"account_id\": \"chk_er38a7c9d2_evergreen\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "close_debit_card_4721"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "close_debit_card_4721", "arguments": "{\"card_id\": \"dbc_er38a7c9d2_evergreen\", \"reason\": \"fraud_suspected\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "order_debit_card_5739"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "order_debit_card_5739", "arguments": "{\"account_id\": \"chk_er38a7c9d2_evergreen\", \"user_id\": \"er38a7c9d2\", \"delivery_option\": \"EXPEDITED\", \"delivery_fee\": 0, \"card_design\": \"CLASSIC\", \"design_fee\": 0, \"shipping_address\": \"1847 Beacon Street, Apt 4B, Boston, MA 02108\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_debit_cards_by_account_id_7823", "arguments": "{\"account_id\": \"chk_er38a7c9d2_blue\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173", "arguments": "{\"account_id\": \"chk_er38a7c9d2_blue\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "reset_debit_card_pin_6284"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "reset_debit_card_pin_6284", "arguments": "{\"card_id\": \"dbc_er38a7c9d2_blue\", \"last_4_digits\": \"6183\", \"new_pin\": \"7294\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_debit_cards_by_account_id_7823", "arguments": "{\"account_id\": \"chk_er38a7c9d2_green\"}"}'
