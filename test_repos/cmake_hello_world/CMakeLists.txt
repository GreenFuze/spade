cmake_minimum_required(VERSION 3.10)
project(TestProject)

# Add executable
add_executable(hello_world src/main.cpp)

# Add library
add_library(utils src/utils.cpp)

# Link library to executable
target_link_libraries(hello_world utils)

# Add test
enable_testing()
add_test(NAME test_hello_world COMMAND hello_world)
