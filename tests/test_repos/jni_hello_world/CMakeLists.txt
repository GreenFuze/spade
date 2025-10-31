cmake_minimum_required(VERSION 3.16)

project(JNIHelloWorld 
    VERSION 1.0.0
    DESCRIPTION "JNI Hello World - C++ executable calling Java JAR"
    LANGUAGES CXX Java
)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Enable CMake File API
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

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

# Function to build JAR using custom commands (for comparison with add_jar)
function(add_custom_jar TARGET_NAME JAR_NAME VERSION)
    set(SOURCES ${ARGN})
    set(OUTPUT_DIR ${CMAKE_CURRENT_BINARY_DIR}/classes_${TARGET_NAME})
    set(JAR_FILE ${CMAKE_CURRENT_BINARY_DIR}/${JAR_NAME}-${VERSION}.jar)

    # Compile each Java source to .class file
    set(CLASS_FILES "")
    foreach(SOURCE ${SOURCES})
        get_filename_component(CLASS_NAME ${SOURCE} NAME_WE)
        set(CLASS_FILE ${OUTPUT_DIR}/${CLASS_NAME}.class)
        list(APPEND CLASS_FILES ${CLASS_FILE})

        add_custom_command(
            OUTPUT ${CLASS_FILE}
            COMMAND ${CMAKE_COMMAND} -E make_directory ${OUTPUT_DIR}
            COMMAND ${Java_JAVAC_EXECUTABLE} -d ${OUTPUT_DIR}
                    ${CMAKE_CURRENT_SOURCE_DIR}/${SOURCE}
            DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/${SOURCE}
            COMMENT "Compiling ${SOURCE} to ${CLASS_NAME}.class"
        )
    endforeach()

    # Package .class files into JAR
    add_custom_command(
        OUTPUT ${JAR_FILE}
        COMMAND ${Java_JAR_EXECUTABLE} cf ${JAR_FILE} -C ${OUTPUT_DIR} .
        DEPENDS ${CLASS_FILES}
        COMMENT "Creating ${JAR_NAME}-${VERSION}.jar"
    )

    # Create target that depends on JAR
    add_custom_target(${TARGET_NAME} ALL
        DEPENDS ${JAR_FILE}
    )
endfunction()

# Build math_lib JAR using custom commands
add_custom_jar(math_lib math_lib 1.0.0
    src/java/MathUtils.java
)

# Function to build Go shared library using go build -buildmode=c-shared
function(add_go_shared_library TARGET_NAME OUTPUT_NAME)
    set(SOURCES ${ARGN})
    set(OUTPUT_FILE ${CMAKE_CURRENT_BINARY_DIR}/${OUTPUT_NAME}.dll)

    # Build Go module as C-shared library
    add_custom_command(
        OUTPUT ${OUTPUT_FILE}
        COMMAND go build -buildmode=c-shared -o ${OUTPUT_FILE} ${CMAKE_CURRENT_SOURCE_DIR}/${SOURCES}
        DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/${SOURCES}
        COMMENT "Building Go shared library ${OUTPUT_NAME}.dll"
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    )

    # Create target that depends on DLL
    add_custom_target(${TARGET_NAME} ALL
        DEPENDS ${OUTPUT_FILE}
    )
endfunction()

# Build Go shared library
add_go_shared_library(hello_go_lib libhello
    src/go/hello.go
)

# Link JNI to C++ executable
target_link_libraries(jni_hello_world
    ${JNI_LIBRARIES}
)

# Include JNI headers
target_include_directories(jni_hello_world PRIVATE
    ${JNI_INCLUDE_DIRS}
)

# Set Java classpath for C++ executable (include both JARs)
set_target_properties(jni_hello_world PROPERTIES
    VS_DEBUGGER_ENVIRONMENT "CLASSPATH=${CMAKE_CURRENT_BINARY_DIR}/java_hello_lib.jar;${CMAKE_CURRENT_BINARY_DIR}/math_lib-1.0.0.jar"
)

# Add dependency on Go shared library
add_dependencies(jni_hello_world hello_go_lib)

# Copy Go DLL to executable directory so it can be loaded at runtime
add_custom_command(TARGET jni_hello_world POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        ${CMAKE_CURRENT_BINARY_DIR}/libhello.dll
        $<TARGET_FILE_DIR:jni_hello_world>/libhello.dll
    COMMENT "Copying libhello.dll to executable directory"
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

