Creating a New Test Repository
==============================

This guide explains how to design and add a realistic but compact test repository under `tests/test_repos/<name>` with a correct, deterministic ground‑truth RIG under `tests/deterministic/<name>`.

What the RIG Is
---------------
- RIG (Repository Information Graph) models buildable artifacts, meta targets, tests, external packages, evidence, and all dependency relations. It is the single source of truth used by the evaluation.
- Components are buildable artifacts (executables, libraries). One Component = one artifact. The Component's `relative_path` must point to the produced artifact (e.g., a C++ DLL: `native/image-core/build/image_core.dll`) and `source_files` must include all non‑test files that build it (e.g., `native/image-core/src/filter.cpp`, `processor.cpp`, `io.cpp`).
- Aggregators are meta targets (not Components). They produce no artifact, exist only to group other targets, and participate in dependency relations (dependency‑only targets). Do not conflate Aggregators with Components.
- Runners are custom targets that execute commands (no artifact). Aggregators cannot be runners, and runners are not aggregators.
- RIG is persisted to SQLite and exported to JSON via `core/rig.py::generate_prompts_json_data()`. Study these examples (CMake‑based) for end‑to‑end patterns and structure: `tests/deterministic/cmake/cmake_hello_world`, `tests/deterministic/cmake/jni_hello_world`, and `tests/deterministic/cmake/metaffi` (see each directory's `description.md` and `create_ground_truth.py`). RIG concepts are build‑system‑agnostic (see `knowledgebase.md`). If unsure how to classify an entity (Component vs Aggregator vs Runner), ask explicitly.

CRITICAL: Language Concepts vs RIG Components
---------------------------------------------
**The Golden Rule: One RIG Component = One Artifact File**

RIG Components represent **buildable artifacts** (executables, libraries, bundles), NOT language-level organizational concepts (packages, modules, namespaces). This distinction is critical and often causes confusion.

### Language Concepts vs Components

**Language Concepts (NOT Components):**
- **Go packages** (`internal/common/config`, `pkg/models`) — these are organizational units, not artifacts
- **npm packages** (`@myorg/auth-lib`, `@myorg/shared-utils`) — these are dependency units, not artifacts
- **Rust crates** (`crate::utils`, `crate::models`) — these are modules, not artifacts
- **Java packages** (`com.example.service`, `com.example.model`) — these are namespaces, not artifacts
- **C/C++ headers** (`utils.h`, `config.h`) — these are included files, not artifacts
- **Python modules** (`utils.py`, `models.py`) — these are source files, not artifacts

**RIG Components (Artifacts):**
- Executable binaries (`bin/api-server.exe`, `dist/app.js`)
- Shared libraries (`lib/utils.so`, `build/utils.dll`)
- Static libraries (`lib/utils.a`, `build/utils.lib`)
- Bundles (`dist/app.wasm`, `build/extension.zip`)

### Common Mistakes to Avoid

**WRONG: Modeling Go packages as separate Components**
```python
# ❌ WRONG: Don't model internal packages as Components
internal_config = Component(
    name="internal/common/config",
    relative_path=Path("internal/common/config"),  # Not an artifact!
    ...
)
```

**CORRECT: Model only the executable that uses those packages**
```python
# ✅ CORRECT: Model the executable artifact
api_server = Component(
    name="api-server",
    relative_path=Path("bin/api-server.exe"),  # Actual artifact
    source_files=[
        Path("cmd/api-server/main.go"),
        Path("internal/common/config/config.go"),  # Include as source
        Path("internal/common/logger/logger.go"),   # Include as source
    ],
    ...
)
```

**WRONG: Modeling npm workspace packages as separate Components**
```python
# ❌ WRONG: Don't model workspace packages as Components
auth_lib = Component(
    name="@myorg/auth-lib",
    relative_path=Path("packages/auth-lib"),  # Not an artifact!
    ...
)
```

**CORRECT: Model only the buildable outputs**
```python
# ✅ CORRECT: Model the actual build outputs
# Each npm package that produces a distinct artifact becomes a Component
auth_lib = Component(
    name="auth-lib.dist.js",
    type=ComponentType.STATIC_LIBRARY,  # NOT EXECUTABLE for JS files!
    programming_language="typescript",
    relative_path=Path("libs/auth-lib/dist/index.js"),  # Actual artifact
    source_files=[
        Path("libs/auth-lib/src/index.ts"),  # Only TypeScript sources
        Path("packages/core/src/index.ts"),   # Transitive TypeScript sources
    ],
    depends_on=[core_lib],  # Artifact dependency
    ...
)

web_app = Component(
    name="web-app.bundle.js",
    type=ComponentType.STATIC_LIBRARY,  # Bundle, not EXECUTABLE
    programming_language="typescript",
    relative_path=Path("apps/web-app/dist/bundle.js"),  # Actual artifact
    source_files=[
        Path("apps/web-app/src/index.tsx"),
        Path("libs/auth-lib/src/index.ts"),    # Include as source
        Path("packages/shared-utils/src/index.ts"), # Include as source
        # ❌ Do NOT include: Path("modules/wasm-module/src/lib.rs")  # Wrong language!
    ],
    depends_on=[auth_lib],  # Artifact dependency, not source file
    ...
)
```

### How to Determine if Something is a Component

Ask these three questions:
1. **Does it produce a distinct output file?** (executable, library, bundle)
   - ✅ Yes → It's a Component
   - ❌ No → It's not a Component
2. **Can you point to a specific artifact path?** (e.g., `bin/app.exe`, `dist/bundle.js`)
   - ✅ Yes → It's a Component
   - ❌ No → It's not a Component
3. **Is it a language-level organizational concept?** (package, module, namespace)
   - ✅ Yes → It's NOT a Component (include in `source_files` instead)
   - ❌ No → Continue evaluating

### Example: Go Microservices (Correct Approach)

See `tests/deterministic/go/microservices/create_ground_truth.py` for a complete example.

**Structure:**
```
cmd/
  api-gateway/main.go          → bin/api-gateway.exe (Component)
  auth-service/main.go         → bin/auth-service.exe (Component)
  user-service/main.go         → bin/user-service.exe (Component)
internal/
  common/config/config.go      → Included in source_files
  common/logger/logger.go      → Included in source_files
```

**Modeling:**
- ✅ Model 3 executable Components (one per `bin/*.exe`)
- ✅ Each Component includes ALL transitive source files (`cmd/...`, `internal/...`)
- ✅ Each Component includes ONLY external packages it actually uses
- ❌ Do NOT model `internal/common/config` as a separate Component
- ❌ Do NOT model `internal/common/logger` as a separate Component

**Key Principle:** Internal packages that compile into executables should be included as `source_files`, not separate Components. Only model what produces distinct output files.

### Example: npm Monorepo (Correct Approach)

See `tests/deterministic/npm/create_ground_truth.py` for a complete example demonstrating npm workspace packages.

**Structure:**
```
packages/
  core/src/index.ts            → packages/core/dist/index.js (Component)
  utils/src/index.ts           → packages/utils/dist/index.js (Component)
libs/
  auth-lib/src/index.ts        → libs/auth-lib/dist/index.js (Component)
apps/
  web-app/src/index.tsx        → apps/web-app/dist/bundle.js (Component)
modules/
  wasm-module/src/lib.rs       → modules/wasm-module/pkg/wasm_module.wasm (Component)
  native-addon/main.go         → modules/native-addon/build/Release/native_addon.node (Component)
```

**Modeling:**
- ✅ Each npm package that produces a distinct artifact (`dist/*.js`, `pkg/*.wasm`, `build/*.node`) becomes a Component
- ✅ Use `STATIC_LIBRARY` for compiled JS bundles, `INTERPRETED` for Node.js services, `SHARED_LIBRARY` for `.node` files
- ✅ Each Component's `source_files` includes only TypeScript/TSX files that compile into it
- ✅ Cross-language dependencies (WASM, native addons) are represented via `depends_on`, NOT in `source_files`
- ❌ Do NOT use `EXECUTABLE` for JavaScript files (use `INTERPRETED` or `STATIC_LIBRARY`)
- ❌ Do NOT include `.rs`, `.go`, or `.py` files in TypeScript components' `source_files`

**Key Principle:** In monorepos, each package that produces a distinct build artifact is a Component. Cross-language dependencies are artifact-to-artifact relationships via `depends_on`, not source file inclusions.

What You Must Provide
---------------------
1. A "real" application (even if simple), not just placeholders:
   - It should build or "do something" when run (e.g., minimal servers, CLIs, or library functions).
   - Keep the design intentionally complex (multiple components, cross‑language edges, deeper dependency chains).
2. A complete test repo under `tests/test_repos/<name>` including build files, minimal sources, and artifacts in the exact paths you model.
3. Ground truth generator mirroring the test repo path under `tests/deterministic/...` (mirror the directory layout under `tests/test_repos/...`), e.g., `tests/test_repos/cmake/metaffi` ↔ `tests/deterministic/cmake/metaffi/create_ground_truth.py`. The generator must:
   - Constructs a `RIG` with accurate Components, dependencies, tests, and external packages.
   - Calls `rig.validate()` and fails fast on errors.
   - Saves SQLite (`<name>_ground_truth.sqlite3`) and canonical JSON (`<name>_ground_truth.json`).
   - Reloads from SQLite and asserts deterministic equality.
   - Computes and asserts the repository complexity is in your intended band.

Authoring Components and Targets
-------------------------------
- Components: buildable artifacts. Set `relative_path` to the produced artifact (binary, shared/static lib, bundle). Set `source_files` to **ALL transitive source files** that produce that artifact (including internal packages, shared modules, etc.). Only artifacts are modeled as Components — language packages/modules should be included in `source_files`, not modeled as separate Components.
- **Component Types**: Use `ComponentType` correctly:
  - `EXECUTABLE`: **Only for binary executables** (`.exe`, `.bin`, native binaries). **NOT for JavaScript files** (`.js`) or interpreted scripts.
  - `INTERPRETED`: For interpreted scripts that are runnable (Node.js services, Python scripts, shell scripts).
  - `STATIC_LIBRARY`: For static libraries (`.a`, `.lib`, compiled `.js` bundles, `.wasm` files).
  - `SHARED_LIBRARY`: For shared libraries (`.so`, `.dll`, `.dylib`, `.node` native addons).
- **Cross-Language Source Files**: `source_files` should **only include files that are compiled/transpiled into that component**. Do NOT include source files from other languages/components:
  - ❌ **WRONG**: Including `modules/wasm-module/src/lib.rs` in a TypeScript component's `source_files`
  - ❌ **WRONG**: Including `modules/native-addon/main.go` in a TypeScript component's `source_files`
  - ✅ **CORRECT**: Cross-language dependencies are represented via `depends_on` relationships to other Components (e.g., `wasm_module`, `native_addon`), not by including their source files.
  - ✅ **CORRECT**: A TypeScript component's `source_files` should only contain `.ts` and `.tsx` files that compile into that component.
- **Path Format**: Always use forward slashes (`/`) in all path strings, even on Windows. Python's `Path` class handles this correctly across platforms.
- Dependencies: use `depends_on` from consumer → provider Components to form the build graph. `depends_on` is **only for artifact-to-artifact dependencies** (e.g., an executable depending on a library). Do not use `depends_on` for internal packages or modules that compile into the same artifact.
- Aggregators: meta targets with no artifact; they group other targets and participate only via dependencies. Do not assign an artifact or source files to an Aggregator. RIG expects this separation.
- Runners: custom targets that execute commands (no artifact) if meaningful for the scenario (not Aggregators).
- External packages: model via `ExternalPackage` and `PackageManager` (e.g., `npm`, `go`, `system`). Include **only external packages actually used** by each Component, not all packages in the dependency tree.
- Evidence: reference authoritative lines (e.g., `CMakeLists.txt:1`, `meson.build:1`, `package.json:1`).

Ground Truth Script Template
---------------------------
- See `tests/deterministic/cmake/metaffi/create_ground_truth.py` for structure. Also see:
  - `tests/deterministic/go/microservices/create_ground_truth.py` for a Go example demonstrating correct Component modeling
  - `tests/deterministic/npm/create_ground_truth.py` for an npm monorepo example with cross-language dependencies
- Typical steps:
  - Create `RIG()`, set `RepositoryInfo` and `BuildSystemInfo`.
  - Define `ExternalPackage` instances.
  - Create Components with stable ordering, wire `depends_on`.
  - Register `TestDefinition`s (name, framework, involved components, test sources).
  - Validate, save SQLite, reload, compare, write JSON.
- **Critical checks before finalizing:**
  - Verify all Component types are correct (no `EXECUTABLE` for JS files)
  - Verify `source_files` only contains files that compile into that component (no cross-language files)
  - Verify all paths use forward slashes (`/`)
  - Verify `depends_on` relationships match actual artifact dependencies

Evaluation Questions
--------------------
- Place 30 questions at `tests/deterministic/<name>/evaluation_questions.json`:
  - 10 easy, 10 medium, 10 hard. Ensure expected answers are exact and verifiable from RIG or files.

### Format Hints and Instructions

**CRITICAL:** Every question MUST include explicit format instructions for LLMs. Format hints guide the LLM to produce answers in the exact structure needed for evaluation.

**Common Format Hints:**
- `"(Provide a list)"` — for questions expecting arrays/lists
- `"(Provide the package name)"` — for single value questions
- `"(Answer yes or no)"` — for boolean questions
- `"(Provide a comma-separated list or space-separated list)"` — for flexible formats
- `"(i.e., ...)"` — for clarifications and examples
- `"(If multiple packages are tied, provide any one of them)"` — for tie-breaking scenarios
- `"(state executable name with extension)"` — for platform-specific artifact names
- `"(use Windows artifact names)"` — for platform-specific formatting
- `"(List the files, or answer 'none' if all are used)"` — for conditional answers

**Why Format Hints Matter:**
- Without format hints, LLMs may answer correctly but in the wrong format (e.g., prose instead of a list)
- Format hints reduce evaluation ambiguity and improve consistency
- They help LLMs understand edge cases (ties, multiple valid answers, conditional responses)

### Expected Answer Formats

The `expected_answer` field must match the format the LLM will produce:

**Single Values:**
- String: `"CMakeHelloWorld"`, `"yes"`, `"no"`
- Number: `2`, `0`, `15`
- Example: `"expected_answer": "CMakeHelloWorld"`

**Lists (Single Format):**
- Array of strings: `["item1", "item2"]`
- Example: `"expected_answer": ["utils.lib"]`

**Lists (Multiple Acceptable Formats):**
- Array of arrays: `[["item1", "item2"], ["item1", "item2"]]` — multiple valid orderings/formats
- Array of strings or arrays: `["github.com/gin-gonic/gin", "gin"]` — multiple valid representations
- Example: `"expected_answer": [["hello_world.exe", "utils.lib"], ["utils.lib", "hello_world.exe"]]`

**Yes/No Questions:**
- String: `"yes"` or `"no"`
- Example: `"expected_answer": "yes"`

**Numeric Ranges (for ambiguous counts):**
- Array of numbers: `[15, 16]` — acceptable range
- Example: `"expected_answer": [15, 16]` for line counts that may vary

**Conditional Answers:**
- Array with multiple valid responses: `[["main.h"], ["none"]]`
- Example: `"expected_answer": [["main.h"], ["utils.h", "main.h"], ["none"]]`

### Following Patterns from Examples

**Study Successful Examples First:**
- Reference `tests/deterministic/cmake/cmake_hello_world/evaluation_questions.json` for proven patterns
- Review `tests/deterministic/cmake/jni_hello_world/evaluation_questions.json` for multi-language examples
- Examine `tests/deterministic/cmake/metaffi/evaluation_questions.json` for complex scenarios

**Key Patterns to Follow:**
1. **Consistent format hints** — use the same phrasing for similar question types
2. **Platform-specific artifacts** — specify platform when asking about artifact names (e.g., "on Windows")
3. **Clear question structure** — one question per concept, unambiguous wording
4. **Appropriate difficulty** — match question complexity to difficulty level
5. **Verifiable answers** — every answer must be checkable against RIG or files

### Question Clarity Best Practices

**Unambiguous Wording:**
- ✅ "What source files are used to build the hello_world component? (Provide a list)"
- ❌ "What files does hello_world use?" (unclear: source files? headers? dependencies?)

**Handle Edge Cases Explicitly:**
- ✅ "What source files (if any) in src/ are not used by any component? (List the files, or answer 'none' if all are used)"
- ❌ "What source files are unused?" (unclear what to return if none)

**Clarify Potentially Confusing Concepts:**
- ✅ "How many components have zero dependencies?" (clear: direct dependencies)
- ✅ "In what order must the components be built to satisfy all dependencies on Windows? (Provide the build order as a list starting with no external dependencies, use Windows artifact names)" (explicit about platform and format)

**Tie-Breaking Instructions:**
- ✅ "If multiple packages are tied, provide any one of them"
- ✅ "If there are multiple valid answers, provide any one"

### Difficulty Definitions

- **EASY** (agent gets 80–90% correct even WITHOUT RIG):
  - Questions answerable by simple file inspection
  - Examples with format hints:
    - `"What is the CMake project name?"` → `"expected_answer": "CMakeHelloWorld"`
    - `"How many .cpp files are in src/?"` → `"expected_answer": 2`
    - `"Is enable_testing() called in this project? (Answer yes or no)"` → `"expected_answer": "yes"`
  - RIG benefit: Minimal, maybe just convenience

- **MEDIUM** (agent gets 40–60% without RIG, 80–90% WITH RIG):
  - Questions where parsing build syntax is challenging BUT RIG provides structured answer
  - This is where RIG shows maximum value
  - Examples with format hints:
    - `"What source files are used to build the hello_world component? (Provide a list)"` → `"expected_answer": ["src/main.cpp"]`
    - `"List all components that hello_world depends on (use Windows artifact names)."` → `"expected_answer": ["utils.lib"]`
    - `"What are the names of all output artifacts produced by this build on Windows? (Provide a list)"` → `"expected_answer": [["hello_world.exe", "utils.lib"]]`
  - RIG benefit: HUGE — turns hard parsing into direct lookup

- **HARD** (agent gets 20–40% without RIG, 60–80% WITH RIG):
  - Questions requiring reasoning/inference even with RIG
  - Examples with format hints:
    - `"In what order must the components be built to satisfy all dependencies on Windows? (Provide the build order as a list starting with no external dependencies, use Windows artifact names)"` → `"expected_answer": ["utils.lib", "hello_world.exe"]`
    - `"If the utils component fails to build, which other components would also fail on Windows? (Provide a list, use Windows artifact names)"` → `"expected_answer": ["hello_world.exe"]`
    - `"Can both components be built in parallel? (Answer yes or no)"` → `"expected_answer": "no"`
  - RIG benefit: Helps but still requires reasoning

### JSON Structure Example

```json
{
  "repository_name": "cmake_hello_world",
  "build_system": "cmake",
  "description": "Evaluation questions for cmake_hello_world repository",
  "questions": [
    {
      "id": 1,
      "name": "project_name",
      "category": "build_system",
      "question": "What is the CMake project name?",
      "expected_answer": "CMakeHelloWorld",
      "difficulty": "easy"
    },
    {
      "id": 12,
      "name": "output_artifacts",
      "category": "component_identification",
      "question": "What are the names of all output artifacts produced by this build on Windows? (Provide a list)",
      "expected_answer": [["hello_world.exe", "utils.lib"]],
      "difficulty": "medium"
    },
    {
      "id": 21,
      "name": "build_order",
      "category": "dependency_analysis",
      "question": "In what order must the components be built to satisfy all dependencies on Windows? (Provide the build order as a list starting with no external dependencies, use Windows artifact names)",
      "expected_answer": ["utils.lib", "hello_world.exe"],
      "difficulty": "hard"
    }
  ],
  "ground_truth_file": "tests/deterministic/cmake/cmake_hello_world/ground_truth_summary.json"
}
```

**Key Points:**
- Each question has `id`, `name`, `category`, `question`, `expected_answer`, and `difficulty`
- Format hints are embedded in the `question` text (parentheses)
- `expected_answer` format matches the question type (string, number, array, array of arrays)
- Reference successful examples for consistent patterns

Repository Complexity
---------------------
- Calculation lives in `tests/deterministic/summary_analysis/complexity.py` with weights in `tests/deterministic/summary_analysis/config.py`.
- Metrics computed from ground truth JSON:
  - component_count
  - programming_language_count and programming_languages
  - external_package_count
  - test_count
  - max_dependency_depth (longest path via dependencies)
  - aggregator_count (interpreted components with >1 dependency)
  - has_cross_language_dependencies (boolean)
- Raw score formula (using config weights):
  - `component * Wc + language * Wl + package * Wp + depth * Wd + aggregator * Wa + (cross_lang_bonus if any)`
- Normalization: divide the raw score by the highest raw complexity among the analyzed repositories and multiply by 100 to get a 0–100 score. The current maximum used for normalization is documented in `tests/deterministic/analysis_images/analysis.md` under "Complexity Score Calculations".

Fast‑Fail and Determinism
-------------------------
- Always fail fast on validation errors or mismatched reload comparisons.
- Keep artifact paths and dependency ids stable (consistent creation order).
- Ensure your repo builds or runs simple actions so agents can meaningfully interact with it.

Checklist
---------
- [ ] Real application behavior (start/build outputs exist)
- [ ] Accurate Components (artifact path, full source_files, deps)
- [ ] Only artifacts are modeled as Components (not language packages/modules)
- [ ] Component types are correct (`EXECUTABLE` only for binaries, `INTERPRETED` for Node.js/Python scripts, `STATIC_LIBRARY` for JS bundles)
- [ ] `source_files` only contains files that compile into that component (no cross-language source files)
- [ ] All transitive source files of the same language included in each Component's `source_files`
- [ ] Cross-language dependencies represented via `depends_on`, not in `source_files`
- [ ] All paths use forward slashes (`/`) consistently
- [ ] Only external packages actually used are included in each Component
- [ ] Tests defined and mapped to components
- [ ] External packages modeled
- [ ] RIG validates and reloads deterministically
- [ ] Complexity within target band (and documented)
- [ ] 30 evaluation questions with verified answers
- [ ] All questions include format hints (e.g., "(Provide a list)", "(Answer yes or no)")
- [ ] Expected answer formats match question types (string, number, array, array of arrays)
- [ ] Questions follow patterns from successful examples (`cmake_hello_world`, `jni_hello_world`, `npm`)
- [ ] Questions are unambiguous and handle edge cases explicitly
