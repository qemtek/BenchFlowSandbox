#!/bin/sh
# Reference solution: the gold actions, driven through the same CLI
# the agent uses. Proves the task is reachable via the agent interface.
set -eu

bank call log_verification '{"name": "Roberto Delgado", "user_id": "b5e8f2a1c9", "address": "4521 Saguaro Drive, Mesa, AZ 85201", "email": "roberto.delgado@delgadolandscaping.com", "phone_number": "480-555-0634", "date_of_birth": "03/18/1986", "time_verified": "2025-11-14 03:40:00 EST"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_all_user_accounts_by_user_id_3847", "arguments": "{\"user_id\": \"b5e8f2a1c9\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "open_bank_account_4821"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "open_bank_account_4821", "arguments": "{\"user_id\": \"b5e8f2a1c9\", \"account_type\": \"business_checking\", \"account_class\": \"Cobalt Blue\"}"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "open_bank_account_4821", "arguments": "{\"user_id\": \"b5e8f2a1c9\", \"account_type\": \"business_savings\", \"account_class\": \"Silver Plus Saver Account\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "transfer_funds_between_bank_accounts_7291"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "transfer_funds_between_bank_accounts_7291", "arguments": "{\"source_account_id\": \"biz_chk_b5e8f2a1c9\", \"destination_account_id\": \"c1b48f17bb35e876\", \"amount\": 3200}"}'
