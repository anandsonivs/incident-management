#!/bin/bash

# Elastic APM Alert Setup Script
# This script sets up comprehensive monitoring alerts for all services in Elastic APM
# and integrates them with the incident management system.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to validate URL
validate_url() {
    if [[ $1 =~ ^https?:// ]]; then
        return 0
    else
        return 1
    fi
}

# Function to check if incident management API is accessible
check_incident_api() {
    local api_url=$1
    local token=$2
    
    print_status "Checking incident management API connectivity..."
    
    if curl -s -f -H "Authorization: Bearer $token" "$api_url/health" >/dev/null 2>&1; then
        print_success "Incident management API is accessible"
        return 0
    else
        print_error "Cannot connect to incident management API at $api_url"
        return 1
    fi
}

# Function to check if Elastic APM is accessible
check_elastic_api() {
    local elastic_url=$1
    local api_key=$2
    
    print_status "Checking Elastic APM connectivity..."
    
    if curl -s -f -H "Authorization: ApiKey $api_key" "$elastic_url/api/apm/services" >/dev/null 2>&1; then
        print_success "Elastic APM is accessible"
        return 0
    else
        print_error "Cannot connect to Elastic APM at $elastic_url"
        return 1
    fi
}

# Function to create environment file
create_env_file() {
    local env_file=".elastic_alerts.env"
    
    if [ -f "$env_file" ]; then
        print_warning "Environment file $env_file already exists. Backing up..."
        cp "$env_file" "${env_file}.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    cat > "$env_file" << EOF
# Elastic APM Configuration
ELASTIC_URL=""
ELASTIC_API_KEY=""

# Incident Management Configuration
INCIDENT_API_URL=""
INCIDENT_API_TOKEN=""

# Alert Configuration
ENVIRONMENT="production"
TEAM_MAPPING_FILE="config/team_mapping.json"
ALERT_THRESHOLDS_FILE="config/alert_thresholds.json"

# Optional Configuration
SERVICE_PATTERN=""
DRY_RUN="false"
EOF

    print_success "Created environment file: $env_file"
    print_status "Please edit $env_file with your configuration values"
}

# Function to run dry run
run_dry_run() {
    local env_file=".elastic_alerts.env"
    
    if [ ! -f "$env_file" ]; then
        print_error "Environment file $env_file not found. Please run setup first."
        exit 1
    fi
    
    # Source environment variables
    source "$env_file"
    
    print_status "Running dry run to preview alert creation..."
    
    python3 scripts/create_elastic_alerts.py \
        --elastic-url "$ELASTIC_URL" \
        --elastic-api-key "$ELASTIC_API_KEY" \
        --incident-api-url "$INCIDENT_API_URL" \
        --incident-api-token "$INCIDENT_API_TOKEN" \
        --team-mapping "$TEAM_MAPPING_FILE" \
        --environment "$ENVIRONMENT" \
        --dry-run \
        ${SERVICE_PATTERN:+--service-pattern "$SERVICE_PATTERN"}
}

# Function to create alerts
create_alerts() {
    local env_file=".elastic_alerts.env"
    
    if [ ! -f "$env_file" ]; then
        print_error "Environment file $env_file not found. Please run setup first."
        exit 1
    fi
    
    # Source environment variables
    source "$env_file"
    
    print_status "Creating Elastic APM alerts..."
    
    python3 scripts/create_elastic_alerts.py \
        --elastic-url "$ELASTIC_URL" \
        --elastic-api-key "$ELASTIC_API_KEY" \
        --incident-api-url "$INCIDENT_API_URL" \
        --incident-api-token "$INCIDENT_API_TOKEN" \
        --team-mapping "$TEAM_MAPPING_FILE" \
        --environment "$ENVIRONMENT" \
        ${SERVICE_PATTERN:+--service-pattern "$SERVICE_PATTERN"}
}

# Function to show help
show_help() {
    echo "Elastic APM Alert Setup Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup      - Initial setup and configuration"
    echo "  dry-run    - Run in dry-run mode to preview changes"
    echo "  create     - Create alerts for all services"
    echo "  help       - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup                    # Initial setup"
    echo "  $0 dry-run                  # Preview alert creation"
    echo "  $0 create                   # Create all alerts"
    echo "  $0 dry-run --service-pattern 'api.*'  # Preview for API services only"
    echo ""
    echo "Configuration:"
    echo "  Edit .elastic_alerts.env to configure your settings"
    echo "  Edit config/team_mapping.json to customize team assignments"
    echo "  Edit config/alert_thresholds.json to customize alert thresholds"
}

# Main script logic
case "${1:-help}" in
    "setup")
        print_status "Starting Elastic APM Alert Setup..."
        
        # Check dependencies
        if ! command_exists python3; then
            print_error "Python 3 is required but not installed"
            exit 1
        fi
        
        if ! command_exists curl; then
            print_error "curl is required but not installed"
            exit 1
        fi
        
        # Check if required files exist
        if [ ! -f "scripts/create_elastic_alerts.py" ]; then
            print_error "Alert creation script not found: scripts/create_elastic_alerts.py"
            exit 1
        fi
        
        if [ ! -f "config/team_mapping.json" ]; then
            print_error "Team mapping file not found: config/team_mapping.json"
            exit 1
        fi
        
        if [ ! -f "config/alert_thresholds.json" ]; then
            print_error "Alert thresholds file not found: config/alert_thresholds.json"
            exit 1
        fi
        
        # Create environment file
        create_env_file
        
        print_success "Setup completed!"
        print_status "Next steps:"
        print_status "1. Edit .elastic_alerts.env with your configuration"
        print_status "2. Run '$0 dry-run' to preview alert creation"
        print_status "3. Run '$0 create' to create all alerts"
        ;;
    
    "dry-run")
        print_status "Running dry run..."
        run_dry_run
        ;;
    
    "create")
        print_status "Creating alerts..."
        
        # Confirm before creating
        echo ""
        print_warning "This will create alerts for ALL services in Elastic APM."
        print_warning "Make sure you have reviewed the configuration and run dry-run first."
        echo ""
        read -p "Are you sure you want to continue? (y/N): " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            create_alerts
        else
            print_status "Alert creation cancelled."
        fi
        ;;
    
    "help"|*)
        show_help
        ;;
esac
