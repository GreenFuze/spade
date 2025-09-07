# SPADE - Build System Analysis Tool

SPADE is a tool for analyzing build systems and extracting canonical representations of build configurations, components, and dependencies.

## Overview

The `CMakeEntrypoint` class provides a comprehensive parser for CMake-based projects that:

1. **Extracts Build Information**: Parses CMake configuration to identify components, tests, and dependencies
2. **Creates Canonical Structure**: Converts CMake-specific information into a generalized, build-system-agnostic format
3. **Supports Multiple Parsing Methods**: Uses CMake file API when available, falls back to direct file parsing
4. **Detects Runtime Environments**: Automatically identifies programming languages and runtime environments

## Architecture

### Core Components

- **`CMakeEntrypoint`**: Main class that orchestrates the parsing and extraction process
- **`schemas.py`**: Pydantic models defining the canonical data structures
- **`main.py`**: CLI entry point for the SPADE tool

### Data Models

The implementation uses Pydantic models to ensure type safety and validation:

- **`Component`**: Represents a build target (executable, library, etc.)
- **`Test`**: Represents test definitions and their dependencies
- **`ExternalPackage`**: Represents external package dependencies
- **`Snippet`**: Provides evidence of where information was found in source files

## Features

### Component Detection

- **Target Types**: Executable, shared library, static library, VM, interpreted
- **Runtime Detection**: JVM, VS-C, VS-CPP, CLANG-C, Go, .NET
- **Language Detection**: C++, C, Python, Java, Go, C#
- **Source File Analysis**: Extracts and normalizes source file paths

### Test Analysis

- **Test Framework Detection**: Identifies CTest, doctest, and other frameworks
- **Dependency Mapping**: Maps tests to their dependent components
- **Source File Tracking**: Tracks all source files used in test builds

### External Package Management

- **Package Manager Support**: vcpkg, conan, and other package managers
- **Dependency Resolution**: Identifies external package dependencies
- **Version Information**: Extracts package version and configuration details

## Usage

### Basic Usage

```python
from pathlib import Path
from cmake_entrypoint import CMakeEntrypoint

# Create entrypoint for a CMake project
cmake_dir = Path("path/to/cmake-build-debug")
entrypoint = CMakeEntrypoint(cmake_dir)

# Access extracted information
repo_root = entrypoint.get_repo_root()
components = entrypoint.get_components()
tests = entrypoint.get_tests()
project_name = entrypoint.get_project_name()

# Get build commands
configure_cmd = entrypoint.get_configure_command()
build_cmd = entrypoint.get_build_command()
test_cmd = entrypoint.get_test_command()
```

### Advanced Usage

```python
# Access specific component information
for component in entrypoint.get_components():
    print(f"Component: {component.name}")
    print(f"  Type: {component.type}")
    print(f"  Runtime: {component.runtime}")
    print(f"  Language: {component.programming_language}")
    print(f"  Source files: {len(component.source_files)}")
    print(f"  Dependencies: {len(component.dependent_components)}")
    
    # Access snippet information for evidence
    snippet = component.snippet
    print(f"  Defined in: {snippet.file}:{snippet.start_line}-{snippet.end_line}")

# Access test information
for test in entrypoint.get_tests():
    print(f"Test: {test.name}")
    print(f"  Framework: {test.test_framework}")
    print(f"  Dependencies: {len(test.dependent_components)}")
    print(f"  Testing: {len(test.components_being_tested)} components")
```

## Implementation Details

### Parsing Strategy

The `CMakeEntrypoint` class uses a two-tier parsing approach:

1. **CMake File API**: When available, uses the official CMake file API for structured data extraction
2. **Direct File Parsing**: Falls back to regex-based parsing of CMakeLists.txt files when API is unavailable

### Target Detection

The parser recognizes multiple CMake target definition patterns:

- **Custom Macros**: `c_cpp_exe()`, `c_cpp_shared_lib()` (MetaFFI-specific)
- **Standard CMake**: `add_executable()`, `add_library()`
- **Test Definitions**: `add_test()` calls

### Runtime Detection

Runtime environments are detected using multiple heuristics:

- **Target Names**: Pattern matching on target names (e.g., "go_api_test" → Go runtime)
- **Source Files**: File extension analysis (.go → Go, .java → JVM, .py → Python)
- **Build Context**: Analysis of build configuration and dependencies

### Source File Handling

Source files are processed to ensure consistency:

- **Path Normalization**: Converts absolute paths to repository-relative paths
- **Extension Analysis**: Determines primary programming language from file extensions
- **Dependency Tracking**: Maps source files to their build targets

## Error Handling

The implementation follows a fail-fast philosophy:

- **Immediate Failure**: Unexpected conditions result in immediate exceptions
- **Clear Error Messages**: Detailed error context for debugging
- **Graceful Degradation**: Falls back to alternative parsing methods when possible
- **Validation**: Pydantic models ensure data integrity and provide clear validation errors

## Testing

The implementation has been tested with the MetaFFI project and successfully extracts:

- **9 Components**: Including executables, shared libraries, and various runtime environments
- **15 Tests**: Covering multiple test frameworks and configurations
- **Runtime Detection**: Correctly identifies Go, JVM, Python, and C++ runtimes
- **Language Detection**: Accurately determines programming languages from source files

## Future Enhancements

### Planned Features

- **Dependency Resolution**: Automatic mapping of component dependencies
- **Build Graph Generation**: Create dependency graphs for build optimization
- **Package Version Analysis**: Extract and validate package version requirements
- **Cross-Platform Support**: Enhanced support for different operating systems

### Extensibility

The architecture is designed for easy extension:

- **New Build Systems**: Framework can be extended to support other build systems
- **Additional Runtimes**: Runtime detection can be enhanced for new environments
- **Custom Parsers**: Plugin architecture for custom parsing logic
- **Output Formats**: Support for multiple output formats (JSON, YAML, GraphML)

## Requirements

- **Python 3.12+**: For type hints and modern language features
- **Pydantic**: For data validation and serialization
- **Pathlib**: For cross-platform path handling

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd spade

# Install dependencies
pip install pydantic

# Run the tool
python main.py
```

## Contributing

Contributions are welcome! Please ensure:

- **Type Safety**: All code includes proper type annotations
- **Error Handling**: Follows the fail-fast philosophy
- **Testing**: Include tests for new functionality
- **Documentation**: Update documentation for new features

## License

This project is licensed under the terms specified in the LICENSE.md file.
