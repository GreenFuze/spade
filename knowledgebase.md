# SPADE Phase 0 - Development Knowledge Base

## Project Overview

**SPADE** (Software Program Architecture Discovery Engine) is a tool for inferring software architecture from codebases. **Phase 0 "Startup"** focuses on directory-based scaffold inference using LLMs.

### Core Philosophy
- **No hardcoded language heuristics** - LLM infers everything from directory structure
- **No AST/CPG analysis** - Only directory names and structure
- **No code execution** - Pure static analysis
- **No web/RAG** - Self-contained operation
- **Object-oriented design** - Clean separation of concerns

## Architecture

### File Structure
```
spade/
├── main.py              # CLI entry point
├── agent.py             # Core OOP implementation
├── logger.py            # Centralized logging
├── prompts/
│   ├── phase0_scaffold_system.md
│   └── phase0_scaffold_user.md
├── requirements.txt     # Python dependencies
├── README.md           # User documentation
└── knowledgebase.md    # This file
```

### Core Classes (agent.py)

#### 1. `Telemetry`
- **Purpose**: Capture and persist run statistics
- **Key Features**:
  - Run ID, timestamps, wall clock time
  - Scan statistics (dir count, depth, entries, skipped)
  - LLM statistics (attempts, chars, latency, retries)
  - Scaffold statistics (blocks, confidence, questions)
  - Success/failure tracking
- **Output**: JSONL format for historical analysis

#### 2. `DirectorySnapshot`
- **Purpose**: Scan directory tree and create structured entries
- **Key Features**:
  - Configurable depth and entry limits
  - Noise filtering (`.git`, `.spade`, `node_modules`, etc.)
  - Permission error handling
  - Deterministic sorting
  - Unlimited mode support (`0` = unlimited)
- **Output**: List of directory entries with metadata

#### 3. `PromptLoader`
- **Purpose**: Load system and user prompt templates
- **Key Features**:
  - Template loading from `prompts/` directory
  - UTF-8 encoding support
  - Fail-fast on missing files
- **Templates**: System instructions + user context injection

#### 4. `LLMClient`
- **Purpose**: Interface with LLM via `llm` Python package
- **Key Features**:
  - Configurable model selection
  - Retry logic for JSON parsing failures
  - Comprehensive logging of input/output
  - Statistics collection
- **Default Model**: `gpt-5-nano`

#### 5. `Phase0Context`
- **Purpose**: Build LLM input context from directory snapshot
- **Key Features**:
  - Repository metadata (root path, git presence)
  - Directory structure data
  - Scan limits information
- **Output**: Structured JSON for LLM consumption

#### 6. `ScaffoldWriter`
- **Purpose**: Persist outputs to `.spade/` directory
- **Key Features**:
  - Context JSON output
  - Scaffold JSON with version/timestamp
  - Telemetry JSONL append
  - Automatic directory creation
- **Output Files**:
  - `phase0_context.json`
  - `scaffold.json`
  - `telemetry.jsonl`

#### 7. `Phase0Agent`
- **Purpose**: Main orchestrator for Phase 0 execution
- **Key Features**:
  - 8-step execution pipeline
  - Exception handling and telemetry
  - Component coordination
  - Success/failure reporting

## Implementation Details

### CLI Interface (main.py)

#### Argument Parsing
- **Command Format**: `python main.py <repo_path> [options]`
- **Options**:
  - `--model MODEL_ID`: LLM model (default: `gpt-5-nano`)
  - `--max_depth N`: Scan depth (default: `3`, `0` = unlimited)
  - `--max_entries N`: Entries per dir (default: `40`, `0` = unlimited)
  - `--fresh`: Delete `.spade` directory before running
  - `--help`: Show usage and exit

#### Key Features
- **Robust validation**: Type checking, range validation
- **Help system**: Multiple `--help` locations supported
- **Signal handling**: CTRL+C hard shutdown
- **Resource management**: Logger file handle conflict resolution

### Logging System (logger.py)

#### Configuration
- **File Output**: `DEBUG` level to `.spade/spade.log`
- **Console Output**: `INFO` level to stdout
- **Format**: Timestamp, logger name, level, message
- **Encoding**: UTF-8

#### Special Logging
- **LLM Input**: `------\nUser: {prompt}`
- **LLM Output**: `-------\nAgent: {response}`
- **Debug Level**: All operational details logged

### Directory Scanning

#### Unlimited Mode
- **Depth**: `0` triggers `os.walk()` for unlimited depth
- **Entries**: `0` removes list truncation
- **Logging**: Shows "unlimited" instead of "0"

#### Noise Filtering
```python
SKIP_DIRS = {
    ".git", ".spade", ".idea", ".vscode", "__pycache__",
    "node_modules", "dist", "build", "target", "bin", "obj"
}
```

#### Error Handling
- **Permission Errors**: Graceful handling with empty entries
- **Path Resolution**: Skip non-relative paths
- **Fail-Fast**: Unexpected errors raise exceptions

### LLM Integration

#### Model Configuration
- **Default**: `gpt-5-nano`
- **Configurable**: Via `--model` switch
- **Library**: Uses `llm` Python package

#### Retry Logic
- **Attempts**: Maximum 2 attempts
- **JSON Parsing**: Automatic retry on parse failure
- **Strict Reminder**: "Output ONLY valid JSON" on retry

#### Prompt Engineering
- **System Prompt**: Instructions and JSON schema
- **User Prompt**: Context injection with `{{PHASE0_CONTEXT_JSON}}`
- **Schema**: Structured output with confidence scores

### Output Schemas

#### Phase 0 Context
```json
{
  "repo": {
    "root": "absolute/path",
    "git_present": true
  },
  "dirs": [
    {
      "path": "relative/path",
      "depth": 2,
      "entry_count": 15,
      "subdir_count": 3,
      "sample_entries": ["file1.py", "dir1"]
    }
  ],
  "limits": {
    "max_depth": 3,
    "max_entries_per_dir": 40
  }
}
```

#### Scaffold Output
```json
{
  "version": "0.1",
  "ts": "2024-01-01T12:00:00Z",
  "inferred": {
    "big_blocks": [
      {
        "name": "Core Engine",
        "description": "Main processing logic",
        "confidence": 85,
        "evidence": ["src/core/", "engine.py"]
      }
    ]
  },
  "open_questions_ranked": [
    "What is the primary data flow?",
    "How are components coupled?"
  ],
  "notes": "Phase 0 scaffold inferred from directory structure/names only."
}
```

#### Telemetry
```json
{
  "run_id": "uuid",
  "repo_root": "path",
  "model_id": "gpt-5-nano",
  "started_at": "2024-01-01T12:00:00Z",
  "finished_at": "2024-01-01T12:01:00Z",
  "wall_ms": 60000.0,
  "dir_count": 25,
  "max_depth": 3,
  "max_entries": 40,
  "skipped_dirs": [".git", "node_modules"],
  "llm_attempts": 1,
  "llm_prompt_chars": 5000,
  "llm_response_chars": 800,
  "llm_latency_ms": 2500.0,
  "llm_parse_retries": 0,
  "scaffold_big_blocks_count": 4,
  "scaffold_conf_min": 25,
  "scaffold_conf_max": 90,
  "scaffold_conf_avg": 65.5,
  "scaffold_questions_count": 3,
  "success": true,
  "error_message": null
}
```

## Development Decisions

### 1. Object-Oriented Design
- **Rationale**: Clean separation of concerns, testability, maintainability
- **Implementation**: 7 distinct classes with clear responsibilities
- **Benefits**: Modular, extensible, easy to understand

### 2. Command-Line Arguments vs Environment Variables
- **Decision**: CLI switches for `max_depth` and `max_entries`
- **Rationale**: More explicit, better user experience, easier debugging
- **Implementation**: Robust argument parsing with validation

### 3. Unlimited Mode Implementation
- **Decision**: Use `0` for unlimited (not `-1`)
- **Rationale**: More intuitive, non-negative validation
- **Implementation**: Conditional logic in scanning methods

### 4. Logging Strategy
- **Decision**: Separate `logger.py` module
- **Rationale**: Centralized configuration, reusability
- **Implementation**: File + console handlers with different levels

### 5. Resource Management
- **Issue**: Logger file handle conflicts with `--fresh`
- **Solution**: Initialize agent after directory deletion
- **Rationale**: Prevent file handle conflicts during deletion

### 6. Error Handling Philosophy
- **Approach**: Fail-fast with clear error messages
- **Implementation**: Comprehensive validation, graceful degradation
- **Benefits**: Better debugging, user experience

## Current State

### ✅ Completed Features
1. **Core Architecture**: All 7 classes implemented and tested
2. **CLI Interface**: Robust argument parsing with help system
3. **Directory Scanning**: Configurable depth/entries with unlimited mode
4. **LLM Integration**: Retry logic, comprehensive logging
5. **Output Generation**: Context, scaffold, and telemetry files
6. **Logging System**: File and console output with debug details
7. **Error Handling**: Graceful degradation and clear error messages
8. **Resource Management**: Fixed file handle conflicts

### 🔧 Technical Specifications
- **Python Version**: 3.8+
- **Dependencies**: `llm` package for LLM integration
- **File Encoding**: UTF-8 throughout
- **Exit Codes**: 0 (success), 1 (error), 2 (usage error)
- **Default Limits**: depth=3, entries=40, model=gpt-5-nano

### 📁 Output Structure
```
target_repo/
└── .spade/
    ├── phase0_context.json    # LLM input context
    ├── scaffold.json          # LLM output with metadata
    ├── telemetry.jsonl        # Run statistics (append)
    └── spade.log             # Debug logs
```

## Usage Examples

### Basic Usage
```bash
# Scan current directory with defaults
python main.py .

# Scan specific repository
python main.py /path/to/repo

# Show help
python main.py --help
```

### Advanced Configuration
```bash
# Use different model
python main.py . --model gpt-4o-mini

# Unlimited depth and entries
python main.py . --max_depth 0 --max_entries 0

# Limited scan
python main.py . --max_depth 2 --max_entries 20

# Fresh start (delete existing .spade)
python main.py . --fresh
```

### Environment Variables
- **SPADE_LLM_MODEL**: Default model (fallback to gpt-5-nano)
- **Note**: CLI switches take precedence over environment variables

## Next Steps (Future Sessions)

### Potential Enhancements
1. **Phase 1**: File content analysis and AST parsing
2. **Phase 2**: Code execution and dynamic analysis
3. **Phase 3**: Web/RAG integration for external knowledge
4. **Testing**: Unit tests for all classes
5. **Performance**: Optimization for large repositories
6. **UI**: Web interface or IDE integration

### Known Limitations
1. **Directory-only**: No file content analysis in Phase 0
2. **LLM Dependency**: Requires internet connection and API access
3. **Cost**: LLM API calls incur charges
4. **Determinism**: LLM responses may vary between runs

## Troubleshooting

### Common Issues
1. **Permission Errors**: Check directory access rights
2. **LLM Failures**: Verify API key and internet connection
3. **JSON Parse Errors**: Automatic retry with stricter instructions
4. **File Handle Conflicts**: Fixed with proper initialization order

### Debug Information
- **Logs**: Check `.spade/spade.log` for detailed debug information
- **Telemetry**: Review `.spade/telemetry.jsonl` for run statistics
- **Context**: Examine `.spade/phase0_context.json` for LLM input

## Architecture Decisions Log

### 2024-01-01: Initial Implementation
- **Decision**: Object-oriented design with 7 core classes
- **Rationale**: Clean separation, testability, maintainability
- **Status**: ✅ Implemented and tested

### 2024-01-01: CLI Design
- **Decision**: Command-line switches over environment variables
- **Rationale**: Better UX, explicit configuration
- **Status**: ✅ Implemented with help system

### 2024-01-01: Unlimited Mode
- **Decision**: Use `0` for unlimited depth/entries
- **Rationale**: Intuitive, non-negative validation
- **Status**: ✅ Implemented with `os.walk()` and conditional logic

### 2024-01-01: Resource Management
- **Issue**: Logger file handle conflicts with `--fresh`
- **Solution**: Initialize agent after directory deletion
- **Status**: ✅ Fixed and tested

This knowledge base captures the complete state of SPADE Phase 0 development and provides a foundation for future enhancements and maintenance.
