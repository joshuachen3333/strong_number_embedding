#!/bin/bash
# Start a simple HTTP server and open the showoff viewer
cd "$(dirname "$0")/.." || exit 1
echo "Starting server at http://localhost:8989/showoff_finished_4review/"
echo "Press Ctrl+C to stop"
python3 -m http.server 8989
