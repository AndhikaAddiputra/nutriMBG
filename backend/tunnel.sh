#!/bin/bash
# tunnel.sh — Auto-restarting HTTPS tunnel for NutriMBG backend
# Usage: ./backend/tunnel.sh

BACKEND_PORT=8000
TUNNEL_URL_FILE="backend/tunnel_url.txt"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "=== NutriMBG Tunnel ==="
log "Backend: localhost:$BACKEND_PORT"

while true; do
  if command -v cloudflared &>/dev/null; then
    # Method 1: cloudflared (preferred)
    log "Starting cloudflared tunnel..."
    CLOUD_OUTPUT=$(mktemp)
    cloudflared tunnel --url "http://localhost:$BACKEND_PORT" 2>&1 | tee "$CLOUD_OUTPUT" &
    CLOUD_PID=$!
    
    # Wait for URL, extract it
    sleep 5
    TUNNEL_URL=$(grep -o 'https://[a-z0-9.-]*\.trycloudflare\.com' "$CLOUD_OUTPUT" 2>/dev/null | head -1)
    
    if [ -n "$TUNNEL_URL" ]; then
      echo "$TUNNEL_URL" > "$TUNNEL_URL_FILE"
      log "================================"
      log "  PUBLIC URL: $TUNNEL_URL"
      log "  Saved to: $TUNNEL_URL_FILE"
      log "================================"
    fi

    # Follow logs, restart when tunnel exits
    wait $CLOUD_PID 2>/dev/null
    rm -f "$CLOUD_OUTPUT"
    log "cloudflared disconnected."
  fi

  log "Restarting in 3 seconds..."
  sleep 3
done
