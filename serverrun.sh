#!/bin/bash

while true; do
    echo "Starting server..."
    bash run.sh
    
    echo "Server stopped with exit code $?"
    echo "Restarting in 10 seconds... (Ctrl+C to cancel)"
    sleep 10
done
