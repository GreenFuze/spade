#!/bin/bash
# Manual Codex Test Script for MetaFFI RIG Debugging
# This script runs Codex with the generated prompt to debug timeout issues

set -e

echo "=== Manual Codex Test for MetaFFI RIG ==="
echo ""

# Configuration
WORKSPACE_BASE="/mnt/c/src/github.com/GreenFuze/spade/tests/deterministic/wsl_runners/_codex_workspace"
REPO_NAME="metaffi"
REPO_PATH="${WORKSPACE_BASE}/${REPO_NAME}"
PROMPT_FILE="/mnt/c/src/github.com/GreenFuze/spade/tests/deterministic/wsl_runners/_cursor_workspace/theprompt.txt"

# Check if prompt file exists
if [ ! -f "$PROMPT_FILE" ]; then
    echo "ERROR: Prompt file not found at: $PROMPT_FILE"
    exit 1
fi

# Check if codex is available
if ! command -v codex &> /dev/null; then
    echo "ERROR: 'codex' command not found. Please ensure Codex is installed and in PATH."
    exit 1
fi

# Display prompt stats
PROMPT_SIZE=$(wc -c < "$PROMPT_FILE")
echo "Prompt file: $PROMPT_FILE"
echo "Prompt size: $PROMPT_SIZE bytes ($(echo "scale=1; $PROMPT_SIZE/1024" | bc) KB)"
echo ""

# Check if workspace directory exists
if [ ! -d "$REPO_PATH" ]; then
    echo "WARNING: Repository not found at: $REPO_PATH"
    echo "You may need to copy it from: /mnt/c/src/github.com/GreenFuze/spade/tests/test_repos/cmake/metaffi"
    echo ""
    read -p "Press Enter to continue anyway, or Ctrl+C to cancel..."
fi

# Change to repository directory
cd "$REPO_PATH"
echo "Working directory: $(pwd)"
echo ""

# Run Codex with the prompt
echo "Starting Codex..."
echo "----------------------------------------"
echo ""

# Read the prompt and pass it to codex
time codex exec "$(cat $PROMPT_FILE)"

echo ""
echo "----------------------------------------"
echo "Codex finished!"
echo ""

# Check if answers.json was created
if [ -f "$REPO_PATH/answers.json" ]; then
    echo "SUCCESS: answers.json was created"
    echo "File size: $(wc -c < "$REPO_PATH/answers.json") bytes"
    echo ""
    echo "Preview:"
    head -20 "$REPO_PATH/answers.json"
else
    echo "WARNING: answers.json was NOT created"
fi
