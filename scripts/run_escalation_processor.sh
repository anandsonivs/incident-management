#!/bin/bash

# Escalation Processor Runner
# This script runs the escalation processor and can be used with cron

# Set up logging
LOG_FILE="$(dirname "$0")/../logs/escalation_processor.log"
ERROR_LOG_FILE="$(dirname "$0")/../logs/escalation_processor_error.log"

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Change to the project directory
cd "$(dirname "$0")/.."

# Log start time
echo "$(date): Starting escalation processor..." >> "$LOG_FILE"

# Activate virtual environment
source venv/bin/activate

# Run the escalation processor and capture output
python scripts/escalation_processor.py >> "$LOG_FILE" 2>> "$ERROR_LOG_FILE"

# Check exit code
if [ $? -eq 0 ]; then
    echo "$(date): Escalation processor completed successfully" >> "$LOG_FILE"
else
    echo "$(date): Escalation processor failed with exit code $?" >> "$ERROR_LOG_FILE"
    exit 1
fi
