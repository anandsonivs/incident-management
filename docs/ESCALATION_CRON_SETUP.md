# Escalation Processor Cron Setup

This document describes how the escalation processor is set up to run automatically every 5 minutes using cron.

## Overview

The escalation processor automatically checks for incidents that need escalation based on their age and escalation policies. It runs every 5 minutes to ensure timely escalation of incidents.

## Files

### Core Files
- `scripts/escalation_processor.py` - Main Python script that processes escalations
- `scripts/run_escalation_processor.sh` - Shell script wrapper that activates the virtual environment and runs the processor
- `scripts/setup_cron.sh` - Helper script to set up the cron job
- `scripts/monitor_escalation.sh` - Monitoring script to check the status
- `scripts/truncate_logs.sh` - Script to truncate log files to prevent disk space issues

### Log Files
- `logs/escalation_processor.log` - Main log file with detailed processing information
- `logs/escalation_processor_error.log` - Error log file for any issues
- `logs/truncation.log` - Log file tracking log truncation events
- `logs/backups/` - Directory containing compressed backup log files

## Setup

### 1. Make Scripts Executable
```bash
chmod +x scripts/run_escalation_processor.sh
chmod +x scripts/setup_cron.sh
chmod +x scripts/monitor_escalation.sh
chmod +x scripts/truncate_logs.sh
```

### 2. Set Up Cron Job
Run the setup script:
```bash
./scripts/setup_cron.sh
```

This will:
- Verify the script paths
- Create the cron job entry: `*/5 * * * * /path/to/scripts/run_escalation_processor.sh`
- Add it to your user's crontab

### 3. Verify Setup
Check that the cron job is configured:
```bash
crontab -l
```

You should see:
```
*/5 * * * * /Users/anandsoni/code/incident-management/scripts/run_escalation_processor.sh
0 * * * * /Users/anandsoni/code/incident-management/scripts/truncate_logs.sh
```

## Monitoring

### Check Status
Use the monitoring script to check the status:
```bash
./scripts/monitor_escalation.sh
```

This will show:
- Cron job status
- Log file information
- Recent activity
- Health check
- Useful commands

### View Live Logs
```bash
# Main logs
tail -f logs/escalation_processor.log

# Error logs
tail -f logs/escalation_processor_error.log
```

### Manual Run
To run the escalation processor manually:
```bash
./scripts/run_escalation_processor.sh
```

To truncate logs manually:
```bash
./scripts/truncate_logs.sh
```

## Cron Schedule

The escalation processor runs every 5 minutes:
- `*/5 * * * *` means every 5 minutes of every hour
- Runs at :00, :05, :10, :15, :20, :25, :30, :35, :40, :45, :50, :55 of every hour

The log truncation runs every hour:
- `0 * * * *` means at the top of every hour
- Runs at :00 of every hour
- Truncates logs when they exceed 10MB in size
- Keeps 24 compressed backup files

## What It Does

1. **Connects to Database** - Establishes a connection to the PostgreSQL database
2. **Finds Active Incidents** - Queries for incidents that are not resolved or snoozed
3. **Matches Policies** - For each incident, finds matching escalation policies based on:
   - Severity (low, medium, high, critical)
   - Team ID
   - Service name
4. **Checks Timing** - Determines if escalation steps are due based on incident age
5. **Processes Escalations** - Executes escalation actions (notifications, assignments)
6. **Logs Results** - Records all activities in log files

## Troubleshooting

### Cron Job Not Running
1. Check if cron is enabled: `sudo launchctl list | grep cron`
2. Verify crontab: `crontab -l`
3. Check system logs: `sudo tail -f /var/log/system.log | grep cron`

### Script Errors
1. Check error logs: `tail -f logs/escalation_processor_error.log`
2. Verify virtual environment: `ls -la venv/bin/python`
3. Test manual run: `./scripts/run_escalation_processor.sh`

### Database Connection Issues
1. Verify database is running: `pg_isready -h localhost -p 5432`
2. Check database credentials in environment variables
3. Test connection manually

### Permission Issues
1. Ensure scripts are executable: `chmod +x scripts/*.sh`
2. Check file ownership: `ls -la scripts/`
3. Verify log directory permissions: `ls -la logs/`

## Removing the Cron Job

To remove the cron job:
```bash
crontab -e
# Delete the line with escalation_processor
# Save and exit
```

Or remove all cron jobs:
```bash
crontab -r
```

## Log Truncation

The log files can grow large over time. The system automatically truncates logs:

- **Automatic truncation**: Runs every hour via cron
- **Size threshold**: Logs are truncated when they exceed 10MB
- **Backup retention**: Keeps 24 compressed backup files (24 hours of history)
- **Backup location**: `logs/backups/` directory
- **Compression**: Old logs are automatically compressed with gzip

### Manual Truncation
```bash
# Truncate logs manually
./scripts/truncate_logs.sh

# View truncation log
tail -f logs/truncation.log

# View backup files
ls -la logs/backups/
```

### Configuration
You can modify the truncation settings in `scripts/truncate_logs.sh`:
- `MAX_LOG_SIZE="10M"` - Maximum log file size before truncation
- `BACKUP_COUNT=24` - Number of backup files to keep

## Security Considerations

1. **File Permissions** - Ensure log files are not world-readable
2. **Database Credentials** - Store database credentials securely
3. **Script Access** - Limit access to escalation scripts to authorized users
4. **Log Content** - Be aware that logs may contain sensitive information

## Performance Considerations

1. **Database Connections** - The script creates a new database connection each run
2. **Processing Time** - Monitor how long each run takes
3. **Log Size** - Regularly check log file sizes
4. **Resource Usage** - Monitor CPU and memory usage during processing

## Integration with Incident Management

The escalation processor integrates with the incident management system by:

1. **Reading Incidents** - Queries the incidents table for active incidents
2. **Checking Policies** - Matches incidents against escalation policies
3. **Creating Events** - Records escalation events in the database
4. **Sending Notifications** - Triggers notifications through the notification service
5. **Updating Assignments** - Assigns incidents to appropriate users

This ensures that incidents are automatically escalated according to defined policies, reducing manual intervention and improving response times.
