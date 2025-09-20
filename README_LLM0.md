# LLM-Based RIG Generation System

This is an experimental LLM-based approach to generate Repository Intelligence Graphs (RIG) using `agentkit-gf` and `gpt-5-nano` with temperature 0 for deterministic behavior.

## Overview

The system replaces the current CMake-specific parser with a system-agnostic approach that can work with any build system while maintaining strict evidence-based architecture.

## Architecture

### Four-Phase Agent Pipeline

1. **Repository Discovery Agent** - Systematically discovers and catalogs build system evidence
2. **Component Classification Agent** - Classifies and categorizes build components based on evidence
3. **Relationship Mapping Agent** - Establishes dependencies and relationships between components
4. **RIG Assembly Agent** - Assembles the final RIG structure with comprehensive validation

### Key Features

- **Evidence-First Architecture** - Only uses first-party evidence, never makes assumptions
- **Deterministic Behavior** - Temperature 0 ensures consistent output
- **System-Agnostic** - Works with CMake, Cargo, npm, Python, Go, Java projects
- **Dynamic Prompt Refinement** - Prompts can be improved based on validation feedback

## Installation

1. Install dependencies:
```bash
pip install -r requirements_llm0.txt
```

2. Set your OpenAI API key:
```bash
export OPENAI_API_KEY="sk-..."
```

## Usage

### Basic Usage

```python
from llm0_rig_generator import LLMRIGGenerator
from pathlib import Path

# Initialize generator
generator = LLMRIGGenerator(Path("path/to/repository"))

# Run discovery phase
discovery_result = generator.discover_repository()

if discovery_result.success:
    print("Discovery successful!")
    print(f"Repository info: {discovery_result.repository_info}")
    print(f"Evidence catalog: {discovery_result.evidence_catalog}")
```

### Command Line Usage

```bash
python llm0_rig_generator.py /path/to/repository
```

## Testing

Run the test suite:

```bash
python test_llm0_discovery.py
```

This will:
1. Create a simple CMake test project
2. Test the Repository Discovery Agent
3. Validate evidence extraction quality
4. Test with existing repositories (if available)

## Current Status

### ✅ Phase 1: Repository Discovery Agent
- **Implemented**: Basic repository discovery with DelegatingToolsAgent
- **Features**: CMake File API detection, build system identification
- **Testing**: Simple CMake project validation

### 🚧 Phase 2: Component Classification Agent
- **Status**: Not yet implemented
- **Planned**: Evidence-based component classification

### 🚧 Phase 3: Relationship Mapping Agent  
- **Status**: Not yet implemented
- **Planned**: Dependency and relationship mapping

### 🚧 Phase 4: RIG Assembly Agent
- **Status**: Not yet implemented
- **Planned**: Final RIG structure assembly

## Evidence Sources

The system prioritizes evidence sources in this order:

1. **Build System APIs** - CMake File API, Cargo metadata, npm info
2. **Test Frameworks** - CTest, pytest, cargo test, etc.
3. **Build Files** - CMakeLists.txt, package.json, Cargo.toml, etc.
4. **Cache/Config** - CMakeCache.txt, package-lock.json, etc.

## Deterministic Behavior

The system ensures deterministic behavior through:

- **Temperature 0** - All LLM calls use greedy sampling
- **Structured Prompts** - Clear decision trees and validation rules
- **Evidence-Only** - No heuristics or assumptions
- **Validation Checkpoints** - Comprehensive validation at each phase

## Comparison with Current System

| Feature          | Current System       | LLM-Based System                    |
| ---------------- | -------------------- | ----------------------------------- |
| Build Systems    | CMake only           | CMake, Cargo, npm, Python, Go, Java |
| Evidence Sources | CMake File API       | Multiple build system APIs          |
| Deterministic    | Yes                  | Yes (temperature 0)                 |
| Extensible       | Limited              | Highly extensible                   |
| Maintenance      | CMake-specific logic | Generic prompt-based                |

## Development

### Adding New Build Systems

1. Add evidence extraction prompts in `llm0_prompts.md`
2. Update decision trees for new build system patterns
3. Test with real repositories
4. Refine prompts based on validation feedback

### Prompt Refinement

The system includes dynamic prompt refinement based on validation feedback:

1. Analyze validation results
2. Identify common error patterns
3. Update prompt instructions
4. Add specific examples for error cases
5. Test refined prompts

## Files

- `llm0_rig_generator.py` - Main implementation
- `llm0_prompts.md` - Comprehensive prompt design
- `llm0plan.md` - Implementation plan and architecture
- `test_llm0_discovery.py` - Test suite
- `requirements_llm0.txt` - Dependencies

## Next Steps

1. **Complete Phase 1** - Validate Repository Discovery Agent
2. **Implement Phase 2** - Component Classification Agent
3. **Implement Phase 3** - Relationship Mapping Agent
4. **Implement Phase 4** - RIG Assembly Agent
5. **Performance Testing** - Compare with current system
6. **Production Ready** - Error handling and optimization
