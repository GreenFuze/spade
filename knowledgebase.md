# SPADE Phase 0 - Development Knowledge Base

## Project Overview

**SPADE** (Software Program Architecture Discovery Engine) is a tool for inferring software architecture from codebases. **Phase 0 "Directory-based Scaffold Inference"** focuses on using LLMs to infer architectural big blocks from repository directory structures.

### Core Philosophy
- **No hardcoded language heuristics** - LLM infers everything from directory structure
- **No AST/CPG analysis** - Only directory names and structure  
- **No code execution** - Pure static analysis
- **No web/RAG** - Self-contained operation
- **Object-oriented design** - Clean separation of concerns
- **Strict data validation** - Pydantic v2 for all schemas
- **Centralized configuration** - Single source of truth for all settings

## Architecture

### File Structure
```
spade/
├── main.py              # CLI entry point with subcommands
├── cli/                 # CLI command implementations
├── models.py            # Pydantic v2 schemas (RunConfig, DirMeta, etc.)
├── workspace.py         # Workspace management and configuration
├── snapshot.py          # Directory snapshot and metadata generation
├── ignore.py            # Skip logic using .spadeignore/.spadeallow
├── markers.py           # Marker detection and rules
├── languages.py         # Language mapping and aggregation
├── scoring.py           # Deterministic scoring for children
├── context.py           # Phase-0 context builder
├── scaffold.py          # Scaffold store and merge semantics
├── prompts.py           # Prompt loading and management
├── llm.py               # LLM client with JSON repair
├── nav.py               # Navigation guardrails and fallback
├── phase0.py            # Phase-0 traversal loop and analysis
├── learning.py          # Post-snapshot learning passes
├── sanitize.py          # LLM output sanitization and guardrails
├── worklist.py          # Worklist management and persistence
├── report.py            # Report generation (JSON and Markdown)
├── agent.py             # Legacy agent implementation
├── logger.py            # Centralized logging singleton
├── prompts/             # Prompt templates
├── tests/               # Comprehensive test suite (83 tests)
│   ├── conftest.py      # Test fixtures and helpers
│   ├── test_*.py        # Unit and integration tests
├── fakeapp/             # Test application for integration tests
├── requirements.txt     # Python dependencies
├── research_log.md      # Development process documentation
└── knowledgebase.md     # This file
```

### Core Components

#### 1. **Configuration System** (`models.py`, `workspace.py`)
- **RunConfig**: Centralized configuration with Pydantic validation
- **Caps**: Configurable limits for samples, navigation, context, sanitizer
- **Policies**: Runtime policies for learning, telemetry, timestamps
- **Workspace**: Configuration loading and management

#### 2. **Data Models** (`models.py`)
- **DirMeta**: Directory metadata with counts, extensions, scoring
- **ChildScore**: Deterministic scoring for directory children
- **LLMResponse**: Structured LLM output with components and questions
- **WorklistItem**: Traversal worklist items with state tracking

#### 3. **Snapshot System** (`snapshot.py`)
- **Directory scanning**: DFS traversal with depth limits
- **Metadata generation**: File counts, extension histograms, timestamps
- **Deterministic scoring**: Evidence-based scoring for children
- **Extension rules**: Multi-dot extensions, hidden files, no-extension files

#### 4. **Ignore Engine** (`ignore.py`)
- **Pattern matching**: `pathspec` library with `gitwildmatch` patterns
- **Allow overrides**: `.spadeallow` can override `.spadeignore`
- **Symlink policy**: Configurable symlink handling
- **Complex patterns**: Support for complex ignore/allow rules

#### 5. **Navigation System** (`nav.py`)
- **Guardrails**: Depth limits, safe names, ignore patterns
- **Max children caps**: Configurable limits per navigation step
- **Deterministic fallback**: Safe navigation when LLM fails
- **Path validation**: Ensure updates only apply to current/ancestors

#### 6. **Context Building** (`context.py`)
- **Token-safe caps**: Configurable limits for context elements
- **Ancestor information**: Build ancestor chain from scaffold data
- **Context metadata**: Inform LLM about truncation
- **Phase-0 context**: Exact schema for LLM consumption

#### 7. **LLM Integration** (`llm.py`)
- **JSON repair**: One-shot repair for malformed JSON
- **Strict validation**: Pydantic validation of LLM responses
- **Retry logic**: Automatic retry on parse failures
- **Transport abstraction**: Support for different LLM backends

#### 8. **Sanitization** (`sanitize.py`)
- **Output sanitization**: Post-process LLM responses
- **Language canonicalization**: Map language names to canonical forms
- **Confidence punishment**: Reduce confidence for insufficient evidence
- **Configurable caps**: Limits on summaries, languages, tags, evidence

#### 9. **Learning System** (`learning.py`)
- **Marker learning**: Learn new markers from repository structure
- **Language learning**: Learn new language mappings
- **Post-snapshot passes**: Re-run learning after snapshot completion
- **Re-scoring**: Update scores based on learned information

#### 10. **Phase-0 Engine** (`phase0.py`)
- **DFS traversal**: Depth-first search with worklist management
- **Analysis persistence**: Save analysis results to scaffold
- **Telemetry collection**: Comprehensive run statistics
- **Resume capability**: Continue from worklist state

## Implementation Details

### CLI Interface (`main.py`, `cli/`)

#### Command Structure
```bash
python main.py <command> [options]
```

#### Commands
- **`--init-workspace`**: Initialize .spade workspace directory
- **`--clean`**: Clean .spade workspace directory
- **`phase0 [options]`**: Run Phase-0 analysis
- **`phase0 inspect <relpath>`**: Preview Phase-0 context for debugging

#### Key Features
- **Subcommand architecture**: Clean separation of functionality
- **Configuration-driven**: All settings via `run.json`
- **Error handling**: Comprehensive error reporting and logging
- **Telemetry**: Automatic collection of run statistics
- **Safety features**: Lock management and graceful shutdown
- **Debug tools**: Context inspection and preview generation

### Configuration System

#### RunConfig Schema
```python
class RunConfig(BaseModel):
    caps: Caps                    # Configurable limits
    policies: Policies           # Runtime policies
    llm: LLMConfig              # LLM settings
    telemetry: TelemetryConfig  # Telemetry settings
```

#### Caps Configuration
```python
class Caps(BaseModel):
    samples: Samples            # Sample limits (max_dirs, max_files)
    nav: Nav                   # Navigation limits (max_children_per_step)
    context: Context           # Context limits (max_siblings, etc.)
    sanitizer: Sanitizer       # Sanitizer limits (max_summary_chars, etc.)
```

### Data Validation

#### Pydantic v2 Integration
- **Strict validation**: All data structures validated at runtime
- **Type safety**: Comprehensive type hints throughout
- **Error messages**: Clear validation error messages
- **Serialization**: Automatic JSON serialization/deserialization

#### Schema Examples
```python
class DirMeta(BaseModel):
    path: str
    counts: DirCounts
    ext_histogram: Optional[Dict[str, int]]
    deterministic_scoring: Optional[Dict[str, ChildScore]]
    timestamp: str

class ChildScore(BaseModel):
    score: float
    reasons: List[str]
    evidence: List[str]
```

### Testing Framework

#### Test Organization
- **83 total tests**: Comprehensive coverage of all components
- **Unit tests**: Isolated component testing with fixtures
- **Integration tests**: End-to-end testing with fakeapp
- **Pytest framework**: Modern Python testing with fixtures

#### Test Categories
- **Core mechanics**: Ignore engine, navigation, snapshot, scoring
- **Context building**: Token-safe caps and context generation
- **Sanitization**: Output processing and normalization
- **Integration**: Full Phase-0 workflow testing

#### Test Structure
```
tests/
├── conftest.py              # Shared fixtures and helpers
├── test_ignore.py           # Ignore engine tests (8 tests)
├── test_nav.py              # Navigation tests (5 tests)
├── test_snapshot_exts.py    # Snapshot extension tests (4 tests)
├── test_scoring.py          # Scoring tests (3 tests)
├── test_sanitize.py         # Sanitization tests (4 tests)
├── test_context_caps.py     # Context caps tests (4 tests)
├── test_*.py                # Integration and acceptance tests
```

## Current State

### ✅ Completed Features (Tasks 1-23)

#### Core Infrastructure
1. **Configuration System**: Centralized `run.json` with Pydantic validation
2. **Data Models**: Comprehensive Pydantic schemas for all data structures
3. **Workspace Management**: Configuration loading and validation
4. **Logging System**: Singleton logger with file and console output

#### Phase-0 Core
5. **Snapshot System**: Directory scanning with metadata generation
6. **Ignore Engine**: Pattern-based skip logic with allow overrides
7. **Marker Detection**: Configurable marker rules and detection
8. **Language Mapping**: Seed and learned language mappings
9. **Deterministic Scoring**: Evidence-based child scoring
10. **Context Building**: Token-safe LLM context generation
11. **Scaffold Store**: Persistent understanding with merge semantics
12. **Prompt Management**: Template loading and context injection
13. **LLM Client**: JSON repair and strict validation
14. **Navigation Guardrails**: Safe navigation with fallbacks
15. **Phase-0 Traversal**: DFS with worklist management
16. **Learning Passes**: Post-snapshot marker and language learning
17. **Output Sanitization**: LLM response processing and validation
18. **Worklist Management**: Traversal state persistence
19. **Report Generation**: JSON and Markdown report output
20. **CLI Interface**: Subcommand architecture with configuration
21. **Token Safety**: Configurable context caps and limits
22. **Sanitizer Hardening**: Configurable output processing
23. **Unit Testing**: Comprehensive test suite (83 tests)

### 🔧 Technical Specifications
- **Python Version**: 3.8+
- **Dependencies**: `pydantic`, `pathspec`, `pytest`
- **File Encoding**: UTF-8 throughout
- **Configuration**: JSON-based with Pydantic validation
- **Testing**: Pytest with fixtures and temporary directories

### 📁 Output Structure
```
target_repo/
└── .spade/
    ├── run.json              # Configuration file
    ├── snapshot/             # Directory snapshots
    │   ├── dirmeta.json      # Root directory metadata
    │   └── <rel>/dirmeta.json # Subdirectory metadata
    ├── scaffold/             # Scaffold data
    │   └── repository_scaffold.json
    ├── analysis/             # Analysis results
    ├── reports/              # Generated reports
    ├── worklist.json         # Traversal worklist
    ├── summary.json          # Run summary
    └── spade.log            # Debug logs
```

## Usage Examples

### Basic Usage
```bash
# Analyze repository with default configuration
python main.py analyze .

# Refresh analysis (reset worklist)
python main.py refresh .

# Generate reports from existing analysis
python main.py report .

# Run smoke test
python main.py smoke .
```

### Configuration
```json
{
  "caps": {
    "samples": {"max_dirs": 8, "max_files": 8},
    "nav": {"max_children_per_step": 4},
    "context": {"max_siblings": 10, "max_child_scores": 5},
    "sanitizer": {"max_summary_chars": 200, "max_languages": 5}
  },
  "policies": {
    "learned_markers": true,
    "learned_languages": true,
    "timestamps_utc": true
  }
}
```

## Development Decisions

### 1. Pydantic v2 Integration
- **Rationale**: Strict data validation, type safety, serialization
- **Implementation**: All data structures use Pydantic models
- **Benefits**: Runtime validation, clear error messages, JSON compatibility

### 2. Configuration-Driven Design
- **Rationale**: Single source of truth, runtime flexibility
- **Implementation**: Centralized `run.json` with Pydantic validation
- **Benefits**: Easy configuration changes, validation, documentation

### 3. Token-Safe Context Building
- **Rationale**: Prevent oversized LLM prompts
- **Implementation**: Configurable caps on context elements
- **Benefits**: Predictable prompt sizes, cost control

### 4. Comprehensive Testing
- **Rationale**: Ensure reliability and maintainability
- **Implementation**: 83 tests covering all components
- **Benefits**: Regression prevention, documentation, confidence

### 5. Modular Architecture
- **Rationale**: Clean separation of concerns, testability
- **Implementation**: Separate modules for each major function
- **Benefits**: Maintainability, extensibility, reusability

## Next Steps

### Potential Enhancements
1. **Phase 1**: File content analysis and AST parsing
2. **Phase 2**: Code execution and dynamic analysis
3. **Phase 3**: Web/RAG integration for external knowledge
4. **Performance**: Optimization for large repositories
5. **UI**: Web interface or IDE integration
6. **CI/CD**: Automated testing and deployment

### Known Limitations
1. **Directory-only**: No file content analysis in Phase 0
2. **LLM Dependency**: Requires internet connection and API access
3. **Cost**: LLM API calls incur charges
4. **Determinism**: LLM responses may vary between runs

## Troubleshooting

### Common Issues
1. **Configuration Errors**: Check `run.json` syntax and Pydantic validation
2. **Permission Errors**: Verify directory access rights
3. **LLM Failures**: Check API key and internet connection
4. **Test Failures**: Run `python -m pytest tests/ -v` from parent directory

### Debug Information
- **Logs**: Check `.spade/spade.log` for detailed debug information
- **Configuration**: Review `run.json` for settings
- **Test Output**: Run tests with `-v` flag for verbose output

This knowledge base captures the complete state of SPADE Phase 0 development and provides a foundation for future enhancements and maintenance.
