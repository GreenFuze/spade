# Manual Codex Testing Guide for MetaFFI RIG Debugging

## Problem Summary

Codex times out (>1200 seconds) when provided with the MetaFFI RIG, while Claude and Cursor complete successfully:

| Agent | NO-RIG Time | With RIG | Result |
|-------|-------------|----------|--------|
| Cursor | 78s | 34s | ✅ Success |
| Claude | 357s | 277s | ✅ Success |
| Codex | 434s | **TIMEOUT** | ❌ Failed |

The RIG size is **58.3 KB**, creating a **61.8 KB total prompt** with 30 evaluation questions.

## Files Prepared

- `theprompt.txt` - The complete prompt with MetaFFI RIG (61,833 characters)
- `run_codex_manual.sh` - Bash script to run Codex manually
- This README - Testing instructions

## Prerequisites

1. **Codex installed** and available in PATH (`codex` command works in WSL)
2. **MetaFFI repository** copied to workspace
3. **Workspace directory trusted** by Codex (may require one-time approval)

## Step-by-Step Testing Instructions

### Step 1: Prepare the Workspace

```bash
# In WSL
cd /mnt/c/src/github.com/GreenFuze/spade/tests/deterministic/wsl_runners/_codex_workspace

# Copy the MetaFFI test repository
cp -r /mnt/c/src/github.com/GreenFuze/spade/tests/test_repos/cmake/metaffi .

# Verify the copy
ls -la metaffi/
```

Expected structure:
```
_codex_workspace/
└── metaffi/
    ├── CMakeLists.txt
    ├── metaffi-core/
    ├── lang-plugin-python311/
    ├── lang-plugin-openjdk/
    ├── lang-plugin-go/
    └── ... (other files)
```

### Step 2: Review the Prompt (Optional but Recommended)

```bash
# Check prompt size
wc -c /mnt/c/src/github.com/GreenFuze/spade/tests/deterministic/wsl_runners/_cursor_workspace/theprompt.txt

# Preview the prompt structure
head -100 /mnt/c/src/github.com/GreenFuze/spade/tests/deterministic/wsl_runners/_cursor_workspace/theprompt.txt

# See where the RIG JSON starts
grep -n "\"repo\":" /mnt/c/src/github.com/GreenFuze/spade/tests/deterministic/wsl_runners/_cursor_workspace/theprompt.txt | head -1

# See where questions start
grep -n "^1\." /mnt/c/src/github.com/GreenFuze/spade/tests/deterministic/wsl_runners/_cursor_workspace/theprompt.txt
```

### Step 3: Run Codex Manually

#### Option A: Using the Provided Script (Easiest)

```bash
cd /mnt/c/src/github.com/GreenFuze/spade/tests/deterministic/wsl_runners/_cursor_workspace

# Make script executable
chmod +x run_codex_manual.sh

# Run it
./run_codex_manual.sh
```

The script will:
- Verify all prerequisites
- Display prompt statistics
- Run Codex with timing
- Check for output

#### Option B: Direct Command Line

```bash
cd /mnt/c/src/github.com/GreenFuze/spade/tests/deterministic/wsl_runners/_codex_workspace/metaffi

# Run Codex with the prompt
time codex exec "$(cat /mnt/c/src/github.com/GreenFuze/spade/tests/deterministic/wsl_runners/_cursor_workspace/theprompt.txt)"
```

### Step 4: Monitor Progress

In a **separate terminal**, watch for the answers file:

```bash
# Watch for file creation
watch -n 1 'ls -lh /mnt/c/src/github.com/GreenFuze/spade/tests/deterministic/wsl_runners/_codex_workspace/metaffi/answers.json 2>/dev/null || echo "Not created yet..."'

# Or use a loop
while true; do
    clear
    date
    echo "Waiting for answers.json..."
    if [ -f /mnt/c/src/github.com/GreenFuze/spade/tests/deterministic/wsl_runners/_codex_workspace/metaffi/answers.json ]; then
        echo "FILE CREATED!"
        wc -l /mnt/c/src/github.com/GreenFuze/spade/tests/deterministic/wsl_runners/_codex_workspace/metaffi/answers.json
        break
    fi
    sleep 2
done
```

### Step 5: Analyze Results

Once Codex completes (or you stop it), check the output:

```bash
cd /mnt/c/src/github.com/GreenFuze/spade/tests/deterministic/wsl_runners/_codex_workspace/metaffi

# Check if answers.json exists
if [ -f answers.json ]; then
    echo "SUCCESS: File created"

    # Validate JSON
    python3 -c "import json; json.load(open('answers.json'))" && echo "Valid JSON" || echo "Invalid JSON"

    # Count answers
    python3 -c "import json; print(f'Answers provided: {len(json.load(open(\"answers.json\")))} / 30')"

    # Preview answers
    head -50 answers.json
else
    echo "FAILED: No answers.json file created"
fi
```

## What to Look For

### Signs of Success:
- ✅ `answers.json` file appears
- ✅ File contains valid JSON array
- ✅ Has 30 answer objects with "id" and "answer" fields
- ✅ Codex outputs "READY!" signal

### Signs of Timeout/Hang:
- ❌ No output for extended period (>5 minutes of silence)
- ❌ No `answers.json` file after 20+ minutes
- ❌ Codex process becomes unresponsive

### Things to Monitor:
- **Time to first response**: How long before Codex starts writing?
- **Partial answers**: Does it write some answers then stop?
- **Memory/CPU usage**: Is Codex consuming excessive resources?
- **Error messages**: Any stderr output from Codex?

## Debugging Tips

### If Codex Hangs Immediately:
1. **Check prompt validity**: Ensure `theprompt.txt` is well-formed
2. **Test with smaller prompt**: Try removing the RIG section
3. **Verify Codex works**: Test with a simple "Hello World" prompt

### If Codex Produces Partial Results:
1. **Check which questions answered**: Identify where it stopped
2. **Look for error patterns**: Is it a specific question type?
3. **Check disk space**: Ensure there's space to write

### If You Want to Test Variations:

```bash
# Test WITHOUT RIG (generate new prompt without RIG section)
python3 -c "
import json
with open('tests/deterministic/cmake/metaffi/evaluation_questions.json') as f:
    questions = json.load(f)['questions']

prompt = '''You are an expert at analyzing code repositories and build systems.

Please answer the following questions about this repository.

IMPORTANT: Write your answers to a file named \"answers.json\" in the root of this repository.

The answers.json file must be a JSON array with this exact format:
[{\"id\": 1, \"answer\": \"your answer here\"}]

For answers that are lists, use JSON arrays. For yes/no questions, answer with \"yes\" or \"no\".

Questions:

'''
for q in questions:
    prompt += f\"{q['id']}. {q['question']}\\n\"
prompt += \"\\n\\nRemember: Write your answers to answers.json in the repository root!\\nREADY!\"

with open('tests/deterministic/wsl_runners/_cursor_workspace/theprompt_NORIG.txt', 'w') as f:
    f.write(prompt)
print(f'NO-RIG prompt size: {len(prompt)} chars')
"

# Then test with NO-RIG prompt
cd /mnt/c/src/github.com/GreenFuze/spade/tests/deterministic/wsl_runners/_codex_workspace/metaffi
time codex exec "$(cat /mnt/c/src/github.com/GreenFuze/spade/tests/deterministic/wsl_runners/_cursor_workspace/theprompt_NORIG.txt)"
```

## Expected Completion Times

Based on historical data:

- **Small repos (cmake_hello_world)**: ~90 seconds with RIG
- **Medium repos (jni_hello_world)**: ~115 seconds with RIG
- **Large repos (metaffi)**: Unknown (times out at 1200s)

**Without RIG**: MetaFFI takes ~435 seconds

## Validation

To validate the answers after completion:

```python
import json
import sys

# Load answers
with open('/mnt/c/src/github.com/GreenFuze/spade/tests/deterministic/wsl_runners/_codex_workspace/metaffi/answers.json') as f:
    answers = json.load(f)

# Check format
assert isinstance(answers, list), "Answers must be a list"
print(f"✓ Valid list with {len(answers)} items")

# Check each answer
expected_ids = set(range(1, 31))  # Questions 1-30
found_ids = set()

for ans in answers:
    assert 'id' in ans, f"Missing 'id' in answer: {ans}"
    assert 'answer' in ans, f"Missing 'answer' in answer: {ans}"
    found_ids.add(ans['id'])

missing = expected_ids - found_ids
if missing:
    print(f"✗ Missing answers for questions: {sorted(missing)}")
else:
    print("✓ All 30 questions answered!")
```

## Next Steps Based on Results

### If Codex Completes Successfully:
- Compare timing to Claude/Cursor
- Validate answer accuracy
- Investigate what changed vs previous timeout

### If Codex Times Out Again:
- Note exactly when it stops responding
- Check if ANY partial output was created
- Consider RIG size optimization strategies
- Compare prompt structure to Claude/Cursor

### If Codex Completes but Slowly (>10 minutes):
- This confirms it's a performance issue, not a bug
- RIG size is the likely culprit
- Consider filtered/compressed RIG variants

## Contact

If you discover insights from manual testing, document findings in this directory or update the project documentation.
