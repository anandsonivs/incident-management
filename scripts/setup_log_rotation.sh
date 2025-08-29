#!/bin/bash

# Setup Log Rotation for Escalation Processor
# This script sets up log rotation to prevent log files from growing too large

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$PROJECT_DIR/logs"

echo "Setting up log rotation for escalation processor..."
echo "Project directory: $PROJECT_DIR"
echo "Log directory: $LOG_DIR"
echo ""

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Create logrotate configuration
LOGROTATE_CONFIG="/etc/logrotate.d/escalation-processor"

echo "Creating logrotate configuration at $LOGROTATE_CONFIG..."

# Check if we can write to /etc/logrotate.d
if [ ! -w "/etc/logrotate.d" ]; then
    echo "❌ Cannot write to /etc/logrotate.d. You may need to run with sudo."
    echo ""
    echo "Manual setup required:"
    echo "1. Run: sudo $0"
    echo "2. Or manually create the logrotate configuration"
    echo ""
    echo "Alternative: Create a local logrotate configuration in the project directory"
    
    # Create local logrotate configuration
    LOCAL_CONFIG="$PROJECT_DIR/logrotate.conf"
    echo "Creating local logrotate configuration at $LOCAL_CONFIG..."
    
    cat > "$LOCAL_CONFIG" << EOF
# Log rotation configuration for escalation processor
$LOG_DIR/escalation_processor*.log {
    hourly
    rotate 24
    compress
    delaycompress
    missingok
    notifempty
    create 644 $(whoami) staff
    postrotate
        # Optional: Restart any services that might be using the logs
        # echo "Logs rotated for escalation processor"
    endscript
}
EOF
    
    echo "✅ Local logrotate configuration created at $LOCAL_CONFIG"
    echo ""
    echo "To use this configuration:"
    echo "1. Test it: logrotate -d $LOCAL_CONFIG"
    echo "2. Run it manually: logrotate $LOCAL_CONFIG"
    echo "3. Add to crontab for automatic rotation:"
    echo "   0 * * * * /usr/sbin/logrotate $LOCAL_CONFIG"
    
    # Set up crontab for local logrotate
    echo ""
    echo "Would you like me to set up a cron job to run logrotate hourly? (y/n)"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "Adding logrotate cron job..."
        (crontab -l 2>/dev/null; echo "0 * * * * /usr/sbin/logrotate $LOCAL_CONFIG") | crontab -
        echo "✅ Logrotate cron job added successfully!"
        echo ""
        echo "Current crontab entries:"
        crontab -l
    fi
    
    exit 0
fi

# Create the system logrotate configuration
sudo tee "$LOGROTATE_CONFIG" > /dev/null << EOF
# Log rotation configuration for escalation processor
$LOG_DIR/escalation_processor*.log {
    hourly
    rotate 24
    compress
    delaycompress
    missingok
    notifempty
    create 644 $(whoami) staff
    postrotate
        # Optional: Restart any services that might be using the logs
        # echo "Logs rotated for escalation processor"
    endscript
}
EOF

echo "✅ Logrotate configuration created successfully!"
echo ""

# Test the configuration
echo "Testing logrotate configuration..."
if sudo logrotate -d "$LOGROTATE_CONFIG" > /dev/null 2>&1; then
    echo "✅ Logrotate configuration is valid"
else
    echo "❌ Logrotate configuration has issues"
    echo "Testing with verbose output:"
    sudo logrotate -d "$LOGROTATE_CONFIG"
fi

echo ""
echo "=== Log Rotation Setup Complete ==="
echo ""
echo "Configuration details:"
echo "- Logs will be rotated every hour"
echo "- Keeps 24 rotated log files (24 hours of history)"
echo "- Compresses old log files"
echo "- Creates new log files with proper permissions"
echo ""
echo "The logrotate daemon will automatically handle rotation."
echo "You can also test it manually with:"
echo "  sudo logrotate -f $LOGROTATE_CONFIG"
echo ""
echo "To view current logrotate status:"
echo "  sudo logrotate -d $LOGROTATE_CONFIG"
