#!/bin/sh
# Reference solution: the gold actions, driven through the same CLI
# the agent uses. Proves the task is reachable via the agent interface.
set -eu

bank call log_verification '{"name": "Marcus Thompson", "user_id": "mt35a7c9d2", "address": "2847 Pine Street, Apt 12B, Seattle, WA 98101", "email": "marcus.thompson@techdev.io", "phone_number": "206-555-3842", "date_of_birth": "03/15/1990", "time_verified": "2025-11-14 03:40:00 EST"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847", "arguments": "{\"user_id\": \"mt35a7c9d2\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_debit_cards_by_account_id_7823"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_debit_cards_by_account_id_7823", "arguments": "{\"account_id\": \"chk_mt35a7c9d2_blue\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "unfreeze_debit_card_3893"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "unfreeze_debit_card_3893", "arguments": "{\"card_id\": \"dbc_mt35a7c9d2_blue\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "clear_debit_card_fraud_alert_4892"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "clear_debit_card_fraud_alert_4892", "arguments": "{\"card_id\": \"dbc_mt35a7c9d2_blue\", \"reason\": \"velocity_clear\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_debit_cards_by_account_id_7823", "arguments": "{\"account_id\": \"chk_mt35a7c9d2_gff\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "unfreeze_debit_card_3893", "arguments": "{\"card_id\": \"dbc_mt35a7c9d2_gff\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_debit_cards_by_account_id_7823", "arguments": "{\"account_id\": \"chk_mt35a7c9d2_evergreen\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_bank_account_transactions_9173", "arguments": "{\"account_id\": \"chk_mt35a7c9d2_evergreen\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "file_debit_card_transaction_dispute_6281"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "file_debit_card_transaction_dispute_6281", "arguments": "{\"transaction_id\": \"btxn_70fb52ef4e29\", \"account_id\": \"chk_mt35a7c9d2_evergreen\", \"card_id\": \"dbc_mt35a7c9d2_evergreen\", \"user_id\": \"mt35a7c9d2\", \"dispute_category\": \"card_present_fraud\", \"transaction_date\": \"11/06/2025\", \"discovery_date\": \"11/06/2025\", \"disputed_amount\": 499.99, \"transaction_type\": \"pin_purchase\", \"card_in_possession\": true, \"pin_compromised\": \"no\", \"contacted_merchant\": false, \"police_report_filed\": false, \"written_statement_provided\": true, \"provisional_credit_eligible\": true, \"customer_max_liability_amount\": 50, \"card_action\": \"close_and_reissue\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "close_debit_card_4721"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "close_debit_card_4721", "arguments": "{\"card_id\": \"dbc_mt35a7c9d2_evergreen\", \"reason\": \"fraud_suspected\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "order_debit_card_5739"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "order_debit_card_5739", "arguments": "{\"account_id\": \"chk_mt35a7c9d2_evergreen\", \"user_id\": \"mt35a7c9d2\", \"delivery_option\": \"EXPEDITED\", \"delivery_fee\": 0, \"card_design\": \"PREMIUM\", \"design_fee\": 0, \"shipping_address\": \"2847 Pine Street, Apt 12B, Seattle, WA 98101\"}"}'
