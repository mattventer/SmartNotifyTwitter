#!/bin/bash

echo "Starting SmartNotify Twitter Success"
nohup python3 src/twitter_success.py >> src/twit_success.log &
echo "Running"