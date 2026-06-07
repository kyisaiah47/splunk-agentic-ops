#!/bin/bash
# Starts public localtunnel URLs for both the backend and frontend.
# Backend:  https://splunk-agentic-ops-api.loca.lt → localhost:9000
# Frontend: https://splunk-agentic-ops.loca.lt     → localhost:3002

echo "Starting tunnels..."
lt --port 9000 --subdomain splunk-agentic-ops-api &
lt --port 3002 --subdomain splunk-agentic-ops &
wait
