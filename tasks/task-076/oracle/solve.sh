#!/bin/sh
# Reference solution: the gold actions, driven through the same CLI
# the agent uses. Proves the task is reachable via the agent interface.
set -eu

bank call log_verification '{"name": "Anastasia Volkov", "user_id": "av96d4e7f1", "address": "1847 Pacific Heights Avenue, San Francisco, CA 94115", "email": "anastasia.volkov@globaltech.com", "phone_number": "415-555-2983", "date_of_birth": "03/14/1996", "time_verified": "2025-11-14 03:40:00 EST"}'
bank call unlock_discoverable_agent_tool '{"agent_tool_name": "open_bank_account_4821"}'
bank call call_discoverable_agent_tool '{"agent_tool_name": "open_bank_account_4821", "arguments": "{\"user_id\": \"av96d4e7f1\", \"account_type\": \"checking\", \"account_class\": \"Purple Account\"}"}'
