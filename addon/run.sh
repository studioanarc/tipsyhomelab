#!/usr/bin/with-contenv bashio
# ==============================================================================
# Wine Fermentation Monitor Add-on Entry Point
# ==============================================================================

set -e

# ------------------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------------------

# Print banner
print_banner() {
    bashio::log.info "Starting Wine Fermentation Monitor..."
    bashio::log.info "================================================"
    bashio::log.info "Version: $(bashio::addon.version)"
    bashio::log.info "Build: $(bashio::addon.build)"
    bashio::log.info "================================================"
}

# Check required configuration
check_configuration() {
    bashio::log.info "Validating configuration..."

    # Check MQTT host
    if ! bashio::config.has_value 'mqtt.host'; then
        bashio::log.fatal "MQTT host is not configured!"
        bashio::exit.nok
    fi

    # Check MQTT port
    if ! bashio::config.has_value 'mqtt.port'; then
        bashio::log.fatal "MQTT port is not configured!"
        bashio::exit.nok
    fi

    bashio::log.info "Configuration validated successfully"
}

# Set environment variables from config
set_environment() {
    bashio::log.info "Setting environment variables..."

    # Set configuration file path
    export CONFIG_PATH="/data/options.json"

    # Set data directories
    export DATA_DIR="/data"
    export MODELS_DIR="/data/models"
    export HISTORY_DIR="/data/history"
    export LOGS_DIR="/data/logs"

    # Set Home Assistant Supervisor environment
    export SUPERVISOR_TOKEN="${SUPERVISOR_TOKEN}"
    export HASSIO_TOKEN="${HASSIO_TOKEN}"

    # Set logging level
    export LOG_LEVEL="$(bashio::config 'logging.level')"

    # Set Python environment
    export PYTHONUNBUFFERED=1
    export PYTHONDONTWRITEBYTECODE=1
    export PYTHONIOENCODING=utf-8

    bashio::log.info "Environment configured"
}

# Create necessary directories
create_directories() {
    bashio::log.info "Creating data directories..."

    mkdir -p "${MODELS_DIR}" || bashio::exit.nok "Failed to create models directory"
    mkdir -p "${HISTORY_DIR}" || bashio::exit.nok "Failed to create history directory"
    mkdir -p "${LOGS_DIR}" || bashio::exit.nok "Failed to create logs directory"

    bashio::log.info "Data directories created"
}

# Wait for MQTT broker
wait_for_mqtt() {
    local mqtt_host
    local mqtt_port
    local max_attempts=30
    local attempt=0

    mqtt_host=$(bashio::config 'mqtt.host')
    mqtt_port=$(bashio::config 'mqtt.port')

    bashio::log.info "Waiting for MQTT broker at ${mqtt_host}:${mqtt_port}..."

    while [ ${attempt} -lt ${max_attempts} ]; do
        if nc -z "${mqtt_host}" "${mqtt_port}" > /dev/null 2>&1; then
            bashio::log.info "MQTT broker is ready"
            return 0
        fi

        attempt=$((attempt + 1))
        bashio::log.debug "Waiting for MQTT broker... (${attempt}/${max_attempts})"
        sleep 2
    done

    bashio::log.warning "MQTT broker not ready after ${max_attempts} attempts, continuing anyway..."
    return 0
}

# Start the application
start_application() {
    bashio::log.info "Starting Wine Fermentation Monitor service..."

    cd /app || bashio::exit.nok "Failed to change to /app directory"

    # Run the Python application
    exec python3 -u /app/main.py
}

# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------

main() {
    # Print banner
    print_banner

    # Check configuration
    check_configuration

    # Set environment variables
    set_environment

    # Create necessary directories
    create_directories

    # Wait for MQTT broker
    wait_for_mqtt

    # Start the application
    start_application
}

# Run main function
main "$@"
