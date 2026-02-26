#!/bin/bash

# Travel Backend Test Runner Script
# This script provides easy commands to run different types of tests

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Travel Backend Test Runner ===${NC}\n"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

case "$1" in
    "all")
        echo -e "${GREEN}Running all tests...${NC}"
        python manage.py test --settings=core.settings.test
        ;;
    "api")
        echo -e "${GREEN}Running API tests...${NC}"
        python manage.py test apps.user_account.tests.test_api --settings=core.settings.test
        ;;
    "coverage")
        echo -e "${GREEN}Running tests with coverage...${NC}"
        coverage run --source='.' manage.py test apps.user_account.tests.test_api --settings=core.settings.test
        echo -e "\n${YELLOW}Coverage Report:${NC}"
        coverage report
        ;;
    "coverage-html")
        echo -e "${GREEN}Running tests with HTML coverage report...${NC}"
        coverage run --source='.' manage.py test apps.user_account.tests.test_api --settings=core.settings.test
        coverage html
        echo -e "\n${YELLOW}HTML coverage report generated in htmlcov/index.html${NC}"
        ;;
    "verbose")
        echo -e "${GREEN}Running tests with verbose output...${NC}"
        python manage.py test apps.user_account.tests.test_api --settings=core.settings.test -v 2
        ;;
    "fast")
        echo -e "${GREEN}Running tests with keepdb (faster)...${NC}"
        python manage.py test apps.user_account.tests.test_api --settings=core.settings.test --keepdb
        ;;
    *)
        echo -e "${YELLOW}Usage:${NC}"
        echo "  ./run_tests.sh all              - Run all tests"
        echo "  ./run_tests.sh api              - Run API tests only"
        echo "  ./run_tests.sh coverage         - Run tests with coverage report"
        echo "  ./run_tests.sh coverage-html    - Run tests with HTML coverage report"
        echo "  ./run_tests.sh verbose          - Run tests with verbose output"
        echo "  ./run_tests.sh fast             - Run tests with keepdb (faster)"
        echo ""
        echo -e "${YELLOW}Examples:${NC}"
        echo "  ./run_tests.sh api"
        echo "  ./run_tests.sh coverage"
        ;;
esac
