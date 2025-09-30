# JNI Hello World

A multi-language CMake project demonstrating JNI (Java Native Interface) integration between C++ and Java components.

## Project Structure

```
jni_hello_world/
├── CMakeLists.txt              # Root CMake configuration
├── src/
│   ├── cpp/                    # C++ source files
│   │   ├── main.cpp           # Main C++ executable
│   │   ├── jni_wrapper.h      # JNI wrapper header
│   │   └── jni_wrapper.cpp    # JNI wrapper implementation
│   └── java/                   # Java source files
│       ├── HelloWorld.java     # Main Java class
│       └── HelloWorldJNI.java  # JNI helper class
└── tests/
    ├── cpp/                    # C++ tests (doctest)
    │   └── test_jni_wrapper.cpp
    └── java/                   # Java tests (JUnit)
        └── HelloWorldTest.java
```

## Components

### C++ Components
- **`jni_hello_world`** - Main executable that loads Java JAR and calls Java methods via JNI
- **`test_jni_wrapper`** - C++ test executable using doctest framework

### Java Components
- **`java_hello_lib.jar`** - Java library containing HelloWorld and HelloWorldJNI classes
- **`java_tests.jar`** - Java test library using JUnit framework

## Dependencies

- **JNI** - Java Native Interface for C++/Java integration
- **Java** - Java runtime and development tools
- **doctest** - C++ testing framework
- **JUnit** - Java testing framework

## Build Instructions

```bash
mkdir build
cd build
cmake ..
cmake --build .
```

## Test Execution

```bash
# Run C++ tests
./test_jni_wrapper

# Run Java tests
java -cp java_hello_lib.jar:java_tests.jar org.junit.runner.JUnitCore HelloWorldTest

# Run all tests via CTest
ctest
```

## Expected LLM Analysis

The LLM-based RIG generator should identify:

1. **Build System**: CMake 3.16+
2. **Languages**: C++ (C++17), Java
3. **Components**:
   - `jni_hello_world` (executable, C++, depends on JNI)
   - `java_hello_lib` (JAR library, Java)
   - `test_jni_wrapper` (executable, C++, test)
   - `java_tests` (JAR library, Java, test)
4. **Test Frameworks**: doctest (C++), JUnit (Java)
5. **Dependencies**: JNI, Java runtime
6. **Relationships**: C++ executable calls Java JAR methods via JNI
