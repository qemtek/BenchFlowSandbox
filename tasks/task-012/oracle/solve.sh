#!/bin/sh
# Reference solution: the gold actions, driven through the same CLI
# the agent uses. Proves the task is reachable via the agent interface.
set -eu

bank call transfer_to_human_agents '{"reason": "kb_search_unsuccessful_customer_requests_transfer", "summary": "Customer is asking about how to set up a travel notification for their Platinum Rewards Card before traveling to Japan. I was unable to find information about this process in the knowledge base."}'
