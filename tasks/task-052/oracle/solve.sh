#!/bin/sh
# Reference solution: the gold actions, driven through the same CLI
# the agent uses. Proves the task is reachable via the agent interface.
set -eu

bank call log_verification '{"name": "Zhang Mei", "user_id": "5e4c1a83b0", "address": "3178 Harbor View Drive, San Diego, CA 92101", "email": "meimeimeimei@icloud.com", "phone_number": "619-555-0756", "date_of_birth": "01/24/1991", "time_verified": "2025-11-14 03:40:00 EST"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "submit_credit_limit_increase_request_7392"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "submit_credit_limit_increase_request_7392", "arguments": "{\"credit_card_account_id\": \"cc_5e4c1a83b0_bronze\", \"user_id\": \"5e4c1a83b0\", \"requested_increase_amount\": 400}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_credit_limit_increase_history_4829"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_credit_limit_increase_history_4829", "arguments": "{\"credit_card_account_id\": \"cc_5e4c1a83b0_bronze\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_user_dispute_history_7291"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_user_dispute_history_7291", "arguments": "{\"user_id\": \"5e4c1a83b0\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_pending_replacement_orders_5765"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_pending_replacement_orders_5765", "arguments": "{\"credit_card_account_id\": \"cc_5e4c1a83b0_bronze\"}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "get_payment_history_6183"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "get_payment_history_6183", "arguments": "{\"credit_card_account_id\": \"cc_5e4c1a83b0_bronze\", \"months\": 6}"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "deny_credit_limit_increase_5848"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "deny_credit_limit_increase_5848", "arguments": "{\"credit_card_account_id\": \"cc_5e4c1a83b0_bronze\", \"user_id\": \"5e4c1a83b0\", \"denial_reason\": \"cooldown_period_active\"}"}'
