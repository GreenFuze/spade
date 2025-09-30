# LLM0 Phases Detail - Agent Behavior Analysis

## Abstract

The LLM0 Repository Intelligence Graph (RIG) generation system represents a novel approach to automated build system analysis through Large Language Model (LLM) orchestration. This document provides a comprehensive analysis of the eight-phase agent architecture (V4), detailing the behavioral patterns, evidence-based methodologies, and technical implementation of each specialized agent. The system employs deterministic LLM interactions with temperature 0 (greedy sampling) to ensure reproducible, evidence-based repository analysis across diverse build systems including CMake, Maven, npm, Cargo, and others.

## 1. Introduction

### 1.1 System Architecture Overview

The LLM0 RIG generation system implements a sophisticated eight-phase agent architecture designed to systematically analyze software repositories and generate canonical, evidence-based representations of build components, dependencies, and relationships. Each phase employs a specialized agent optimized for specific aspects of repository analysis, with clean context management and evidence-based approaches.

### 1.2 Core Design Principles

**Evidence-Based Architecture**: All conclusions must be backed by first-party evidence from repository files, build system configurations, and source code analysis. No heuristics or assumptions are permitted.

**Deterministic Behavior**: Temperature 0 (greedy sampling) ensures reproducible results across multiple runs, critical for research and production applications.

**System Agnostic**: The architecture supports any build system without code modifications, enabling analysis of CMake, Maven, npm, Cargo, Python, Go, and other build systems.

**Context Isolation**: Each agent receives only relevant context from previous phases, preventing context pollution and enabling targeted optimization.

**Fail-Fast Philosophy**: When evidence is insufficient, the system reports UNKNOWN rather than making assumptions, ensuring data integrity.

## 2. Phase 1: Repository Overview Agent

### 2.1 Purpose and Scope

The Repository Overview Agent serves as the initial reconnaissance phase, performing high-level structural analysis and build system identification. This agent establishes the foundational understanding of the repository's architecture, build systems, and exploration scope for subsequent phases.

### 2.2 Behavioral Analysis

#### 2.2.1 Natural Exploration Methodology

The agent employs a systematic exploration strategy that begins with directory listing operations to establish ground truth about file existence. This evidence-based approach prevents path hallucination and ensures all subsequent operations are based on verified file presence.

**Exploration Sequence**:
1. **Root Directory Analysis**: Initial `list_dir` operation to catalog available files and directories
2. **Build System Detection**: Identification of build system configuration files through pattern matching
3. **Directory Classification**: Categorization of directories by purpose (source, test, build, documentation)
4. **Entry Point Discovery**: Identification of main configuration files and project entry points
5. **Scope Definition**: Determination of exploration priorities for subsequent phases

#### 2.2.2 Evidence-Based File Access Protocol

The agent implements a strict evidence-based file access protocol that requires verification of file existence before any read operations. This protocol prevents the common LLM failure mode of attempting to access non-existent files.

**Verification Protocol**:
- **Pre-Read Verification**: All file access operations must be preceded by directory listing verification
- **Glob Pattern Filtering**: Efficient file discovery using pattern matching (e.g., `*.cmake`, `CMakeLists.txt`)
- **Existence Confirmation**: Files are only read if their existence is confirmed through directory operations
- **Error Handling**: Graceful handling of missing files with context updates

#### 2.2.3 Build System Guidance Strategy

Rather than arbitrary file scanning, the agent follows build system logic to guide exploration. This approach ensures efficient analysis while maintaining evidence-based principles.

**Guidance Mechanisms**:
- **Configuration File Priority**: Build system configuration files receive highest priority
- **Dependency Chain Following**: Natural exploration following build system dependency chains
- **Framework Detection**: Identification of testing frameworks and development tools
- **Language Detection**: Analysis of file extensions and content for programming language identification

### Input
- Repository path
- No previous context (clean slate)

### Output
```json
{
  "repository_info": {
    "path": "repository_path",
    "build_systems": [
      {
        "type": "string (discovered from evidence)",
        "version": "string|UNKNOWN",
        "config_files": ["path1", "path2"],
        "api_available": true|false,
        "evidence": "string describing what evidence led to this conclusion"
      }
    ],
    "source_directories": ["path1", "path2"],
    "test_directories": ["path1", "path2"]
  },
  "evidence_catalog": {
    "cmake_file_api": {
      "available": true|false,
      "index_file": "path|UNKNOWN"
    },
    "test_frameworks": [
      {
        "type": "string (discovered from evidence)",
        "config_files": ["path1", "path2"],
        "evidence": "string describing what evidence led to this conclusion"
      }
    ]
  }
}
```

### Critical Rules
- ALWAYS use list_dir to see what files exist before trying to read them
- If a file is not in the directory listing, DO NOT try to read it
- Focus on build system configuration files and key source files only
- Let the build system guide exploration, not arbitrary file scanning

### Tools Used
- `list_dir`: Explore directory structure with optional glob filtering
- `read_text`: Read build system configuration files
- `delegate_ops`: Gateway to all file operations

## Phase 2: Classification Agent

### Purpose
Classify components based on discovery results with detailed line-level evidence.

### Key Behaviors
- **Evidence-Based Classification**: Uses discovery results to guide component analysis
- **Line-Level Evidence**: Provides specific line numbers and content for each component
- **Component Type Detection**: Identifies executables, libraries, tests, etc.
- **Programming Language Detection**: Determines language from source files and build configuration
- **Dependency Analysis**: Maps component dependencies and relationships

### Input
- Repository path
- Discovery results from Phase 1

### Output
```json
{
  "components": [
    {
      "name": "component_name",
      "type": "executable|library|test|utility",
      "programming_language": "C++|Java|Python|Go|etc",
      "source_files": ["path1", "path2"],
      "evidence": [
        {
          "file": "CMakeLists.txt",
          "lines": "L5-L5",
          "content": "add_executable(component_name src/main.cpp)",
          "reason": "CMake defines an executable target with source file main.cpp."
        }
      ],
      "dependencies": ["dep1", "dep2"],
      "test_relationship": "test_component_name runs component_name according to CMake test configuration"
    }
  ]
}
```

### Critical Rules
- Use discovery results to guide exploration
- Focus on source files and build configuration for component classification
- Provide detailed evidence with line numbers and content
- Map test relationships to components

### Tools Used
- `read_text`: Read source files and build configuration
- `list_dir`: Explore component directories
- `delegate_ops`: Gateway to all file operations

## Phase 3: Relationships Agent

### Purpose
Map dependencies and relationships between components based on previous results.

### Key Behaviors
- **Dependency Mapping**: Establishes build dependencies between components
- **Include Relationships**: Maps header file includes and dependencies
- **Test Relationships**: Links test components to their targets
- **Transitive Dependencies**: Resolves indirect dependencies through component chains
- **Evidence-Based Mapping**: Uses build system evidence to establish relationships

### Input
- Repository path
- Discovery results from Phase 1
- Classification results from Phase 2

### Output
```json
{
  "relationships": [
    {
      "source": "component_a",
      "target": "component_b",
      "type": "build_dependency|include_dependency|test_relationship",
      "evidence": "CMakeLists.txt shows component_a depends on component_b",
      "strength": "direct|transitive"
    }
  ],
  "dependency_graph": {
    "nodes": ["component1", "component2"],
    "edges": [
      {
        "from": "component1",
        "to": "component2",
        "type": "depends_on"
      }
    ]
  }
}
```

### Critical Rules
- Use previous phase results to guide relationship mapping
- Focus on build files and source files that show dependencies
- Map both direct and transitive dependencies
- Provide evidence for each relationship

### Tools Used
- `read_text`: Read build files and source files for dependency analysis
- `delegate_ops`: Gateway to all file operations

## Phase 4: Assembly Agent

### Purpose
Assemble the final RIG from all previous results with validation.

### Key Behaviors
- **RIG Construction**: Creates the final RIG object with all components and relationships
- **Validation**: Ensures all data is properly structured and consistent
- **Evidence Integration**: Combines evidence from all previous phases
- **Final Assembly**: Produces a complete, validated RIG object

### Input
- Repository path
- Discovery results from Phase 1
- Classification results from Phase 2
- Relationships results from Phase 3

### Output
- Complete RIG object with all components, relationships, and evidence

### Critical Rules
- Use all previous phase results to build the final RIG
- Ensure all components have proper evidence
- Validate relationships and dependencies
- Produce a complete, consistent RIG object

### Tools Used
- `delegate_ops`: Gateway to any final file operations needed

## Agent Architecture

### BaseLLMAgent
- **Common Functionality**: Shared methods for all agents
- **Tool Management**: FileTools and ProcessTools with repository scope
- **Request Tracking**: Monitors request count and limits
- **JSON Parsing**: Handles LLM response parsing and validation

### Agent Configuration
```python
DelegatingToolsAgent(
    model="openai:gpt-5-nano",
    tool_sources=[FileTools, ProcessTools],
    builtin_enums=[],
    model_settings=ModelSettings(temperature=0),
    real_time_log_user=True,
    real_time_log_agent=True
)
```

### Context Management
- **Clean Context**: Each agent starts fresh with only relevant previous results
- **No Context Pollution**: Previous phase results are passed as structured input
- **Current Directory Focus**: Only provide current directory context, not all previous directories
- **Natural Exploration**: Let LLM choose which directories to explore

## Key Technical Features

### Evidence-Based Approach
- **No Assumptions**: Never guess about file existence or structure
- **Verification First**: Always verify file existence through directory listing
- **Line-Level Evidence**: Provide specific line numbers and content for all conclusions
- **Build System Guidance**: Follow build system logic, not arbitrary exploration

### Error Handling
- **Graceful Degradation**: Handle missing files and incomplete data gracefully
- **Evidence Preservation**: Maintain evidence even when some data is missing
- **Clear Error Messages**: Provide specific, actionable error information

### Performance Optimization
- **Glob Filtering**: Efficient file filtering with pattern matching
- **Targeted Exploration**: Focus on build system relevant files only
- **Context Management**: Prevent context explosion in large repositories
- **Request Efficiency**: Minimize unnecessary file operations

## Success Metrics

### Discovery Phase
- ✅ **No Path Hallucination**: LLM correctly identifies actual paths
- ✅ **Evidence-Based Discovery**: All conclusions backed by actual file verification
- ✅ **Clean Context Management**: Successful exploration without context overwhelm
- ✅ **Build System Detection**: Correctly identifies build system type and configuration

### Classification Phase
- ✅ **Component Detection**: Identifies all major components (executables, libraries, tests)
- ✅ **Language Detection**: Correctly determines programming languages
- ✅ **Line-Level Evidence**: Provides detailed evidence with line numbers
- ✅ **Dependency Mapping**: Maps component dependencies and relationships

### Relationships Phase
- ✅ **Dependency Resolution**: Establishes build dependencies between components
- ✅ **Test Relationships**: Links test components to their targets
- ✅ **Transitive Dependencies**: Resolves indirect dependencies
- ✅ **Evidence Integration**: Combines evidence from all previous phases

### Assembly Phase
- ✅ **RIG Construction**: Creates complete, validated RIG object
- ✅ **Data Consistency**: Ensures all data is properly structured
- ✅ **Evidence Preservation**: Maintains all evidence from previous phases
- ✅ **Final Validation**: Produces a complete, consistent RIG

## V4 Eight-Phase Architecture

The V4 architecture expands the original four-phase approach into eight specialized phases, each optimized for specific aspects of repository analysis. This provides deeper exploration and more granular discovery capabilities.

### Phase 1: Repository Overview Agent

#### Purpose
High-level repository structure analysis and build system identification.

#### Key Behaviors
- **Repository Scanning**: Performs initial high-level scan of repository structure
- **Build System Detection**: Identifies primary build systems (CMake, Maven, npm, etc.)
- **Directory Classification**: Categorizes directories by purpose (source, test, build, docs)
- **Entry Point Discovery**: Identifies main entry points and configuration files
- **Scope Definition**: Determines which directories to explore in detail

#### Input
- Repository path
- No previous context (clean slate)

#### Output
```json
{
  "repository_overview": {
    "name": "repository_name",
    "type": "application|library|framework|tool",
    "primary_language": "C++|Java|Python|JavaScript|Go|etc",
    "build_systems": ["cmake", "maven", "npm"],
    "directory_structure": {
      "source_dirs": ["src", "lib", "core"],
      "test_dirs": ["tests", "test", "spec"],
      "build_dirs": ["build", "dist", "target"],
      "config_dirs": ["config", "scripts", "tools"]
    },
    "entry_points": ["CMakeLists.txt", "package.json", "pom.xml"],
    "exploration_scope": {
      "priority_dirs": ["src", "tests"],
      "skip_dirs": ["build", "node_modules", ".git"],
      "deep_exploration": ["src/main", "tests/unit"]
    }
  }
}
```

#### Critical Rules
- Focus on high-level structure, not detailed analysis
- Identify build systems from configuration files
- Determine exploration scope for subsequent phases
- Avoid deep directory traversal in this phase

### Phase 2: Source Structure Discovery Agent

#### Purpose
Comprehensive source directory and component discovery.

#### Key Behaviors
- **Source Mapping**: Maps all source directories and their contents
- **Component Identification**: Identifies potential components from source structure
- **Language Detection**: Determines programming languages from file extensions and content
- **Module Discovery**: Finds modules, packages, and logical groupings
- **Dependency Hints**: Identifies potential dependencies from import/include statements

#### Input
- Repository path
- Repository overview from Phase 1

#### Output
```json
{
  "source_structure": {
    "source_directories": [
      {
        "path": "src/main",
        "language": "C++",
        "components": ["main_app", "utils_lib"],
        "files": ["main.cpp", "utils.cpp", "utils.h"],
        "dependencies": ["boost", "opencv"]
      }
    ],
    "language_analysis": {
      "primary_language": "C++",
      "secondary_languages": ["Python", "Java"],
      "language_distribution": {
        "C++": 0.7,
        "Python": 0.2,
        "Java": 0.1
      }
    },
    "component_hints": [
      {
        "name": "main_app",
        "type": "executable",
        "source_files": ["src/main/main.cpp"],
        "language": "C++"
      }
    ]
  }
}
```

#### Critical Rules
- Focus on source directories identified in Phase 1
- Analyze file extensions and content for language detection
- Identify potential components from source structure
- Map import/include statements for dependency hints

### Phase 3: Test Structure Discovery Agent

#### Purpose
Test framework and test directory discovery.

#### Key Behaviors
- **Test Framework Detection**: Identifies testing frameworks (CTest, JUnit, pytest, etc.)
- **Test Organization**: Maps test directory structure and organization
- **Test Configuration**: Analyzes test configuration files and settings
- **Test Coverage**: Identifies what components are tested
- **Test Execution**: Discovers test execution patterns and commands

#### Input
- Repository path
- Repository overview from Phase 1
- Source structure from Phase 2

#### Output
```json
{
  "test_structure": {
    "test_frameworks": [
      {
        "name": "CTest",
        "version": "3.10+",
        "config_files": ["CMakeLists.txt"],
        "test_directories": ["tests", "test"]
      }
    ],
    "test_organization": {
      "test_directories": [
        {
          "path": "tests/unit",
          "framework": "CTest",
          "test_files": ["test_main.cpp", "test_utils.cpp"],
          "targets": ["main_app", "utils_lib"]
        }
      ]
    },
    "test_configuration": {
      "test_command": "ctest",
      "test_timeout": "300",
      "parallel_tests": true
    }
  }
}
```

#### Critical Rules
- Focus on test directories identified in Phase 1
- Analyze test configuration files for framework detection
- Map test files to their target components
- Identify test execution patterns and commands

### Phase 4: Build System Analysis Agent

#### Purpose
Build configuration and target analysis.

#### Key Behaviors
- **Build Configuration**: Analyzes build system configuration files
- **Target Discovery**: Identifies all build targets (executables, libraries, tests)
- **Dependency Mapping**: Maps build dependencies between targets
- **Build Options**: Discovers build options, flags, and configurations
- **Output Analysis**: Determines build outputs and artifacts

#### Input
- Repository path
- Repository overview from Phase 1
- Source structure from Phase 2
- Test structure from Phase 3

#### Output
```json
{
  "build_analysis": {
    "build_targets": [
      {
        "name": "main_app",
        "type": "executable",
        "source_files": ["src/main/main.cpp"],
        "dependencies": ["utils_lib"],
        "output_path": "build/main_app",
        "build_options": ["-O2", "-Wall"]
      }
    ],
    "build_dependencies": [
      {
        "source": "main_app",
        "target": "utils_lib",
        "type": "link_dependency"
      }
    ],
    "build_configuration": {
      "build_type": "Debug|Release",
      "compiler": "gcc|clang|msvc",
      "flags": ["-std=c++17", "-Wall"]
    }
  }
}
```

#### Critical Rules
- Analyze build system configuration files in detail
- Map all build targets and their dependencies
- Identify build options and configurations
- Determine build outputs and artifacts

### Phase 5: Artifact Discovery Agent

#### Purpose
Build output files and artifacts discovery.

#### Key Behaviors
- **Artifact Detection**: Identifies build output files and artifacts
- **Output Mapping**: Maps build targets to their output files
- **Artifact Types**: Classifies artifacts by type (executables, libraries, packages)
- **Installation Analysis**: Discovers installation targets and procedures
- **Distribution Preparation**: Identifies distribution and packaging artifacts

#### Input
- Repository path
- All previous phase results

#### Output
```json
{
  "artifact_analysis": {
    "build_artifacts": [
      {
        "name": "main_app",
        "type": "executable",
        "output_file": "build/main_app.exe",
        "size": "1024KB",
        "dependencies": ["msvcrt.dll"]
      }
    ],
    "library_artifacts": [
      {
        "name": "utils_lib",
        "type": "static_library",
        "output_file": "build/utils_lib.lib",
        "size": "256KB"
      }
    ],
    "package_artifacts": [
      {
        "name": "java_hello_lib",
        "type": "jar",
        "output_file": "build/java_hello_lib-1.0.0.jar",
        "version": "1.0.0"
      }
    ]
  }
}
```

#### Critical Rules
- Focus on build output directories
- Map build targets to their actual output files
- Classify artifacts by type and purpose
- Identify installation and distribution artifacts

### Phase 6: Component Classification Agent

#### Purpose
Classify all discovered entities into RIG types.

#### Key Behaviors
- **Component Classification**: Classifies all discovered entities into RIG component types
- **Type Determination**: Determines component types (executable, library, test, utility, etc.)
- **Runtime Analysis**: Analyzes runtime requirements and dependencies
- **Evidence Integration**: Combines evidence from all previous phases
- **Validation**: Validates component classifications against RIG schema

#### Input
- Repository path
- All previous phase results

#### Output
```json
{
  "classified_components": [
    {
      "name": "main_app",
      "type": "executable",
      "programming_language": "C++",
      "runtime": "native",
      "source_files": ["src/main/main.cpp"],
      "output_path": "build/main_app.exe",
      "evidence": [
        {
          "file": "CMakeLists.txt",
          "lines": "L5-L5",
          "content": "add_executable(main_app src/main/main.cpp)",
          "reason": "CMake defines executable target"
        }
      ],
      "dependencies": ["utils_lib"],
      "test_relationship": "test_main_app"
    }
  ]
}
```

#### Critical Rules
- Use all previous phase results for comprehensive classification
- Provide detailed evidence for each component
- Validate component types against RIG schema
- Map dependencies and relationships

### Phase 7: Relationship Mapping Agent

#### Purpose
Map dependencies and relationships between entities.

#### Key Behaviors
- **Dependency Mapping**: Maps all dependencies between components
- **Relationship Types**: Identifies different types of relationships (build, test, runtime)
- **Transitive Dependencies**: Resolves indirect dependencies
- **Evidence Integration**: Combines evidence from all previous phases
- **Graph Construction**: Builds relationship graph structure

#### Input
- Repository path
- All previous phase results

#### Output
```json
{
  "relationship_mapping": {
    "relationships": [
      {
        "source": "main_app",
        "target": "utils_lib",
        "type": "build_dependency",
        "strength": "direct",
        "evidence": [
          {
            "file": "CMakeLists.txt",
            "lines": "L6-L6",
            "content": "target_link_libraries(main_app utils_lib)",
            "reason": "CMake links main_app to utils_lib"
          }
        ]
      }
    ],
    "relationship_graph": {
      "nodes": [
        {
          "id": "main_app",
          "type": "executable",
          "label": "main_app"
        }
      ],
      "edges": [
        {
          "source": "main_app",
          "target": "utils_lib",
          "type": "depends_on",
          "strength": "direct"
        }
      ]
    }
  }
}
```

#### Critical Rules
- Map all dependencies identified in previous phases
- Provide evidence for each relationship
- Build complete relationship graph
- Identify transitive dependencies

### Phase 8: RIG Assembly Agent

#### Purpose
Assemble final RIG with validation.

#### Key Behaviors
- **RIG Construction**: Assembles final RIG from all previous results
- **Data Integration**: Integrates all discovered data into RIG structure
- **Validation**: Validates RIG against schema requirements
- **Evidence Preservation**: Preserves all evidence from previous phases
- **Final Assembly**: Produces complete, validated RIG object

#### Input
- Repository path
- All previous phase results

#### Output
- Complete RIG object with all components, relationships, and evidence

#### Critical Rules
- Integrate all data from previous phases
- Validate RIG against schema requirements
- Preserve all evidence and relationships
- Produce complete, consistent RIG object

## Future Improvements

1. **Performance Optimization**: Further reduce token usage and execution time
2. **Error Recovery**: Add retry logic for failed operations
3. **Context Optimization**: Improve context management for very large repositories
4. **Validation Enhancement**: Add more comprehensive validation checks
5. **Tool Integration**: Add more specialized tools for different build systems
6. **Phase Optimization**: Fine-tune each phase for specific repository types
7. **Parallel Processing**: Explore parallel execution of independent phases
8. **Incremental Updates**: Support incremental RIG updates for repository changes

