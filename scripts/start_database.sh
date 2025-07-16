#!/bin/bash

# AI Investment Tool - Database Management Script
# This script helps manage the PostgreSQL database using Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}AI Investment Tool - Database Manager${NC}"
echo "Project directory: $PROJECT_DIR"
echo

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}Error: Docker is not running. Please start Docker first.${NC}"
        exit 1
    fi
}

# Function to check if Docker Compose is available
check_docker_compose() {
    if ! command -v docker-compose >/dev/null 2>&1 && ! docker compose version >/dev/null 2>&1; then
        echo -e "${RED}Error: Docker Compose is not available.${NC}"
        exit 1
    fi
    
    # Use 'docker compose' if available (newer syntax), otherwise 'docker-compose'
    if docker compose version >/dev/null 2>&1; then
        DOCKER_COMPOSE="docker compose"
    else
        DOCKER_COMPOSE="docker-compose"
    fi
}

# Function to start the database
start_database() {
    echo -e "${YELLOW}Starting PostgreSQL database...${NC}"
    cd "$PROJECT_DIR"
    
    $DOCKER_COMPOSE up -d postgres
    
    echo -e "${GREEN}Waiting for database to be ready...${NC}"
    
    # Wait for PostgreSQL to be ready
    for i in {1..30}; do
        if $DOCKER_COMPOSE exec postgres pg_isready -U ai_user -d ai_investment >/dev/null 2>&1; then
            echo -e "${GREEN}✓ Database is ready!${NC}"
            break
        fi
        
        if [ $i -eq 30 ]; then
            echo -e "${RED}✗ Database failed to start within 30 seconds${NC}"
            exit 1
        fi
        
        echo -n "."
        sleep 1
    done
    
    echo
    echo -e "${GREEN}PostgreSQL is running on localhost:5432${NC}"
    echo -e "${BLUE}Database: ai_investment${NC}"
    echo -e "${BLUE}Username: ai_user${NC}"
    echo -e "${BLUE}Password: ai_password${NC}"
}

# Function to start pgAdmin
start_pgadmin() {
    echo -e "${YELLOW}Starting pgAdmin...${NC}"
    cd "$PROJECT_DIR"
    
    $DOCKER_COMPOSE up -d pgadmin
    
    echo -e "${GREEN}✓ pgAdmin is starting...${NC}"
    echo -e "${BLUE}pgAdmin URL: http://localhost:8080${NC}"
    echo -e "${BLUE}Email: admin@example.com${NC}"
    echo -e "${BLUE}Password: admin123${NC}"
    echo
    echo -e "${YELLOW}Note: It may take a minute for pgAdmin to be fully available.${NC}"
}

# Function to stop services
stop_services() {
    echo -e "${YELLOW}Stopping database services...${NC}"
    cd "$PROJECT_DIR"
    
    $DOCKER_COMPOSE down
    echo -e "${GREEN}✓ Services stopped${NC}"
}

# Function to show status
show_status() {
    echo -e "${YELLOW}Service Status:${NC}"
    cd "$PROJECT_DIR"
    
    $DOCKER_COMPOSE ps
}

# Function to show logs
show_logs() {
    echo -e "${YELLOW}Recent logs:${NC}"
    cd "$PROJECT_DIR"
    
    $DOCKER_COMPOSE logs --tail=50
}

# Function to reset database
reset_database() {
    echo -e "${RED}WARNING: This will delete all data in the database!${NC}"
    read -p "Are you sure you want to continue? (yes/no): " -r
    echo
    
    if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo -e "${YELLOW}Resetting database...${NC}"
        cd "$PROJECT_DIR"
        
        $DOCKER_COMPOSE down
        docker volume rm ai_investment_tool_postgres_data 2>/dev/null || true
        $DOCKER_COMPOSE up -d postgres
        
        # Wait for database to be ready
        echo -e "${YELLOW}Waiting for database to initialize...${NC}"
        sleep 10
        
        echo -e "${GREEN}✓ Database reset complete${NC}"
    else
        echo -e "${BLUE}Database reset cancelled${NC}"
    fi
}

# Function to backup database
backup_database() {
    echo -e "${YELLOW}Creating database backup...${NC}"
    
    BACKUP_DIR="$PROJECT_DIR/backups"
    mkdir -p "$BACKUP_DIR"
    
    BACKUP_FILE="$BACKUP_DIR/ai_investment_backup_$(date +%Y%m%d_%H%M%S).sql"
    
    cd "$PROJECT_DIR"
    $DOCKER_COMPOSE exec -T postgres pg_dump -U ai_user ai_investment > "$BACKUP_FILE"
    
    echo -e "${GREEN}✓ Database backup saved to: $BACKUP_FILE${NC}"
}

# Function to show help
show_help() {
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  start       Start PostgreSQL database"
    echo "  start-all   Start both PostgreSQL and pgAdmin"
    echo "  stop        Stop all services"
    echo "  restart     Restart all services"
    echo "  status      Show service status"
    echo "  logs        Show recent logs"
    echo "  reset       Reset database (WARNING: deletes all data)"
    echo "  backup      Create database backup"
    echo "  shell       Open PostgreSQL shell"
    echo "  help        Show this help message"
    echo
    echo "Examples:"
    echo "  $0 start       # Start just the database"
    echo "  $0 start-all   # Start database and pgAdmin"
    echo "  $0 backup      # Create a backup before making changes"
    echo "  $0 shell       # Connect to database for manual queries"
}

# Function to open database shell
open_shell() {
    echo -e "${YELLOW}Opening PostgreSQL shell...${NC}"
    echo -e "${BLUE}Connected to database 'ai_investment' as user 'ai_user'${NC}"
    echo -e "${BLUE}Type \\q to exit${NC}"
    echo
    
    cd "$PROJECT_DIR"
    $DOCKER_COMPOSE exec postgres psql -U ai_user -d ai_investment
}

# Main script logic
check_docker
check_docker_compose

case "${1:-}" in
    "start")
        start_database
        ;;
    "start-all")
        start_database
        start_pgadmin
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        stop_services
        sleep 2
        start_database
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "reset")
        reset_database
        ;;
    "backup")
        backup_database
        ;;
    "shell")
        open_shell
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    "")
        echo -e "${YELLOW}No command specified. Starting database...${NC}"
        echo -e "${BLUE}Use '$0 help' to see all available commands.${NC}"
        echo
        start_database
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo
        show_help
        exit 1
        ;;
esac 