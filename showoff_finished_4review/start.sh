#!/bin/bash
# Start the review server and open the showoff viewer
cd "$(dirname "$0")/.." || exit 1
python3 start_server.py --port 8989
