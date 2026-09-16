#!/bin/sh
# Reference solution: the gold actions, driven through the same CLI
# the agent uses. Proves the task is reachable via the agent interface.
set -eu

bank call log_verification '{"name": "Rachel Winters", "user_id": "rw42b8d3e1", "address": "4521 Colfax Avenue, Unit 8D, Denver, CO 80220", "email": "rachel.winters.realestate@gmail.com", "phone_number": "303-555-7291", "date_of_birth": "06/18/1983", "time_verified": "2025-11-14 03:40:00 EST"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847", "arguments": "{\"user_id\": \"rw42b8d3e1\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_debit_cards_by_account_id_7823"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_debit_cards_by_account_id_7823", "arguments": "{\"account_id\": \"chk_rw42b8d3e1_blue\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173", "arguments": "{\"account_id\": \"chk_rw42b8d3e1_blue\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "close_debit_card_4721"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "close_debit_card_4721", "arguments": "{\"card_id\": \"dbc_rw42b8d3e1_blue\", \"reason\": \"fraud_suspected\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "order_debit_card_5739"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "order_debit_card_5739", "arguments": "{\"account_id\": \"chk_rw42b8d3e1_blue\", \"user_id\": \"rw42b8d3e1\", \"delivery_option\": \"STANDARD\", \"delivery_fee\": 0, \"card_design\": \"CLASSIC\", \"design_fee\": 0, \"shipping_address\": \"4521 Colfax Avenue, Unit 8D, Denver, CO 80220\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_debit_cards_by_account_id_7823", "arguments": "{\"account_id\": \"chk_rw42b8d3e1_green\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173", "arguments": "{\"account_id\": \"chk_rw42b8d3e1_green\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "close_debit_card_4721", "arguments": "{\"card_id\": \"dbc_rw42b8d3e1_green\", \"reason\": \"fraud_suspected\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "order_debit_card_5739", "arguments": "{\"account_id\": \"chk_rw42b8d3e1_green\", \"user_id\": \"rw42b8d3e1\", \"delivery_option\": \"STANDARD\", \"delivery_fee\": 0, \"card_design\": \"CLASSIC\", \"design_fee\": 0, \"shipping_address\": \"4521 Colfax Avenue, Unit 8D, Denver, CO 80220\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_debit_cards_by_account_id_7823", "arguments": "{\"account_id\": \"chk_rw42b8d3e1_evergreen\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173", "arguments": "{\"account_id\": \"chk_rw42b8d3e1_evergreen\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "reset_debit_card_pin_6284"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "reset_debit_card_pin_6284", "arguments": "{\"card_id\": \"dbc_rw42b8d3e1_evergreen\", \"last_4_digits\": \"7263\", \"new_pin\": \"8127\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_debit_cards_by_account_id_7823", "arguments": "{\"account_id\": \"chk_rw42b8d3e1_lightblue\"}"}'
bank call transfer_to_human_agents '{"summary": "Customer Rachel Winters has a Light Blue Account debit card (ending 4518) with a security hold that cannot be unlocked by chat agents. Customer requests assistance from security team to resolve the hold.", "reason": "fraud_or_security_concern"}'
