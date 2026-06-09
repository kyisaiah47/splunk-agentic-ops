#!/bin/bash
# Exposes the FastAPI backend publicly for the Vercel frontend to call.
# Backend: https://splunk-agentic-ops-api.loca.lt → localhost:9000

echo "Starting backend tunnel..."
lt --port 9000 --subdomain splunk-agentic-ops-api
