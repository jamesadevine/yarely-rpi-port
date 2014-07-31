#!/bin/sh

killall Python
killall Python
killall Python

# Start the Subscription Manager
cd /Users/pdnet/proj/yarely/misc/deployment/starters
./yarely_module_starter.sh -m yarely.frontend.core.subscriptions.subscription_manager /Users/pdnet/proj/yarely/frontend/core/config/samples/yarely.cfg &

# Start the Scheduler
cd /Users/pdnet/proj/yarely/frontend/core/scheduler
python3.2 scheduler.py /Users/pdnet/proj/yarely/frontend/core/config/samples/yarely.cfg
