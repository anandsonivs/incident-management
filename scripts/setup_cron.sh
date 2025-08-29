#!/bin/bash

# Setup Cron Job for Escalation Processor
# This script helps set up a cron job to run the escalation processor every 5 minutes

# Get the absolute path to the project directory
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT_PATH="$PROJECT_DIR/scripts/run_escalation_processor.sh"

echo "Setting up cron job for escalation processor..."
echo "Project directory: $PROJECT_DIR"
echo "Script path: $SCRIPT_PATH"
echo ""

# Check if the script exists and is executable
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Error: Script not found at $SCRIPT_PATH"
    exit 1
fi

if [ ! -x "$SCRIPT_PATH" ]; then
    echo "Error: Script is not executable. Making it executable..."
    chmod +x "$SCRIPT_PATH"
fi

# Create the cron job entry
CRON_JOB="*/5 * * * * $SCRIPT_PATH"

echo "Cron job entry to add:"
echo "$CRON_JOB"
echo ""

echo "To add this cron job, run one of the following commands:"
echo ""
echo "Option 1: Edit crontab manually:"
echo "  crontab -e"
echo "  # Then add this line:"
echo "  $CRON_JOB"
echo ""
echo "Option 2: Add automatically (this will replace existing crontab):"
echo "  (crontab -l 2>/dev/null; echo \"$CRON_JOB\") | crontab -"
echo ""
echo "Option 3: Add to system crontab (requires sudo):"
echo "  sudo crontab -e"
echo "  # Then add this line:"
echo "  $CRON_JOB"
echo ""

echo "After setting up the cron job, you can:"
echo "- Check if it's running: crontab -l"
echo "- View logs: tail -f $PROJECT_DIR/logs/escalation_processor.log"
echo "- View error logs: tail -f $PROJECT_DIR/logs/escalation_processor_error.log"
echo "- Remove the cron job: crontab -e (then delete the line)"
echo ""

echo "Would you like me to add the cron job automatically? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "Adding cron job..."
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "Cron job added successfully!"
    echo ""
    echo "Current crontab entries:"
    crontab -l
else
    echo "Cron job not added. Please add it manually using one of the options above."
fi
