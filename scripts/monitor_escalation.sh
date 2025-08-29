#!/bin/bash

# Monitor Escalation Processor
# This script helps monitor the status of the escalation processor

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_FILE="$PROJECT_DIR/logs/escalation_processor.log"
ERROR_LOG_FILE="$PROJECT_DIR/logs/escalation_processor_error.log"

echo "=== Escalation Processor Monitor ==="
echo "Project directory: $PROJECT_DIR"
echo "Log file: $LOG_FILE"
echo "Error log file: $ERROR_LOG_FILE"
echo ""

# Check if cron jobs are set up
echo "=== Cron Job Status ==="
if crontab -l 2>/dev/null | grep -q "escalation_processor"; then
    echo "✅ Escalation processor cron job is configured:"
    crontab -l | grep "escalation_processor"
else
    echo "❌ No cron job found for escalation processor"
fi

if crontab -l 2>/dev/null | grep -q "truncate_logs"; then
    echo "✅ Log truncation cron job is configured:"
    crontab -l | grep "truncate_logs"
else
    echo "❌ No cron job found for log truncation"
fi
echo ""

# Check log files
echo "=== Log File Status ==="
if [ -f "$LOG_FILE" ]; then
    echo "✅ Main log file exists"
    echo "   Size: $(ls -lh "$LOG_FILE" | awk '{print $5}')"
    echo "   Last modified: $(stat -f "%Sm" "$LOG_FILE")"
else
    echo "❌ Main log file not found"
fi

if [ -f "$ERROR_LOG_FILE" ]; then
    echo "✅ Error log file exists"
    echo "   Size: $(ls -lh "$ERROR_LOG_FILE" | awk '{print $5}')"
    echo "   Last modified: $(stat -f "%Sm" "$ERROR_LOG_FILE")"
else
    echo "❌ Error log file not found"
fi
echo ""

# Show recent activity
echo "=== Recent Activity (last 10 lines) ==="
if [ -f "$LOG_FILE" ]; then
    echo "Main log:"
    tail -10 "$LOG_FILE" | sed 's/^/  /'
else
    echo "No main log file to show"
fi
echo ""

if [ -f "$ERROR_LOG_FILE" ] && [ -s "$ERROR_LOG_FILE" ]; then
    echo "Error log:"
    tail -10 "$ERROR_LOG_FILE" | sed 's/^/  /'
else
    echo "No errors in error log"
fi
echo ""

# Show cron schedule
echo "=== Cron Schedule ==="
echo "The escalation processor runs every 5 minutes"
echo "Next run times (approximate):"
for i in {0..4}; do
    next_minute=$(( (10#$(date +%M) / 5 * 5 + 5 + i * 5) % 60 ))
    if [ $next_minute -eq 0 ]; then
        next_minute=60
    fi
    echo "  - $(date +%H):$(printf "%02d" $next_minute)"
done
echo ""

# Quick health check
echo "=== Health Check ==="
if [ -f "$LOG_FILE" ]; then
    last_run=$(tail -1 "$LOG_FILE" | grep -o ".*Escalation processor completed successfully" | tail -1)
    if [ -n "$last_run" ]; then
        echo "✅ Last successful run: $last_run"
    else
        echo "⚠️  No successful runs found in recent logs"
    fi
else
    echo "❌ Cannot check health - no log file"
fi

if [ -f "$ERROR_LOG_FILE" ] && [ -s "$ERROR_LOG_FILE" ]; then
    echo "⚠️  Errors detected in error log"
else
    echo "✅ No errors detected"
fi
echo ""

echo "=== Useful Commands ==="
echo "To view live logs: tail -f $LOG_FILE"
echo "To view live error logs: tail -f $ERROR_LOG_FILE"
echo "To check cron status: crontab -l"
echo "To remove cron job: crontab -e (then delete the line)"
echo "To run manually: $PROJECT_DIR/scripts/run_escalation_processor.sh"
echo "To truncate logs manually: $PROJECT_DIR/scripts/truncate_logs.sh"
echo "To view truncation log: tail -f $PROJECT_DIR/logs/truncation.log"
