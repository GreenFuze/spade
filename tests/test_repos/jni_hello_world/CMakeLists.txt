cmake_minimum_required(VERSION 3.16)

project(JNIHelloWorld 
    VERSION 1.0.0
    DESCRIPTION "JNI Hello World - C++ executable calling Java JAR"
    LANGUAGES CXX Java
)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(JNI REQUIRED)
find_package(Java REQUIRED)

# Set Java version to match system
set(CMAKE_JAVA_COMPILE_FLAGS "-source" "21" "-target" "21")

# Include Java support
include(UseJava)

# Enable testing
enable_testing()

# Add C++ executable
add_executable(jni_hello_world
    src/cpp/main.cpp
    src/cpp/jni_wrapper.cpp
)

# Add Java JAR library
add_jar(java_hello_lib
    SOURCES 
        src/java/HelloWorld.java
        src/java/HelloWorldJNI.java
    VERSION ${PROJECT_VERSION}
    ENTRY_POINT HelloWorld
)

# Link JNI to C++ executable
target_link_libraries(jni_hello_world
    ${JNI_LIBRARIES}
)

# Include JNI headers
target_include_directories(jni_hello_world PRIVATE
    ${JNI_INCLUDE_DIRS}
)

# Set Java classpath for C++ executable
set_target_properties(jni_hello_world PROPERTIES
    VS_DEBUGGER_ENVIRONMENT "CLASSPATH=${CMAKE_CURRENT_BINARY_DIR}/java_hello_lib.jar"
)

# Add C++ tests (doctest)
add_executable(test_jni_wrapper
    tests/cpp/test_jni_wrapper.cpp
    src/cpp/jni_wrapper.cpp
)

target_link_libraries(test_jni_wrapper
    ${JNI_LIBRARIES}
)

target_include_directories(test_jni_wrapper PRIVATE
    ${JNI_INCLUDE_DIRS}
    src/cpp
)

# Register tests
add_test(NAME test_jni_wrapper_cpp COMMAND test_jni_wrapper)

# Set test properties
set_tests_properties(test_jni_wrapper_cpp PROPERTIES
    LABELS "cpp;doctest;jni"
)
