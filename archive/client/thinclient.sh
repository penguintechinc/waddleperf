#!/usr/bin/env bash

set -e

function usage() {
    echo "Usage: $(basename "$0") [OPTIONS]"
    echo "  -c, --console       Log to console"
    echo "      --logfile=PATH  Specify log file path"
    echo "  -j, --json          Log as JSON"
    echo "  -h, --help          Show help"
    exit 1
}

LOG_TO_CONSOLE=false
LOG_FILE_PATH="logs/thinclient.log"
LOG_AS_JSON=false

for arg in "$@"; do
    case $arg in
        -c|--console)
            LOG_TO_CONSOLE=true
            shift
            ;;
        --logfile=*)
            LOG_FILE_PATH="${arg#*=}"
            if [ ! -d "$(dirname "$LOG_FILE_PATH")" ]; then
                echo "Log file directory does not exist."
                exit 1
            fi
            shift
            ;;
        -j|--json)
            LOG_AS_JSON=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Invalid option: $arg"
            usage
            ;;
    esac
done

echo "Configuring logging..."
if [ "$LOG_TO_CONSOLE" = false ]; then
    touch "$LOG_FILE_PATH"
fi

echo "Running setup..."
bash vars/thinclientvariables.sh || {
    echo "Setup script failed."
    exit 1
}

echo "Validating installation..."
pping --version || {
    echo "Installation check failed."
    exit 1
}

echo "Starting background service..."
nohup py4web run web/apps &>/dev/null &

echo "Running configuration..."
ansible-playbook entrypoint.yml -c local --tags thinclient || {
    echo "Configuration failed."
    exit 1
}

echo "Done."