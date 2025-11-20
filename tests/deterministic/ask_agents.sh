#!/bin/bash
#
# Interactive agent execution script for WSL
#
# This script automates the repetitive parts of running agents while giving
# you full visibility and control over agent execution.
#
# Usage: ./ask_agents.sh
#

set -e  # Fail-fast on any error
set -u  # Fail on undefined variables

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTS_ROOT="$(dirname "$SCRIPT_DIR")"
HELPER="$SCRIPT_DIR/ask_agents_shell_helper.py"

# Agent commands (available in WSL)
AGENTS=("claude" "codex" "cursor-agent")
MODES=("NORIG" "RIG")

echo "================================================================================"
echo "INTERACTIVE AGENT EXECUTION"
echo "================================================================================"
echo "Script directory: $SCRIPT_DIR"
echo "Tests root: $TESTS_ROOT"
echo ""

# Validate required tools and files
echo "Validating environment..."

if [ ! -f "$HELPER" ]; then
    echo -e "${RED}ERROR: Helper script not found: $HELPER${NC}"
    echo "Expected location: tests/deterministic/ask_agents_shell_helper.py"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: python3 not found in PATH${NC}"
    echo "Please install python3 or ensure it's in your PATH"
    exit 1
fi

if ! command -v clip.exe &> /dev/null; then
    echo -e "${RED}ERROR: clip.exe not found${NC}"
    echo "This script requires Windows clipboard (clip.exe) to work in WSL"
    exit 1
fi

# Check if agents are available
for AGENT in "${AGENTS[@]}"; do
    if ! command -v "$AGENT" &> /dev/null; then
        echo -e "${YELLOW}WARNING: Agent '$AGENT' not found in PATH${NC}"
        echo "You may encounter errors when trying to launch this agent"
    fi
done

echo -e "${GREEN}✓ Environment validation passed${NC}"
echo ""

# Get list of repositories
echo "Loading repositories..."
REPOS_OUTPUT=$(python3 "$HELPER" list_repos 2>&1)
PYTHON_EXIT_CODE=$?

if [ $PYTHON_EXIT_CODE -ne 0 ]; then
    echo -e "${RED}ERROR: Failed to load repositories${NC}"
    echo "Command: python3 $HELPER list_repos"
    echo "Output: $REPOS_OUTPUT"
    exit 1
fi

REPOS=($REPOS_OUTPUT)

if [ ${#REPOS[@]} -eq 0 ]; then
    echo -e "${RED}ERROR: No repositories found${NC}"
    echo "Check config.py to ensure REPOS is populated"
    exit 1
fi

echo "Found ${#REPOS[@]} repositories to process"
echo ""

# Process each repository
for REPO_IDX in "${!REPOS[@]}"; do
    REPO="${REPOS[$REPO_IDX]}"
    REPO_NUM=$((REPO_IDX + 1))
    TOTAL_REPOS=${#REPOS[@]}

    echo "================================================================================"
    echo "Repository $REPO_NUM/$TOTAL_REPOS: $REPO"
    echo "================================================================================"

    # Paths for this repository
    DETERMINISTIC_PATH="$SCRIPT_DIR/$REPO"
    REPO_PATH="$TESTS_ROOT/test_repos/$REPO"

    # Validate paths exist
    if [ ! -d "$DETERMINISTIC_PATH" ]; then
        echo -e "${RED}ERROR: Deterministic path not found: $DETERMINISTIC_PATH${NC}"
        exit 1
    fi

    if [ ! -d "$REPO_PATH" ]; then
        echo -e "${RED}ERROR: Repository path not found: $REPO_PATH${NC}"
        exit 1
    fi

    # Process each agent
    for AGENT in "${AGENTS[@]}"; do
        # Process each mode (NORIG then RIG)
        for MODE in "${MODES[@]}"; do
            echo ""
            echo "--------------------------------------------------------------------------------"
            echo -e "${YELLOW}Agent: $AGENT | Mode: $MODE${NC}"
            echo "--------------------------------------------------------------------------------"

            # Normalize agent name for filename (cursor-agent -> cursor)
            case "$AGENT" in
                cursor-agent)
                    AGENT_NAME="cursor"
                    ;;
                *)
                    AGENT_NAME="$AGENT"
                    ;;
            esac

            # Output file path
            OUTPUT_FILE="$DETERMINISTIC_PATH/${AGENT_NAME}_${MODE}_answers.json"

            # Check if output already exists
            if [ -f "$OUTPUT_FILE" ]; then
                echo -e "${GREEN}✓ Output file already exists: $OUTPUT_FILE${NC}"
                echo "Skipping..."
                continue
            fi

            # Generate prompt
            echo "Generating prompt..."
            PROMPT_OUTPUT=$(python3 "$HELPER" generate_prompt "$DETERMINISTIC_PATH" "$MODE" 2>&1)
            PROMPT_EXIT_CODE=$?

            if [ $PROMPT_EXIT_CODE -ne 0 ]; then
                echo -e "${RED}ERROR: Failed to generate prompt${NC}"
                echo "Repository: $REPO"
                echo "Mode: $MODE"
                echo "Command: python3 $HELPER generate_prompt \"$DETERMINISTIC_PATH\" \"$MODE\""
                echo "Output:"
                echo "$PROMPT_OUTPUT"
                echo ""
                echo "To resume later, this combination will be skipped automatically."
                exit 1
            fi

            PROMPT="$PROMPT_OUTPUT"

            # Copy prompt to clipboard
            if ! echo "$PROMPT" | clip.exe 2>&1; then
                echo -e "${YELLOW}WARNING: Failed to copy to clipboard${NC}"
                echo "You'll need to manually copy the prompt (it will be displayed next)"
                echo ""
                echo "===== PROMPT START ====="
                echo "$PROMPT"
                echo "===== PROMPT END ====="
                echo ""
                read -p "Press Enter once you've copied the prompt..."
            else
                echo -e "${GREEN}✓ Prompt copied to clipboard${NC}"
            fi
            echo ""

            # Change to repository directory
            if ! cd "$REPO_PATH" 2>&1; then
                echo -e "${RED}ERROR: Failed to change directory to $REPO_PATH${NC}"
                echo "Repository: $REPO"
                echo "Please ensure the test repository exists"
                exit 1
            fi
            echo "Working directory: $REPO_PATH"
            echo ""

            # Delete any existing answers.json (prevent stale data)
            if [ -f "answers.json" ]; then
                if ! rm answers.json 2>&1; then
                    echo -e "${RED}ERROR: Failed to delete old answers.json${NC}"
                    echo "Location: $REPO_PATH/answers.json"
                    echo "Please delete it manually or check permissions"
                    exit 1
                fi
                echo "Deleted old answers.json"
            fi

            # Prompt user to launch agent
            echo "================================================================================"
            echo "READY TO LAUNCH: $AGENT"
            echo "================================================================================"
            echo "Repository: $REPO"
            echo "Mode: $MODE"
            echo ""
            echo "1. Press Enter to launch $AGENT"
            echo "2. Paste prompt from clipboard (Ctrl+V or right-click)"
            echo "3. Wait for agent to finish and write answers.json"
            echo "4. Exit the agent"
            echo "================================================================================"
            read -p "Press Enter to continue..."
            echo ""

            # Verify agent command exists
            if ! command -v "$AGENT" &> /dev/null; then
                echo -e "${RED}ERROR: Agent command not found: $AGENT${NC}"
                echo "Please ensure $AGENT is installed and in your PATH"
                echo ""
                echo "To skip this agent and continue with others, you would need to modify the script."
                echo "To resume later, already completed combinations will be skipped automatically."
                exit 1
            fi

            # Launch agent with auto-approval flags (blocks until user exits)
            case "$AGENT" in
                claude)
                    if ! claude --dangerously-skip-permissions; then
                        echo ""
                        echo -e "${RED}ERROR: Agent '$AGENT' exited with error${NC}"
                        echo "Repository: $REPO"
                        echo "Mode: $MODE"
                        echo ""
                        echo "To resume later, this combination will be skipped automatically if it completed."
                        exit 1
                    fi
                    ;;
                codex)
                    if ! codex --dangerously-bypass-approvals-and-sandbox; then
                        echo ""
                        echo -e "${RED}ERROR: Agent '$AGENT' exited with error${NC}"
                        echo "Repository: $REPO"
                        echo "Mode: $MODE"
                        echo ""
                        echo "To resume later, this combination will be skipped automatically if it completed."
                        exit 1
                    fi
                    ;;
                cursor-agent)
                    # No auto-approval flag documented for cursor-agent
                    echo -e "${YELLOW}Note: cursor-agent may require manual approvals during execution${NC}"
                    if ! cursor-agent; then
                        echo ""
                        echo -e "${RED}ERROR: Agent '$AGENT' exited with error${NC}"
                        echo "Repository: $REPO"
                        echo "Mode: $MODE"
                        echo ""
                        echo "To resume later, this combination will be skipped automatically if it completed."
                        exit 1
                    fi
                    ;;
                *)
                    # Fallback for unknown agents
                    if ! $AGENT; then
                        echo ""
                        echo -e "${RED}ERROR: Agent '$AGENT' exited with error${NC}"
                        echo "Repository: $REPO"
                        echo "Mode: $MODE"
                        echo ""
                        echo "To resume later, this combination will be skipped automatically if it completed."
                        exit 1
                    fi
                    ;;
            esac

            echo ""
            echo "================================================================================"
            echo "Agent exited"
            echo "================================================================================"

            # Validate answers.json exists
            if [ ! -f "answers.json" ]; then
                echo -e "${RED}ERROR: answers.json not found!${NC}"
                echo "Expected location: $REPO_PATH/answers.json"
                echo "Repository: $REPO"
                echo "Agent: $AGENT"
                echo "Mode: $MODE"
                echo ""
                echo "The agent may not have completed successfully."
                echo "To resume later, this combination will be retried automatically."
                exit 1
            fi

            echo -e "${GREEN}✓ Found answers.json${NC}"

            # Ask user for timing
            echo ""
            echo "Please provide the execution time:"
            read -p "How many MINUTES? " MINUTES
            read -p "How many SECONDS? " SECONDS

            # Validate numeric input
            if ! [[ "$MINUTES" =~ ^[0-9]+$ ]]; then
                echo -e "${RED}ERROR: Minutes must be a non-negative integer${NC}"
                echo "You entered: '$MINUTES'"
                echo "Please enter only digits (e.g., 0, 5, 42)"
                exit 1
            fi

            if ! [[ "$SECONDS" =~ ^[0-9]+$ ]]; then
                echo -e "${RED}ERROR: Seconds must be a non-negative integer${NC}"
                echo "You entered: '$SECONDS'"
                echo "Please enter only digits (e.g., 0, 30, 59)"
                exit 1
            fi

            # Calculate total seconds
            TOTAL_SECONDS=$((MINUTES * 60 + SECONDS))
            echo "Total time: $TOTAL_SECONDS seconds ($MINUTES minutes, $SECONDS seconds)"

            # Add timing to answers.json
            TIMING_OUTPUT=$(python3 "$HELPER" add_timing "answers.json" "$TOTAL_SECONDS" 2>&1)
            TIMING_EXIT_CODE=$?

            if [ $TIMING_EXIT_CODE -ne 0 ]; then
                echo -e "${RED}ERROR: Failed to add timing to answers.json${NC}"
                echo "Repository: $REPO"
                echo "Agent: $AGENT"
                echo "Mode: $MODE"
                echo "Command: python3 $HELPER add_timing \"answers.json\" \"$TOTAL_SECONDS\""
                echo "Output:"
                echo "$TIMING_OUTPUT"
                echo ""
                echo "To resume later, this combination will be retried automatically."
                exit 1
            fi

            echo -e "${GREEN}✓ Added timing to answers.json${NC}"

            # Move to output location
            if ! mv answers.json "$OUTPUT_FILE" 2>&1; then
                echo -e "${RED}ERROR: Failed to move answers.json to $OUTPUT_FILE${NC}"
                echo "Repository: $REPO"
                echo "Agent: $AGENT"
                echo "Mode: $MODE"
                echo "Source: $REPO_PATH/answers.json"
                echo "Destination: $OUTPUT_FILE"
                echo ""
                echo "Please check file permissions and ensure the destination directory exists."
                exit 1
            fi

            echo -e "${GREEN}✓ Saved: $OUTPUT_FILE${NC}"

            # Return to script directory
            cd "$SCRIPT_DIR"
        done
    done

    echo ""
    echo -e "${GREEN}✓ Completed repository: $REPO${NC}"
    echo ""
done

echo ""
echo "================================================================================"
echo "ALL REPOSITORIES COMPLETED"
echo "================================================================================"
echo "Total repositories processed: ${#REPOS[@]}"
echo ""
echo "Next step: Run analysis"
echo "  cd $SCRIPT_DIR"
echo "  python run_after_ask_agents_to_get_full_report.py"
echo "================================================================================"
