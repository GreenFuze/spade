# SPADE

Software Program Architecture Discovery Engine

## Phase 0: Directory-based Scaffold Inference

SPADE Phase 0 analyzes repository directory structures to infer architectural big blocks using LLM reasoning.

## Quickstart

1. **Install dependencies:**
   ```bash
   pip install llm
   ```

2. **Configure LLM provider:**
   Follow the [llm documentation](https://github.com/simonw/llm) to configure your provider keys.

4. **Run SPADE:**
   ```bash
   # Basic usage (uses default model: gpt-5-nano)
   python main.py /path/to/repo
   
   # Specify a different model
   python main.py /path/to/repo --model gpt-4o-mini
   
   # Use --fresh to delete previous results
   python main.py /path/to/repo --fresh
   
   # Customize scan depth and entries
   python main.py /path/to/repo --max_depth 5 --max_entries 100
   
   # Unlimited scan (0 = unlimited)
   python main.py /path/to/repo --max_depth 0 --max_entries 0
   
   # Combine all options
   python main.py /path/to/repo --model gpt-4o-mini --max_depth 5 --max_entries 100 --fresh
   
   # Use environment variable for repo path
   python main.py "$ENV:METAFFI_HOME"
   ```

## Project Structure

```
spade/
├── main.py              # CLI entry point
├── agent.py             # Core OOP implementation
├── logger.py            # Centralized logging configuration
├── requirements.txt     # Dependencies
├── README.md           # Documentation
└── prompts/            # LLM prompt templates
    ├── phase0_scaffold_system.md
    └── phase0_scaffold_user.md
```

## Output

SPADE creates the following files in the target repository:

### Results Directory: `.spade/`
- `phase0_context.json` - Directory structure evidence
- `scaffold.json` - LLM-inferred architectural blocks  
- `telemetry.jsonl` - Run statistics and metrics

### Log File: `.spade/spade.log`
- Comprehensive debug and info logs
- Default logging level: DEBUG
- Console output: INFO level
- File output: DEBUG level (includes all details)
- Located inside `.spade/` directory

## Phase 0 Scope

- **Input:** Directory structure and names only
- **Output:** Inferred big blocks with confidence scores
- **No:** AST analysis, code execution, language-specific heuristics
- **Telemetry:** Comprehensive metrics from day one

Later phases will extend this foundation with deeper code analysis.
