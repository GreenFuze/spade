# SPADE Project Knowledge Base

## Project Overview
SPADE (SPAwn Detector) is a project designed to analyze build systems and extract canonical representations of build information. The project uses Pydantic models to create standardized data structures that can represent various build systems in a unified format.

## Project Structure
```
spade/
├── main.py                 # Main entry point
├── schemas.py             # Pydantic data models
├── cmake_entrypoint.py    # CMake build system parser
├── test_cmake_entrypoint.py # Comprehensive test suite
├── requirements.txt       # Python dependencies
├── pyrightconfig.json    # Type checking configuration
├── .vscode/launch.json   # VS Code debug configurations
└── README.md             # Project documentation
```

## Core Components

### 1. Data Models (schemas.py)
The project defines several Pydantic models to represent build system entities:

- **Component**: Represents build targets with attributes like name, type, runtime, programming language, source files, dependencies, and external packages
- **Test**: Represents test targets with framework detection, dependencies, and source files
- **ExternalPackage**: Represents external dependencies with package manager information
- **PackageManager**: Represents package managers like vcpkg, Conan, etc.
- **Snippet**: Represents evidence of where components/tests were defined (file, line numbers)
- **ComponentType**: Enum for component types (executable, shared library, static library, VM, interpreted)
- **Runtime**: Enum for runtime environments (JVM, VS-C, VS-CPP, CLANG-C, Go, .NET)

### 2. CMakeEntrypoint Class (cmake_entrypoint.py)
The `CMakeEntrypoint` class is the core component for parsing CMake projects using the `cmake-file-api` package.

#### Key Features:
- **Repository Root Detection**: Automatically finds the repository root by traversing up from the CMake configuration directory
- **CMake File API Integration**: Uses the `cmake-file-api` package exclusively (no custom parsing)
- **Comprehensive Data Extraction**: Extracts information from multiple API replies:
  - `codemodel v2`: Build graph, targets, dependencies
  - `cache v2`: CMake cache variables
  - `toolchains v1`: Compiler information
  - `cmakeFiles v1`: CMake file dependencies
- **CTest Integration**: Uses `ctest --show-only=json-v1` for test information
- **Runtime Detection**: Implements documented heuristics for detecting JVM, Go, .NET, and C++ runtimes
- **Package Manager Detection**: Identifies vcpkg, Conan, and other package managers from link fragments
- **Line Number Resolution**: Resolves backtrace indices to actual file paths and line numbers

#### Constructor Options:
- `parse_cmake=True` (default): Automatically parse CMake configuration during initialization
- `parse_cmake=False`: Only detect repository root, defer CMake parsing until `parse_cmake()` is called

#### Methods:
- **Getter Methods**: `get_repo_root()`, `get_components()`, `get_tests()`, etc.
- **Manual Parsing**: `parse_cmake()` to trigger CMake parsing after initialization
- **Error Handling**: Graceful handling of CMake configuration failures

### 3. Testing (test_cmake_entrypoint.py)
Comprehensive pytest test suite with:

- **Unit Tests**: Repository root detection, error handling
- **Integration Tests**: MetaFFI project parsing (marked with `@pytest.mark.integration`)
- **Test Categories**: Component extraction, test detection, dependency analysis
- **Error Handling**: Tests for invalid configurations and graceful failures
- **MetaFFI Integration**: Tests using actual MetaFFI project (skipped if CMake configuration fails)

## Technical Implementation Details

### CMake File API Usage
The implementation follows the documented recipes from `cmake_files_api.md`:

1. **External Package Dependencies**: Extracted from `target["link"]["commandFragments[]]` with role-based filtering
2. **Test Framework Detection**: Uses CTest JSON properties, labels, and command analysis
3. **Line Number Extraction**: Resolves `backtrace` indices via `backtraceGraph` nodes and files
4. **Output Paths**: Uses `target["artifacts"][]` for accurate artifact locations
5. **Programming Languages**: Reads from `target["compileGroups"][*]["language"]`
6. **Runtime Detection**: Implements documented heuristics for JVM, Go, and .NET detection

### Error Handling Philosophy
- **Fail-Fast**: Immediate failure with clear error messages
- **Graceful Degradation**: CTest failures don't crash the entire parsing
- **User Guidance**: Clear error messages with context information
- **No Silent Failures**: System never continues in invalid state

### Type Safety
- **Pydantic Models**: All data structures use Pydantic for validation
- **Type Annotations**: Comprehensive type hints throughout
- **Strict Typing**: No type casting, explicit type definitions

## Build System Integration

### MetaFFI Project
The project includes integration tests with the MetaFFI project:
- **Location**: `C:\src\github.com\MetaFFI`
- **Build Directory**: `C:\src\github.com\MetaFFI\cmake-build-debug`
- **Known Issues**: CMake configuration has environment variable parsing issues (not related to SPADE)
- **Test Strategy**: Tests skip gracefully when CMake configuration fails

### CMake Configuration Workflow
1. **Configure**: `cmake -S . -B build`
2. **Build Tests**: `cmake --build build --target <test_targets>` (for reliable CTest JSON)
3. **Parse**: Use `CMakeEntrypoint` to extract information
4. **CTest**: Run `ctest --show-only=json-v1` for complete test information

## Development Workflow

### VS Code Integration
- **Debug Configurations**: Multiple pytest configurations in `.vscode/launch.json`
- **Integration Tests**: Separate debug configuration for integration tests only
- **Build Detector Tests**: Configuration for existing build detector tests

### Testing Strategy
- **Unit Tests**: Fast, isolated tests for core functionality
- **Integration Tests**: Real-world testing with MetaFFI project
- **Error Scenarios**: Comprehensive error handling validation
- **Type Safety**: Pyright integration for static type checking

## Dependencies

### Python Packages
- `pydantic>=2.0.0`: Data validation and serialization
- `cmake-file-api`: CMake File API integration
- `pytest`: Testing framework

### System Requirements
- **CMake**: 3.20+ for File API support
- **Python**: 3.8+ for type hints and modern features
- **Build Tools**: Appropriate compilers for target platforms

## Recent Changes and Bug Fixes

### CMakeEntrypoint Class Rewrite (Latest)
- **Complete Rewrite**: Replaced all custom parsing with proper cmake-file-api usage
- **API Integration**: Implemented documented recipes for all data extraction
- **Runtime Detection**: Added documented heuristics for JVM, Go, .NET detection
- **Package Manager Detection**: Integrated vcpkg and Conan detection
- **Line Number Resolution**: Implemented backtrace resolution for accurate snippets
- **Error Handling**: Added graceful handling of CMake configuration failures
- **Constructor Flexibility**: Added `parse_cmake` parameter for deferred parsing

### Test Suite Improvements
- **Error Handling Tests**: Fixed test expectations for proper error types
- **Repository Root Tests**: Separated CMake parsing from root detection
- **Integration Test Skipping**: Graceful handling of MetaFFI CMake issues
- **Test Coverage**: Comprehensive coverage of all class functionality

### Type Safety Improvements
- **Pydantic Integration**: All data structures use Pydantic models
- **Type Annotations**: Comprehensive type hints throughout
- **Pyright Configuration**: Proper type checking setup

## Future Enhancements

### Planned Features
1. **Additional Build Systems**: Support for other build systems beyond CMake
2. **Enhanced Runtime Detection**: More sophisticated runtime environment detection
3. **Package Manager Integration**: Deeper integration with package managers
4. **Performance Optimization**: Caching and incremental parsing
5. **Cross-Platform Support**: Enhanced Windows/Linux/macOS compatibility

### Technical Debt
1. **Backtrace Resolution**: Enhance line number extraction accuracy
2. **Test Framework Detection**: Improve test framework identification
3. **External Package Parsing**: More sophisticated package dependency analysis
4. **Error Recovery**: Enhanced error recovery mechanisms

## Known Issues and Limitations

### MetaFFI Project
- **CMake Configuration**: Environment variable parsing issues in `cmake/Environment.cmake`
- **Impact**: Prevents full integration testing
- **Workaround**: Tests skip gracefully, functionality validated through unit tests

### CMake File API
- **Test Commands**: `ctest --show-only=json-v1` requires built targets for reliable `command[]`
- **Discovery Frameworks**: GoogleTest and Catch2 need post-build discovery
- **Workaround**: Build test targets before running CTest JSON extraction

## Contributing Guidelines

### Code Quality Standards
- **Fail-Fast Philosophy**: Immediate failure with clear error messages
- **Type Safety**: Use Pydantic models and comprehensive type annotations
- **Error Handling**: Proper exception handling with context information
- **Testing**: Comprehensive test coverage for all functionality
- **Documentation**: Clear docstrings and inline comments

### Development Process
1. **Feature Development**: Implement with comprehensive testing
2. **Code Review**: Ensure adherence to coding standards
3. **Integration Testing**: Validate with real-world projects
4. **Documentation**: Update knowledgebase and README
5. **Type Checking**: Ensure Pyright passes without errors

## References

### Documentation
- `cmake_files_api.md`: Comprehensive CMake File API recipes and examples
- `README.md`: Project overview and usage instructions
- `requirements.txt`: Python dependency specifications

### External Resources
- [CMake File API Documentation](https://cmake.org/cmake/help/latest/manual/cmake-file-api.7.html)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [CMake Testing Documentation](https://cmake.org/cmake/help/latest/manual/ctest.1.html)
