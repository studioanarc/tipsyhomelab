#!/bin/bash

###############################################################################
# Wine Monitor Test Environment Setup Script
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Functions
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

print_header() {
    echo ""
    echo "========================================"
    echo "$1"
    echo "========================================"
    echo ""
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check for Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        print_success "Python installed: $PYTHON_VERSION"
    else
        print_error "Python 3 is not installed"
        exit 1
    fi

    # Check for pip
    if command -v pip3 &> /dev/null; then
        print_success "pip3 is installed"
    else
        print_error "pip3 is not installed"
        exit 1
    fi

    # Check for Docker (optional)
    if command -v docker &> /dev/null; then
        print_success "Docker is installed"
        HAS_DOCKER=true
    else
        print_info "Docker is not installed (optional)"
        HAS_DOCKER=false
    fi

    # Check for Docker Compose (optional)
    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
        print_success "Docker Compose is installed"
        HAS_DOCKER_COMPOSE=true
    else
        print_info "Docker Compose is not installed (optional)"
        HAS_DOCKER_COMPOSE=false
    fi
}

# Create virtual environment
create_venv() {
    print_header "Creating Virtual Environment"

    cd "$PROJECT_ROOT"

    if [ -d "venv" ]; then
        print_info "Virtual environment already exists"
        read -p "Do you want to recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf venv
            python3 -m venv venv
            print_success "Virtual environment recreated"
        fi
    else
        python3 -m venv venv
        print_success "Virtual environment created"
    fi
}

# Install dependencies
install_dependencies() {
    print_header "Installing Dependencies"

    cd "$PROJECT_ROOT"

    # Activate virtual environment
    source venv/bin/activate

    # Upgrade pip
    print_info "Upgrading pip..."
    pip install --upgrade pip

    # Install development dependencies
    if [ -f "requirements-dev.txt" ]; then
        print_info "Installing development dependencies..."
        pip install -r requirements-dev.txt
        print_success "Development dependencies installed"
    else
        print_info "Creating requirements-dev.txt..."
        cat > requirements-dev.txt << EOF
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.0
pytest-homeassistant-custom-component>=0.13.0
black>=23.7.0
isort>=5.12.0
flake8>=6.1.0
mypy>=1.5.0
pylint>=2.17.0
pre-commit>=3.3.0
paho-mqtt>=1.6.1
numpy>=1.24.0
pandas>=2.0.0
scikit-learn>=1.3.0
EOF
        pip install -r requirements-dev.txt
        print_success "Development dependencies installed"
    fi

    # Install main dependencies
    if [ -f "requirements.txt" ]; then
        print_info "Installing main dependencies..."
        pip install -r requirements.txt
        print_success "Main dependencies installed"
    fi
}

# Setup Docker environment
setup_docker() {
    if [ "$HAS_DOCKER" = false ] || [ "$HAS_DOCKER_COMPOSE" = false ]; then
        print_info "Skipping Docker setup (not available)"
        return
    fi

    print_header "Setting up Docker Environment"

    cd "$PROJECT_ROOT"

    # Create necessary directories
    mkdir -p docker/mosquitto/{config,data,log}
    mkdir -p docker/postgres/init
    mkdir -p docker/grafana/provisioning

    # Create Mosquitto config
    if [ ! -f "docker/mosquitto/config/mosquitto.conf" ]; then
        print_info "Creating Mosquitto configuration..."
        cat > docker/mosquitto/config/mosquitto.conf << EOF
listener 1883
allow_anonymous true
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
log_dest stdout
EOF
        print_success "Mosquitto configuration created"
    fi

    # Create PostgreSQL init script
    if [ ! -f "docker/postgres/init/init.sql" ]; then
        print_info "Creating PostgreSQL init script..."
        cat > docker/postgres/init/init.sql << EOF
-- Wine Monitor Database Schema

CREATE TABLE IF NOT EXISTS batches (
    batch_id VARCHAR(50) PRIMARY KEY,
    batch_name VARCHAR(100) NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    initial_gravity FLOAT NOT NULL,
    final_gravity FLOAT,
    target_gravity FLOAT,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sensors (
    sensor_id VARCHAR(50) PRIMARY KEY,
    sensor_type VARCHAR(20) NOT NULL,
    sensor_name VARCHAR(100),
    calibration JSONB,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sensor_readings (
    id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(50) REFERENCES sensors(sensor_id),
    batch_id VARCHAR(50) REFERENCES batches(batch_id),
    timestamp TIMESTAMP NOT NULL,
    temperature FLOAT,
    gravity FLOAT,
    battery FLOAT,
    angle FLOAT,
    bubble_count INTEGER,
    bubble_rate FLOAT,
    rssi INTEGER,
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    batch_id VARCHAR(50) REFERENCES batches(batch_id),
    timestamp TIMESTAMP NOT NULL,
    completion_percentage FLOAT,
    confidence FLOAT,
    estimated_finish_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_readings_timestamp ON sensor_readings(timestamp);
CREATE INDEX IF NOT EXISTS idx_readings_sensor ON sensor_readings(sensor_id);
CREATE INDEX IF NOT EXISTS idx_readings_batch ON sensor_readings(batch_id);
CREATE INDEX IF NOT EXISTS idx_predictions_batch ON predictions(batch_id);

-- Sample data
INSERT INTO sensors (sensor_id, sensor_type, sensor_name)
VALUES
    ('ispindel_001', 'ispindel', 'iSpindel Fermenter A'),
    ('bubble_001', 'bubble', 'Bubble Counter A')
ON CONFLICT DO NOTHING;

INSERT INTO batches (batch_id, batch_name, start_date, initial_gravity, target_gravity, status)
VALUES
    ('test_batch_001', 'Test Chardonnay 2024', CURRENT_TIMESTAMP, 1.085, 1.008, 'active')
ON CONFLICT DO NOTHING;
EOF
        print_success "PostgreSQL init script created"
    fi

    print_success "Docker environment configured"
}

# Create test data directory structure
setup_test_directories() {
    print_header "Setting up Test Directories"

    cd "$PROJECT_ROOT"

    mkdir -p tests/fixtures
    mkdir -p tests/integration
    mkdir -p custom_components/wine_monitor

    print_success "Test directories created"
}

# Setup pre-commit hooks
setup_precommit() {
    print_header "Setting up Pre-commit Hooks"

    cd "$PROJECT_ROOT"

    # Activate virtual environment
    source venv/bin/activate

    if [ -f ".pre-commit-config.yaml" ]; then
        print_info "Installing pre-commit hooks..."
        pre-commit install
        print_success "Pre-commit hooks installed"
    else
        print_info ".pre-commit-config.yaml not found, skipping..."
    fi
}

# Run initial tests
run_tests() {
    print_header "Running Initial Tests"

    cd "$PROJECT_ROOT"

    # Activate virtual environment
    source venv/bin/activate

    if [ -d "tests" ]; then
        print_info "Running pytest..."
        pytest tests/ -v || print_info "Some tests failed (expected if components not yet implemented)"
        print_success "Test run completed"
    else
        print_info "No tests directory found, skipping..."
    fi
}

# Start Docker services
start_docker_services() {
    if [ "$HAS_DOCKER" = false ] || [ "$HAS_DOCKER_COMPOSE" = false ]; then
        print_info "Skipping Docker services (not available)"
        return
    fi

    print_header "Starting Docker Services"

    cd "$PROJECT_ROOT"

    read -p "Do you want to start Docker services? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Starting services..."
        docker-compose up -d mqtt postgres
        sleep 5
        print_success "Docker services started"
        print_info "MQTT Broker: localhost:1883"
        print_info "PostgreSQL: localhost:5432"
        print_info "Adminer: http://localhost:8080"
    fi
}

# Print summary
print_summary() {
    print_header "Setup Complete!"

    echo "Next steps:"
    echo ""
    echo "1. Activate virtual environment:"
    echo "   source venv/bin/activate"
    echo ""
    echo "2. Run tests:"
    echo "   pytest tests/ -v"
    echo ""
    echo "3. Start all Docker services:"
    echo "   docker-compose up -d"
    echo ""
    echo "4. Access services:"
    echo "   - Home Assistant: http://localhost:8123"
    echo "   - Grafana: http://localhost:3000 (admin/admin)"
    echo "   - Adminer: http://localhost:8080"
    echo ""
    echo "5. Format code:"
    echo "   black ."
    echo "   isort ."
    echo ""
    echo "6. Run linters:"
    echo "   flake8 ."
    echo "   pylint custom_components/"
    echo ""
    print_success "Happy coding!"
}

# Main execution
main() {
    print_header "Wine Monitor Test Environment Setup"

    check_prerequisites
    create_venv
    install_dependencies
    setup_test_directories
    setup_docker
    setup_precommit
    run_tests
    start_docker_services
    print_summary
}

# Run main function
main
