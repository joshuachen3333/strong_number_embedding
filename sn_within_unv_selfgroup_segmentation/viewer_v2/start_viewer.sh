#!/bin/bash
# start_viewer.sh
# Start HTTP server and open Parsed Verse Viewer in browser

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PORT=8000

echo "========================================="
echo "  Parsed Verse Viewer"
echo "========================================="
echo ""

# Check if manifest exists
MANIFEST_PATH="$SCRIPT_DIR/../output/manifest.json"
if [ ! -f "$MANIFEST_PATH" ]; then
  echo "Warning: manifest.json not found at $MANIFEST_PATH"
  echo "Please run: python generate_manifest.py"
  echo ""
  read -p "Continue anyway? (y/n) " -n 1 -r
  echo ""
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
else
  # Check if manifest is recent
  MANIFEST_AGE=$(find "$MANIFEST_PATH" -mtime +1 2>/dev/null)
  if [ -n "$MANIFEST_AGE" ]; then
    echo "Note: manifest.json is more than 1 day old"
    echo "Consider running: python generate_manifest.py"
    echo ""
  fi
fi

# Change to parent directory (where output/ is)
cd "$SCRIPT_DIR/.."

# Check if port is already in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
  echo "Port $PORT is already in use."
  echo "Opening browser to existing server..."
  echo ""
else
  echo "Starting HTTP server on port $PORT..."
  python3 -m http.server $PORT >/dev/null 2>&1 &
  SERVER_PID=$!
  echo "Server started (PID: $SERVER_PID)"
  echo ""

  # Wait a moment for server to start
  sleep 1
fi

# Open browser
URL="http://localhost:$PORT/viewer_v2/"
echo "Opening viewer at: $URL"
echo ""

if command -v open >/dev/null 2>&1; then
  # macOS
  open "$URL"
elif command -v xdg-open >/dev/null 2>&1; then
  # Linux
  xdg-open "$URL"
elif command -v start >/dev/null 2>&1; then
  # Windows
  start "$URL"
else
  echo "Please open your browser and navigate to:"
  echo "  $URL"
fi

echo ""
echo "========================================="
echo "  Server is running"
echo "  Press Ctrl+C to stop"
echo "========================================="

# Keep script running
if [ -n "$SERVER_PID" ]; then
  trap "echo ''; echo 'Stopping server...'; kill $SERVER_PID 2>/dev/null; exit 0" INT TERM
  wait $SERVER_PID
else
  echo ""
  echo "(Server was already running, this script will exit)"
fi
