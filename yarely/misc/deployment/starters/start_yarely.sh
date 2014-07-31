#!/bin/sh
./facade.py &
./sensor_manager.py &
./subscription_manager.py &
./scheduler.py
