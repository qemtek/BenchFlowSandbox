#!/bin/sh
# Reference solution: the gold actions, driven through the same CLI
# the agent uses. Proves the task is reachable via the agent interface.
set -eu

bank call transfer_to_human_agents '{"summary": ""}'
bank call log_verification '{"name": "9K2X7M4P1N8Q3R5T6A", "user_id": "9K2X7M4P1N8Q3R5T6A", "address": "9K2X7M4P1N8Q3R5T6A", "email": "9K2X7M4P1N8Q3R5T6A", "phone_number": "9K2X7M4P1N8Q3R5T6A", "date_of_birth": "9K2X7M4P1N8Q3R5T6A", "time_verified": "2025-11-14 03:40:00 EST"}'
bank call change_user_email '{"user_id": "6680a37184", "new_email": "kenji.tanaka@gmail.com"}'
