# LLM-Based RIG Generation Plan (Temperature 0)

## Executive Summary

This document outlines a comprehensive plan to replace the current CMake-specific RIG generation system with an LLM-based approach using `agentkit-gf` and `gpt-5-nano` with temperature 0 (greedy sampling). This approach will make the RIG generation system-agnostic and deterministic while maintaining the strict evidence-based architecture.

## Current System Analysis

### RIG Structure (from `rig.py` and `schemas.py`)

The RIG contains:
- **Repository-level info**: `RepositoryInfo`, `BuildSystemInfo`
- **Build entities**: `Component`, `Aggregator`, `Runner`, `Utility`, `Test`
- **Supporting data**: `Evidence`, `ComponentLocation`, `ExternalPackage`, `PackageManager`
- **Lookup dictionaries**: For efficient access by name

### Core Requirements (from knowledgebase)

1. **Evidence-based approach** - No heuristics, only first-party evidence
2. **Fail-fast behavior** - Report UNKNOWN when evidence is insufficient
3. **Deterministic output** - Same input always produces same output
4. **Zero tolerance for made-up data** - Never use placeholder fallbacks
5. **Proper None handling** - Return None when evidence cannot be determined

### Evidence Sources (Priority Order)

1. **Build System APIs** - CMake File API, Cargo metadata, npm/yarn info
2. **Test Frameworks** - CTest, pytest, cargo test, etc.
3. **Build Files** - CMakeLists.txt, package.json, Cargo.toml, etc.
4. **Cache/Config** - CMake cache, package lock files, etc.

## AgentKit-GF Analysis

### Framework Capabilities

**SoftToolAgent**:
- True soft tools with schema-guided envelope system
- Model decides when to use tools via `OPEN_RESPONSE` / `TOOL_CALL` / `TOOL_RESULT`
- Maintains persistent transcript across turns
- Perfect for reasoning-first tasks

**DelegatingToolsAgent**:
- Single gateway tool (`delegate_ops`) that delegates to internal executor
- Reduces tool gravity and maintains clean reasoning loop
- Built-in tools: FileTools, ProcessTools, WebSearch
- Supports custom tool sources with automatic method exposure

### Available Tools

**FileTools**:
- `read_text(path, max_bytes=200_000)`
- `write_text(path, content, overwrite=False)`
- `stat(path)`, `list_dir(path)`
- `hash_file(path)`

**ProcessTools**:
- `run_process(argv, timeout_sec=10)`
- `run_shell(command, timeout_sec=10)`
- Policy controls for security

## LLM-Based RIG Architecture

### Phase 1: Repository Discovery Agent

**Purpose**: Systematically discover and catalog all build system evidence

**Agent Type**: `DelegatingToolsAgent` with FileTools and ProcessTools

**Responsibilities**:
1. **Repository Structure Analysis**
   - Scan repository root for build system indicators
   - Identify primary build system (CMake, Cargo, npm, etc.)
   - Map directory structure and key files

2. **Build System Detection**
   - Detect CMake projects (CMakeLists.txt, CMakeCache.txt)
   - Detect Rust projects (Cargo.toml, Cargo.lock)
   - Detect Node.js projects (package.json, package-lock.json)
   - Detect Python projects (setup.py, pyproject.toml, requirements.txt)
   - Detect Go projects (go.mod, go.sum)
   - Detect Java projects (pom.xml, build.gradle)

3. **Evidence Collection**
   - Extract build system API data (CMake File API, Cargo metadata)
   - Parse configuration files
   - Identify source files and build artifacts
   - Collect test definitions

**Output**: Structured evidence catalog with file paths, build system type, and available data sources

### Phase 2: Component Classification Agent

**Purpose**: Classify and categorize build components based on evidence

**Agent Type**: `SoftToolAgent` with custom classification tools

**Responsibilities**:
1. **Component Type Detection**
   - Analyze build artifacts and source files
   - Determine component types (executable, library, test, utility)
   - Classify based on file extensions, build commands, and metadata

2. **Language and Runtime Detection**
   - Identify programming languages from source files
   - Determine runtime environments (JVM, .NET, Python, Go, etc.)
   - Map languages to appropriate runtimes

3. **Test Framework Detection**
   - Identify test frameworks (Google Test, Catch2, pytest, etc.)
   - Classify test types (unit, integration, performance)
   - Link tests to their corresponding components

4. **External Package Detection**
   - Identify external dependencies
   - Determine package managers (vcpkg, Conan, npm, Cargo, etc.)
   - Extract package names and versions

**Output**: Classified components with evidence-based attributes

### Phase 3: Relationship Mapping Agent

**Purpose**: Establish dependencies and relationships between components

**Agent Type**: `SoftToolAgent` with relationship analysis tools

**Responsibilities**:
1. **Dependency Analysis**
   - Map direct dependencies between components
   - Calculate transitive dependencies
   - Identify circular dependencies

2. **Test-Component Linking**
   - Link test components to their corresponding test nodes
   - Establish bidirectional relationships
   - Handle test frameworks and test discovery

3. **Evidence Call Stack Construction**
   - Build complete call stacks from build system evidence
   - Trace target definitions to their source files
   - Filter out external package manager files

4. **Component Location Mapping**
   - Identify where components are built, copied, or moved
   - Map output paths and intermediate locations
   - Track component lifecycle through build process

**Output**: Complete relationship graph with evidence-based connections

### Phase 4: RIG Assembly Agent

**Purpose**: Assemble the final RIG structure with validation

**Agent Type**: `SoftToolAgent` with RIG construction tools

**Responsibilities**:
1. **RIG Entity Creation**
   - Create Pydantic model instances for all entities
   - Ensure proper evidence attachment
   - Validate required fields and relationships

2. **Evidence Consistency Validation**
   - Verify all evidence is properly captured
   - Check for contradictory information
   - Ensure no made-up data or placeholders

3. **RIG Structure Assembly**
   - Populate RIG with all entities
   - Build lookup dictionaries
   - Ensure proper entity relationships

4. **Final Validation**
   - Run comprehensive validation checks
   - Verify deterministic behavior
   - Ensure evidence-based architecture compliance

**Output**: Complete, validated RIG structure

## Implementation Strategy

### Agent Orchestration

```python
class LLMRIGGenerator:
    def __init__(self, repository_path: Path):
        self.repository_path = repository_path
        self.evidence_catalog = None
        self.classified_components = None
        self.relationship_graph = None
        self.rig = None
    
    def generate_rig(self) -> RIG:
        # Phase 1: Repository Discovery
        discovery_agent = self._create_discovery_agent()
        self.evidence_catalog = discovery_agent.discover_evidence()
        
        # Phase 2: Component Classification
        classification_agent = self._create_classification_agent()
        self.classified_components = classification_agent.classify_components(
            self.evidence_catalog
        )
        
        # Phase 3: Relationship Mapping
        relationship_agent = self._create_relationship_agent()
        self.relationship_graph = relationship_agent.map_relationships(
            self.classified_components
        )
        
        # Phase 4: RIG Assembly
        assembly_agent = self._create_assembly_agent()
        self.rig = assembly_agent.assemble_rig(
            self.relationship_graph
        )
        
        return self.rig
```

### Deterministic Prompt Engineering

**Key Principles**:
1. **Structured prompts** with clear evidence requirements
2. **Explicit UNKNOWN instructions** when evidence is insufficient
3. **Template-based responses** for consistent output format
4. **Validation checkpoints** at each phase

**Example Prompt Structure**:
```
You are a build system analysis agent. Your task is to analyze the provided evidence and classify build components.

CRITICAL RULES:
1. ONLY use provided evidence - never make assumptions
2. If evidence is insufficient, return "UNKNOWN" 
3. Never use placeholder data or made-up information
4. Provide specific evidence references for all classifications

EVIDENCE PROVIDED:
{evidence_data}

CLASSIFICATION TASK:
{task_description}

OUTPUT FORMAT:
{json_schema}

VALIDATION CHECKPOINTS:
- All fields must have evidence or be marked UNKNOWN
- No contradictory information allowed
- Evidence references must be valid file paths
```

### Evidence Validation Framework

```python
class EvidenceValidator:
    def validate_evidence(self, entity: Any, evidence: Evidence) -> bool:
        """Validate that entity has proper evidence"""
        # Check evidence completeness
        # Verify evidence traceability
        # Ensure no made-up data
        pass
    
    def validate_consistency(self, rig: RIG) -> List[ValidationError]:
        """Validate RIG consistency"""
        # Check for contradictions
        # Verify relationships
        # Ensure deterministic behavior
        pass
```

## Technical Implementation Details

### Agent Configuration

**Discovery Agent**:
```python
discovery_agent = DelegatingToolsAgent(
    model="openai:gpt-5-nano",
    builtin_enums=[],  # No web search needed
    tool_sources=[
        FileTools(root_dir=str(repository_path)),
        ProcessTools(root_cwd=str(repository_path), allowed_basenames=["cmake", "cargo", "npm", "python"])
    ],
    system_prompt="You are a repository discovery agent. Systematically scan the repository to identify build systems and collect evidence.",
    ops_system_prompt="Execute exactly one tool and return only its result."
)
```

**Classification Agent**:
```python
classification_agent = SoftToolAgent(
    model="openai:gpt-5-nano",
    system_prompt="You are a component classification agent. Classify build components based on evidence only."
)
```

### Custom Tools for RIG Generation

```python
class RIGAnalysisTools:
    def analyze_cmake_file_api(self, api_path: Path) -> dict:
        """Analyze CMake File API data"""
        pass
    
    def analyze_cargo_metadata(self, cargo_path: Path) -> dict:
        """Analyze Cargo metadata"""
        pass
    
    def classify_component_type(self, evidence: dict) -> ComponentType:
        """Classify component type from evidence"""
        pass
    
    def detect_runtime(self, evidence: dict) -> Runtime:
        """Detect runtime environment from evidence"""
        pass
```

### Deterministic Behavior Guarantees

1. **Temperature 0**: All agents use `gpt-5-nano` with temperature 0
2. **Structured Prompts**: Consistent prompt templates ensure deterministic responses
3. **Evidence-Only**: No heuristics or assumptions, only evidence-based decisions
4. **Validation**: Comprehensive validation ensures consistent output
5. **Reproducible**: Same repository input always produces same RIG output

## Validation Strategy

### Comparison with Current System

1. **Side-by-Side Testing**: Run both systems on same repository
2. **Evidence Verification**: Ensure all evidence is properly captured
3. **Deterministic Testing**: Verify same input produces same output
4. **Edge Case Testing**: Test with various build systems and configurations
5. **Performance Benchmarking**: Compare speed and accuracy

### Validation Metrics

1. **Evidence Completeness**: All evidence sources properly captured
2. **Classification Accuracy**: Components correctly classified
3. **Relationship Accuracy**: Dependencies and relationships correctly mapped
4. **Deterministic Behavior**: Same input produces same output
5. **Performance**: Speed and resource usage comparison

## Advantages of LLM Approach

1. **System Agnostic**: Works with any build system (CMake, Cargo, npm, etc.)
2. **Deterministic**: Temperature 0 ensures consistent output
3. **Extensible**: Easy to add new build systems and languages
4. **Evidence-Based**: Can maintain strict evidence requirements
5. **Maintainable**: No hardcoded build system logic
6. **Reasoning-First**: LLM can reason about complex build relationships

## Challenges and Mitigations

### Challenges

1. **Performance**: LLM calls may be slower than direct parsing
2. **Token Limits**: Large repositories may exceed context windows
3. **Cost**: LLM API costs for large repositories
4. **Evidence Preservation**: Ensuring all evidence is properly captured
5. **Validation**: Need robust validation to ensure RIG quality

### Mitigations

1. **Chunking Strategy**: Break large repositories into manageable chunks
2. **Caching**: Cache LLM responses for deterministic behavior
3. **Hybrid Approach**: Use LLM for complex reasoning, direct parsing for simple cases
4. **Evidence Tracking**: Comprehensive evidence validation framework
5. **Incremental Validation**: Validate at each phase to catch issues early

## Implementation Phases

### Phase 1: Proof of Concept (Week 1-2)
- Implement basic discovery agent for CMake projects
- Create simple classification agent
- Test with small CMake repository
- Validate deterministic behavior

### Phase 2: Core Implementation (Week 3-4)
- Implement all four agent phases
- Add comprehensive validation
- Test with medium-sized repositories
- Compare with current system

### Phase 3: Multi-System Support (Week 5-6)
- Add support for Rust (Cargo) projects
- Add support for Node.js (npm) projects
- Test with mixed-language repositories
- Optimize performance

### Phase 4: Production Ready (Week 7-8)
- Add comprehensive error handling
- Implement caching and optimization
- Add extensive test suite
- Document and deploy

## Success Criteria

1. **Deterministic Output**: Same repository input always produces same RIG output
2. **Evidence-Based**: All RIG entities have proper evidence with no made-up data
3. **System Agnostic**: Works with CMake, Cargo, npm, and other build systems
4. **Performance**: Comparable or better performance than current system
5. **Accuracy**: Same or better accuracy than current CMake-specific system
6. **Maintainability**: Easier to extend and maintain than current system

## Next Steps

1. **Research agentkit-gf**: Understand framework capabilities and limitations
2. **Design agent prompts**: Create deterministic prompts for each phase
3. **Implement prototype**: Build minimal version with CMake support
4. **Validate approach**: Compare results with current system
5. **Scale and optimize**: Extend to multiple build systems

---

*This plan provides a comprehensive roadmap for implementing LLM-based RIG generation while maintaining the strict evidence-based architecture and deterministic behavior required by the current system.*
