#!/bin/bash

# Change to the project directory
cd /Users/felipe/code/icarus/screentime2notion

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run the sync command
python3 -m src.main sync --days 7 >> sync.log 2>&1