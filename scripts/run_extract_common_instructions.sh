#!/bin/bash
# Run the extract_common_instructions.py script

# Make script exit on first error
set -e

# Print commands before executing them
set -x

# Go to project root directory
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

echo "Running extract_common_instructions.py in $PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    if [[ "$OSTYPE" == "darwin"* || "$OSTYPE" == "linux-gnu"* ]]; then
        # macOS or Linux
        source venv/bin/activate
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        # Windows
        source venv/Scripts/activate
    fi
fi

# Run the script
python scripts/extract_common_instructions.py

echo "Finished extracting common instructions!" 