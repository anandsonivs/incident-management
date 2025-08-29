#!/bin/bash

# Log Truncation Script for Escalation Processor
# This script truncates log files to prevent them from growing too large
# Runs hourly via cron

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$PROJECT_DIR/logs"
MAX_LOG_SIZE="10M"  # Maximum log file size before truncation
BACKUP_COUNT=24     # Number of backup files to keep

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function to truncate a log file
truncate_log() {
    local log_file="$1"
    local backup_dir="$LOG_DIR/backups"
    
    # Create backup directory if it doesn't exist
    mkdir -p "$backup_dir"
    
    # Check if log file exists and has content
    if [ ! -f "$log_file" ] || [ ! -s "$log_file" ]; then
        return 0
    fi
    
    # Get current file size
    local file_size=$(stat -f%z "$log_file" 2>/dev/null || echo 0)
    local max_size_bytes=$(numfmt --from=iec "$MAX_LOG_SIZE" 2>/dev/null || echo 10485760)  # Default to 10MB
    
    # Only truncate if file is larger than max size
    if [ "$file_size" -gt "$max_size_bytes" ]; then
        echo "$(date): Truncating $log_file (size: $(numfmt --to=iec $file_size))"
        
        # Create timestamped backup
        local timestamp=$(date +"%Y%m%d_%H%M%S")
        local filename=$(basename "$log_file")
        local backup_file="$backup_dir/${filename}.${timestamp}"
        
        # Move current log to backup
        mv "$log_file" "$backup_file"
        
        # Create new empty log file
        touch "$log_file"
        chmod 644 "$log_file"
        
        # Compress backup
        gzip "$backup_file" &
        
        echo "$(date): Created backup: $backup_file.gz"
    fi
}

# Function to clean up old backups
cleanup_old_backups() {
    local backup_dir="$LOG_DIR/backups"
    
    if [ ! -d "$backup_dir" ]; then
        return 0
    fi
    
    # Find and remove old backup files (keep only the last $BACKUP_COUNT)
    local backup_files=$(find "$backup_dir" -name "*.gz" -type f | sort)
    local count=$(echo "$backup_files" | wc -l)
    
    if [ "$count" -gt "$BACKUP_COUNT" ]; then
        local to_remove=$(echo "$backup_files" | head -n $((count - BACKUP_COUNT)))
        echo "$(date): Removing old backup files..."
        echo "$to_remove" | xargs rm -f
        echo "$(date): Cleaned up old backups"
    fi
}

# Main execution
echo "$(date): Starting log truncation process..."

# Truncate main log files
truncate_log "$LOG_DIR/escalation_processor.log"
truncate_log "$LOG_DIR/escalation_processor_error.log"

# Clean up old backups
cleanup_old_backups

echo "$(date): Log truncation process completed"

# Log the truncation event to a separate log
echo "$(date): Log truncation completed" >> "$LOG_DIR/truncation.log"
