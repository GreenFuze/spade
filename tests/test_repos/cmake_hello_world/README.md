# CMake Hello World Test Repository

This is a simple CMake test repository used for testing the LLM-based RIG generation system.

## Structure

```
cmake_hello_world/
├── CMakeLists.txt          # Main CMake configuration
├── src/
│   ├── main.cpp           # Main executable source
│   ├── utils.cpp          # Utility library source
│   └── utils.h            # Utility library header
└── README.md              # This file
```

## Components

- **hello_world** - Executable that prints "Hello, World!" and calls utility function
- **utils** - Static library with a simple utility function
- **test_hello_world** - CTest test that runs the hello_world executable

## Build Instructions

```bash
# Configure
cmake -B build -S .

# Build
cmake --build build

# Test
ctest --test-dir build
```

## Expected Output

When built and run, the hello_world executable should output:
```
Hello, World!
Utils library working!
```

## Usage in Testing

This repository is used by `test_llm0_discovery.py` to test the Repository Discovery Agent's ability to:

1. Detect CMake build system
2. Identify build targets (hello_world, utils)
3. Extract source files and dependencies
4. Discover test configurations
5. Create evidence catalog with proper file references
