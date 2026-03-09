#!/bin/bash
# Launch the ICC Code Development Platform
cd "$(dirname "$0")"
echo "Starting ICC Code Development Platform..."
echo "Dashboard: http://localhost:8000"
echo "Press Ctrl+C to stop"
python3 main.py
