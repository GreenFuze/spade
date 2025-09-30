# MetaFFI Architecture (manual ground truth)

## terminology
$METAFFI_HOME - environment variable of MetaFFI output directory.
This is where MetaFFI application is built to.

## Build system structure from "main" MetaFFI aggregator
MetaFFI aggregator.
Contains:
- metaffi-core aggregator - defined in metaffi-core/:
  - xllr - defined in metaffi-core/XLLR/:
    - kind: C++ dynamic library
    - packages: Boost.filesystem, Boost.thread 
    - actions in metaffi-core/XLLR/:
      - copy of several .c files and .h files to $METAFFI_HOME
  - metaffi - defined in metaffi-core/CLI/:
    - kind: C++ executable
    - packages: Boost.filesystem, Boost.program_options
  - cdts_test - defined in metaffi-core/plugin-sdk/:
    - kind: C++ executable
    - CTest unit-test
    - packages: Boost.filesystem, doctest
  - xllr_capi_test - defined in metaffi-core/plugin-sdk/:
    - kind: C++ executable
    - CTest unit-test
    - packages: Boost.filesystem, doctest
    
- python311 aggregator - defined in lang-plugin-python311/:
  - xllr.python311 - defined in lang-plugin-python311/runtime/:
    - kind C++ dynamic library
    - packages: Boost.filesystem
  - python_runtime_test - defined in lang-plugin-python311/runtime/:
    - kind: C++ executable
    - CTest unit-test
    - packages: Boost.filesystem, doctest
    - depends on: xllr.python311
  - metaffi.idl.python311 - defined in lang-plugin-python311/idl/:
    - kind: C++ dynamic library
    - packages: Boost.filesystem
  - python311_idl_plugin_test - defined in lang-plugin-python311/idl/:
    - kind: "C++ executable"
    - CTest unit-test
    - packages: Boost.filesystem, doctest
    - depends on: metaffi.idl.python311
  - metaffi.compiler.python311 - defined in lang-plugin-python311/compiler/:
    - kind: Go dynamic library
    

- openjdk aggregator - defined in lang-plugin-openjdk/:
  - xllr.openjdk - defined in lang-plugin-openjdk/runtime/:
    - kind: C++ dynamic library
    - packages: Boost.filesystem, JNI
  - xllr.openjdk.jni.bridge - defined in lang-plugin-openjdk/xllr-openjdk-bridge/:
    - kind: C++ dynamic library
    - packages: Boost.filesystem, JNI
    - depends on: xllr.openjdk
  - xllr.openjdk.bridge - defined in lang-plugin-openjdk/xllr-openjdk-bridge/:
    - kind: JVM jar
    - depends on: xllr.openjdk.jni.bridge
  - metaffi.api - defined in lang-plugin-openjdk/api/:
    - kind: JVM jar
    - depends on: xllr.openjdk.bridge
  - openjdk_api_test - defined in lang-plugin-openjdk/runtime/:
    - kind: C++ executable
    - CTest unit-test
    - packages: Boost.filesystem, doctest, JNI
    - depends on: xllr.openjdk
  - cdts_java_test - defined in lang-plugin-openjdk/runtime/:
    - kind: C++ executable
    - CTest unit-test
    - packages: Boost.filesystem, doctest, JNI
    - depends on: xllr.openjdk
  - metaffi.idl.openjdk - defined in lang-plugin-openjdk/idl/:
    - kind: C++ dynamic library
    - packages: JNI
  - metaffi.compiler.openjdk - defined in lang-plugin-openjdk/compiler/:
    - kind: Go dynamic library

- go aggregator - defined in lang-plugin-go/
  - xllr.go - defined in lang-plugin-go/runtime/:
    - kind: C++ dynamic library
    - packages: Boost.filesystem
  - metaffi.compiler.go - defined in lang-plugin-go/compiler/:
    - kind: Go dynamic library
  - metaffi.idl.go - defined in lang-plugin-go/idl/:
    - kind: Go dynamic library
  - go_api_test - defined in lang-plugin-go/api/:
    - kind: C++ executable
    - CTest unit-test
    - packages: doctest; Boost.filesystem
    - depends on: xllr.go, build_go_guest

## Targets not derived from MetaFFI aggregator
The following are targets that are not tied directly to the "main" aggregator (MetaFFI), but targets that either executed directly, or CTests:
- python3_api_unitest - defined in lang-plugin-python311/api/:
  - CTest target that runs python3 unittest on lang-plugin-python311/api/unittest/test_python311_api.py
- python3_api_cross_pl_tests - defined in lang-plugin-python311/api/:
  - CTest runner that runs python3 script lang-plugin-python311/api/tests/run_api_tests.py
- python311.publish - defined in lang-plugin-python311/api/:
  - Runs using python3 the script "publish_python_package.py" which publishes a package to pypi
  - Depends on xllr.python311
- metaffi_compiler_python311_test - defined in lang-plugin-python311/compiler/:
  - Go Test unit test runner executed by CTest
- openjdk_api_cross_pl_tests - defined in lang-plugin-openjdk/api/:
  - CTest runner that runs python3 script lang-plugin-openjdk/api/tests/run_api_tests.py
- openjdk_idl_extractor - defined in lang-plugin-openjdk/idl/
  - kind: JVM jar
  - packages: libs/gson-2.10.1.jar, libs/asm-9.6.jar, libs/asm-tree-9.6.jar, libs/javaparser-core-3.24.4.jar
- test_data_classes: - defined in lang-plugin-openjdk/idl/:
  - kind: JVM classes
- java_tests_classes - defined in lang-plugin-openjdk/idl/:
  - kind: JVM classes
- java_tests_run - defined in lang-plugin-openjdk/idl/:
  - JUnitCore unit test runner
- openjdk_idl_plugin_java_tests - defined in plugin-openjdk/idl/:
  - JUnitCore unit test runner executed by CTest
  - depends on: java_tests_run
- actions in plugin-openjdk/idl/:
  - copies JAR files to plugin-openjdk/idl/lib/
  - Post build to metaffi.idl.openjdk - copies plugin-openjdk/idl/src/java_extractor/ to CMake binary dir "/src/java_extractor"
- openjdk_compiler_go_tests - defined in lang-plugin-openjdk/compiler/:
  - Go Test unit test runner executed by CTest
- build_go_guest - defined in lang-plugin-openjdk/runtime/:
  - Runner executing python3 script lang-plugin-openjdk/runtime/test/build_guest.py
- metaffi_compiler_go_test - defined in lang-plugin-go/compiler/:
  - Go Test unit test runner executed by CTest
- metaffi_idl_go_test - defined in lang-plugin-go/idl/:
  - Go Test unit test runner executed by CTest
- go_runtime_test - defined in lang-plugin-go/go-runtime/:
  - Go Test unit test runner executed by CTest

## Targets that should not be detected as they are commented out from the root CMakeLists.txt
The following subdirectories are commented out (on purpose) and are not being built:
- lang-plugin-c/ - C plugin support, work in progress
- metaffi-installer/ directory - build installers
If components inside are detected, this is not hallucinations, but the LLM didn't understand they are not being built.

## Directories without any build information
The following subdirectories are not part of the build. they hold artifacts.
- containers/ - hold docker files
- cmake-build-*/ - cmake build directories
- cmake/ - contains CMake scripts
- output/ - output directory of the MetaFFI
- metaffi.github.io/ - Github pages directory
