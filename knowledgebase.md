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
- **Workspace-centric architecture** - All filesystem operations through Workspace object

## Architecture

### File Structure
```
spade/
├── main.py              # CLI entry point with Click-based subcommands
├── schemas.py           # Pydantic v2 schemas (RunConfig, SpadeStateEntry, etc.)
├── workspace.py         # Workspace management and configuration
├── spade_state.py       # Unified state management with SQLite backend
├── ignore.py            # Skip logic using .spadeignore/.spadeallow
├── markers.py           # Marker detection and rules
├── languages.py         # Language mapping and aggregation
├── context.py           # Phase-0 context builder
├── scaffold.py          # Scaffold store and merge semantics
├── prompts.py           # Prompt loading and management
├── agent.py             # Abstract agent base class
├── phase0_agent.py      # Phase-0 agent implementation
├── sanitize.py          # LLM output sanitization and guardrails
├── report.py            # Report generation (JSON and Markdown)
├── telemetry.py         # Telemetry collection and persistence
├── logger.py            # Centralized logging singleton
├── default_run_phase0.yaml # Default configuration template
├── default.spadeignore  # Default ignore patterns
├── prompts/             # Prompt templates
├── tests/               # Comprehensive test suite
│   ├── conftest.py      # Test fixtures and helpers
│   ├── test_*.py        # Unit and integration tests
├── fakeapp/             # Test application for integration tests
├── requirements.txt     # Python dependencies
├── research_log.md      # Development process documentation
└── knowledgebase.md     # This file

# Note: learning.py, nav.py, scoring.py are temporarily commented out (LLM disabled)
```

### Core Components

#### 1. **Configuration System** (`schemas.py`, `workspace.py`)
- **RunConfig**: Centralized configuration with Pydantic validation
- **Caps**: Configurable limits for samples, navigation, context, sanitizer
- **Policies**: Runtime policies for learning, telemetry, timestamps
- **Workspace**: Single point of interaction for all filesystem operations

#### 2. **Data Models** (`schemas.py`)
- **SpadeStateEntryFile**: File entries with metadata, size, extension, confidence
- **SpadeStateEntryDir**: Directory entries with children, counts, markers, scoring
- **SpadeStateMetadata**: Database metadata with repo root, timestamps, version
- **ChildScore**: Deterministic scoring for directory children
- **LLMResponse**: Structured LLM output with components and questions

#### 3. **Unified State Management** (`spade_state.py`)
- **SQLite backend**: ACID-compliant database for all state data
- **Unified storage**: Files and directories in single table with type differentiation
- **Upfront tree building**: Complete filesystem scan before traversal
- **Metadata collection**: File counts, extensions, timestamps, markers, scoring
- **Type-safe access**: Separate Pydantic models for files (`SpadeStateEntryFile`) and directories (`SpadeStateEntryDir`)
- **Traversal methods**: `get_parent()`, `get_sub_directories()`, `get_files()` with visited filtering
- **File content access**: `get_file_content()` reads from filesystem on demand
- **Statistics on-demand**: Real-time SQL queries for comprehensive statistics
- **Confidence tracking**: 0-100 confidence scores for all entries

#### 4. **Ignore Engine** (`ignore.py`)
- **Pattern matching**: `pathspec` library with `gitwildmatch` patterns
- **Allow overrides**: `.spadeallow` can override `.spadeignore`
- **Symlink policy**: Configurable symlink handling
- **Complex patterns**: Support for complex ignore/allow rules

#### 5. **Navigation System** (`nav.py`) - Temporarily Disabled
- **Guardrails**: Depth limits, safe names, ignore patterns
- **Max children caps**: Configurable limits per navigation step
- **Deterministic fallback**: Safe navigation when LLM fails
- **Path validation**: Ensure updates only apply to current/ancestors

#### 6. **Context Building** (`context.py`) - Temporarily Disabled
- **Token-safe caps**: Configurable limits for context elements
- **Ancestor information**: Build ancestor chain from scaffold data
- **Context metadata**: Inform LLM about truncation
- **Phase-0 context**: Exact schema for LLM consumption

#### 7. **Agent System** (`agent.py`, `phase0_agent.py`)
- **Abstract base class**: Common interface for all agents with workspace integration
- **LLM integration**: JSON repair and strict validation
- **Phase-0 agent**: DFS traversal with worklist management
- **Telemetry collection**: Comprehensive run statistics
- **Workspace encapsulation**: All agents interact with filesystem through Workspace object

#### 8. **Sanitization** (`sanitize.py`)
- **Output sanitization**: Post-process LLM responses
- **Language canonicalization**: Map language names to canonical forms
- **Confidence punishment**: Reduce confidence for insufficient evidence
- **Configurable caps**: Limits on summaries, languages, tags, evidence

#### 9. **Learning System** (`learning.py`) - Temporarily Disabled
- **Marker learning**: Learn new markers from repository structure
- **Language learning**: Learn new language mappings
- **Post-snapshot passes**: Re-run learning after snapshot completion
- **Re-scoring**: Update scores based on learned information

#### 10. **Phase-0 Engine** (`phase0_agent.py`)
- **DFS traversal**: Depth-first search with unified state management
- **Analysis persistence**: Save analysis results to scaffold via workspace
- **Telemetry collection**: Comprehensive run statistics via workspace
- **Resume capability**: Continue from state database
- **Workspace integration**: All filesystem operations delegated to workspace object
- **LLM integration**: Currently commented out, focusing on filesystem tree building

## Implementation Details

### CLI Interface (`main.py`)

#### Command Structure
```bash
python main.py <repo_path> <command> [options]
```

#### Commands
- **`init-workspace`**: Initialize .spade workspace directory
- **`clean`**: Clean .spade workspace directory
- **`refresh`**: Rebuild snapshot and reset worklist
- **`phase0 [--break-lock]`**: Run Phase-0 analysis
- **`inspect <phase> [relpath]`**: Preview context for debugging

#### Key Features
- **Click-based CLI**: Modern command-line interface with automatic help generation
- **Logical command structure**: `REPO_PATH` as first parameter, command-specific options
- **Configuration-driven**: All settings via `run_phase0.yaml`
- **Error handling**: Comprehensive error reporting and logging
- **Telemetry**: Automatic collection of run statistics
- **Safety features**: Lock management and graceful shutdown
- **Debug tools**: Context inspection and preview generation

### Configuration System

#### RunConfig Schema
```python
class RunConfig(BaseModel):
    model: str                   # LLM model to use
    caps: Caps                   # Configurable limits
    limits: Limits              # Runtime limits
    scoring: Scoring            # Scoring weights and parameters
    policies: Policies          # Runtime policies
    learn_markers: bool         # Learning settings
    marker_learning: MarkerLearning  # Learning parameters
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

### ✅ Completed Features (Tasks 1-25)

#### Core Infrastructure
1. **Configuration System**: Centralized `run_phase0.yaml` with Pydantic validation
2. **Data Models**: Comprehensive Pydantic schemas for all data structures
3. **Workspace Management**: Single point of interaction for all filesystem operations
4. **Logging System**: Singleton logger with file and console output

#### Phase-0 Core
5. **Unified State Management**: SQLite-based state management for files and directories
6. **Ignore Engine**: Pattern-based skip logic with allow overrides
7. **Marker Detection**: Configurable marker rules and detection
8. **Language Mapping**: Seed and learned language mappings
9. **Deterministic Scoring**: Evidence-based child scoring (temporarily disabled)
10. **Context Building**: Token-safe LLM context generation
11. **Scaffold Store**: Persistent understanding with merge semantics
12. **Prompt Management**: Template loading and context injection
13. **LLM Client**: JSON repair and strict validation
14. **Navigation Guardrails**: Safe navigation with fallbacks (temporarily disabled)
15. **Phase-0 Traversal**: DFS with unified state management
16. **Learning Passes**: Post-snapshot marker and language learning (temporarily disabled)
17. **Output Sanitization**: LLM response processing and validation (temporarily disabled)
18. **State Persistence**: SQLite-based traversal state management
19. **Report Generation**: JSON and Markdown report output (temporarily disabled)
20. **CLI Interface**: Click-based subcommand architecture with configuration
21. **Token Safety**: Configurable context caps and limits
22. **Sanitizer Hardening**: Configurable output processing
23. **Unit Testing**: Comprehensive test suite (83 tests)
24. **Workspace-Centric Architecture**: Complete encapsulation of filesystem operations through Workspace object
25. **Filesystem Tree Building**: Upfront scanning and metadata collection without LLM

### 🔧 Technical Specifications
- **Python Version**: 3.8+
- **Dependencies**: `pydantic`, `pathspec`, `pytest`, `click`
- **File Encoding**: UTF-8 throughout
- **Configuration**: YAML-based with Pydantic validation
- **Testing**: Pytest with fixtures and temporary directories

### 📁 Output Structure
```
target_repo/
└── .spade/
    ├── run_phase0.yaml       # Configuration file (YAML with comments)
    ├── .spadeignore          # Ignore patterns
    ├── .spadeallow           # Allow overrides
    ├── spade.db              # Unified SQLite database (files, directories, telemetry)
    ├── scaffold/             # Scaffold data
    │   ├── repository_scaffold.json
    │   └── high_level_components.json
    ├── analysis/             # Analysis results
    ├── checkpoints/          # Traversal checkpoints
    ├── reports/              # Generated reports
    ├── summary.json          # Run summary
    └── spade.log            # Debug logs
```

## Usage Examples

### Basic Usage
```bash
# Initialize workspace with default configuration
python main.py . init-workspace

# Run Phase-0 analysis
python main.py . phase0

# Run Phase-0 with lock override
python main.py . phase0 --break-lock

# Refresh analysis (rebuild snapshot and reset worklist)
python main.py . refresh

# Preview context for debugging
python main.py . inspect phase0

# Clean workspace
python main.py . clean
```

### Configuration
```yaml
# SPADE Phase-0 Configuration
model: gpt-5-nano # LLM model to use for analysis

caps:
  samples:
    max_dirs: 8 # Maximum directories to sample per directory
    max_files: 8 # Maximum files to sample per directory
  nav:
    max_children_per_step: 4 # Maximum children to navigate per step
  context:
    max_siblings_in_prompt: 200 # Maximum siblings in prompt

limits:
  max_depth: 0 # Maximum traversal depth (0 = unlimited)
  max_nodes: 0 # Maximum nodes to visit (0 = unlimited)
  max_llm_calls: 0 # Maximum LLM calls (0 = unlimited)

scoring:
  weights:
    marker: 0.55 # Weight for marker-based evidence
    lang: 0.25 # Weight for language-based evidence
    name: 0.15 # Weight for name-based evidence
    size: 0.05 # Weight for size-based evidence
```

## Development Decisions

### 1. Pydantic v2 Integration
- **Rationale**: Strict data validation, type safety, serialization
- **Implementation**: All data structures use Pydantic models
- **Benefits**: Runtime validation, clear error messages, JSON compatibility

### 2. Configuration-Driven Design
- **Rationale**: Single source of truth, runtime flexibility
- **Implementation**: Centralized `run_phase0.yaml` with Pydantic validation and inline comments
- **Benefits**: Easy configuration changes, validation, self-documenting configuration

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

### 6. Workspace-Centric Design
- **Rationale**: Single point of interaction for all filesystem operations
- **Implementation**: Workspace object encapsulates all .spade directory operations
- **Benefits**: Encapsulation, testability, consistency across phases, future extensibility

### 7. Unified State Management
- **Rationale**: Eliminate data fragmentation and provide ACID-compliant state management
- **Implementation**: `SpadeState` class with SQLite backend manages all files, directories, and telemetry
- **Benefits**: Unified API, better performance, data integrity, easier extension, clean separation of metadata and content

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
1. **Configuration Errors**: Check `run_phase0.yaml` syntax and Pydantic validation
2. **Permission Errors**: Verify directory access rights
3. **LLM Failures**: Check API key and internet connection
4. **Test Failures**: Run `python -m pytest tests/ -v` from parent directory
5. **Corrupted Data**: Use `python main.py . clean` to reset workspace if dirmeta files are corrupted

### Debug Information
- **Logs**: Check `.spade/spade.log` for detailed debug information
- **Configuration**: Review `run_phase0.yaml` for settings
- **Test Output**: Run tests with `-v` flag for verbose output

This knowledge base captures the complete state of SPADE Phase 0 development and provides a foundation for future enhancements and maintenance.
