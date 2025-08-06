#!/bin/bash

# Setup script for Carbon Daily Scheduler systemd service

SERVICE_NAME="green-moment-carbon-scheduler"
SERVICE_FILE="${SERVICE_NAME}.service"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Green Moment Carbon Scheduler Service Setup"
echo "=========================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)" 
   exit 1
fi

case "$1" in
    install)
        echo "Installing service..."
        
        # Copy service file to systemd directory
        cp "${SCRIPT_DIR}/${SERVICE_FILE}" /etc/systemd/system/
        
        # Reload systemd daemon
        systemctl daemon-reload
        
        # Enable service to start on boot
        systemctl enable ${SERVICE_NAME}
        
        # Start the service
        systemctl start ${SERVICE_NAME}
        
        echo "Service installed and started"
        echo "Check status with: sudo systemctl status ${SERVICE_NAME}"
        ;;
        
    uninstall)
        echo "Uninstalling service..."
        
        # Stop the service
        systemctl stop ${SERVICE_NAME}
        
        # Disable service
        systemctl disable ${SERVICE_NAME}
        
        # Remove service file
        rm -f /etc/systemd/system/${SERVICE_FILE}
        
        # Reload systemd daemon
        systemctl daemon-reload
        
        echo "Service uninstalled"
        ;;
        
    status)
        systemctl status ${SERVICE_NAME}
        ;;
        
    start)
        systemctl start ${SERVICE_NAME}
        echo "Service started"
        ;;
        
    stop)
        systemctl stop ${SERVICE_NAME}
        echo "Service stopped"
        ;;
        
    restart)
        systemctl restart ${SERVICE_NAME}
        echo "Service restarted"
        ;;
        
    logs)
        echo "=== Recent logs ==="
        journalctl -u ${SERVICE_NAME} -n 50 --no-pager
        ;;
        
    follow)
        echo "=== Following logs (Ctrl+C to exit) ==="
        journalctl -u ${SERVICE_NAME} -f
        ;;
        
    *)
        echo "Usage: sudo $0 {install|uninstall|status|start|stop|restart|logs|follow}"
        echo ""
        echo "  install    - Install and start the service"
        echo "  uninstall  - Stop and remove the service"
        echo "  status     - Show service status"
        echo "  start      - Start the service"
        echo "  stop       - Stop the service"
        echo "  restart    - Restart the service"
        echo "  logs       - Show recent logs"
        echo "  follow     - Follow logs in real-time"
        exit 1
        ;;
esac