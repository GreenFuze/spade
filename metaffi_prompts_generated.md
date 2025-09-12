# Repository Build Analysis

## Repository Information
- **Repository**: MetaFFI
- **Root Path**: C:\src\github.com\MetaFFI
- **Build System**: CMake
- **Scope**: ['./']
- **Detection Mode**: configure_only
- **Configure Command**: cmake -B C:\src\github.com\MetaFFI\cmake-build-debug
- **Test Discovery Command**: ctest --test-dir C:\src\github.com\MetaFFI\cmake-build-debug

## Build Data

The following JSON contains the complete build analysis data:

```json
{
  "repo": {
    "name": "MetaFFI",
    "root": "C:\\src\\github.com\\MetaFFI"
  },
  "build": {
    "system": "CMake",
    "generator": null,
    "type": null,
    "configure_cmd": "cmake -B C:\\src\\github.com\\MetaFFI\\cmake-build-debug",
    "test_cmd": "ctest --test-dir C:\\src\\github.com\\MetaFFI\\cmake-build-debug",
    "limits": {
      "max_list": 50
    }
  },
  "components": [
    {
      "id": 0,
      "name": "cdts_test",
      "type": "executable",
      "language": "cxx",
      "runtime": "native",
      "output": "cdts_test.exe",
      "output_path": "cmake-build-debug\\metaffi-core\\cdts_test.exe",
      "source_files": [
        "metaffi-core\\plugin-sdk\\runtime\\cdts_test.cpp",
        "metaffi-core\\plugin-sdk\\runtime\\cdt.cpp",
        "metaffi-core\\plugin-sdk\\runtime\\cdts_traverse_construct.cpp",
        "metaffi-core\\plugin-sdk\\runtime\\cdts_wrapper.cpp",
        "metaffi-core\\plugin-sdk\\runtime\\metaffi_primitives.cpp",
        "metaffi-core\\plugin-sdk\\runtime\\xllr_capi_loader.c",
        "metaffi-core\\plugin-sdk\\runtime\\xllr_static_capi_loader.cpp",
        "metaffi-core\\plugin-sdk\\utils\\entity_path_parser.cpp",
        "metaffi-core\\plugin-sdk\\utils\\expand_env.cpp",
        "metaffi-core\\plugin-sdk\\utils\\library_loader.cpp",
        "metaffi-core\\plugin-sdk\\utils\\xllr_api_wrapper.cpp"
      ],
      "depends_on": [],
      "externals": [
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_filesystem-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_system-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "kernel32.lib user32.lib gdi32.lib winspool.lib shell32.lib ole32.lib oleaut32.lib uuid.lib comdlg32.lib advapi32.lib"
        }
      ],
      "evidence": [
        {
          "call_stack": [
            "cmake/CPP.cmake#L73-L73",
            "metaffi-core/plugin-sdk/run_sdk_tests.cmake#L6-L6",
            "metaffi-core/plugin-sdk/run_sdk_tests.cmake#L1-L1",
            "metaffi-core/CMakeLists.txt#L12-L12",
            "metaffi-core/CMakeLists.txt#L1-L1"
          ]
        }
      ],
      "test_link_id": 1,
      "test_link_name": "cdts_test"
    },
    {
      "id": 1,
      "name": "metaffi",
      "type": "executable",
      "language": "cxx",
      "runtime": "native",
      "output": "metaffi.exe",
      "output_path": "cmake-build-debug\\metaffi-core\\CLI\\metaffi.exe",
      "source_files": [
        "metaffi-core\\CLI\\cli_executor.cpp",
        "metaffi-core\\CLI\\compiler.cpp",
        "metaffi-core\\CLI\\exception_handler.cpp",
        "metaffi-core\\CLI\\idl_extractor.cpp",
        "metaffi-core\\CLI\\idl_plugin_interface_wrapper.cpp",
        "metaffi-core\\CLI\\language_plugin_interface_wrapper.cpp",
        "metaffi-core\\CLI\\main.cpp",
        "metaffi-core\\CLI\\plugin_utils.cpp",
        "metaffi-core\\plugin-sdk\\runtime\\cdt.cpp",
        "metaffi-core\\plugin-sdk\\runtime\\cdts_traverse_construct.cpp",
        "metaffi-core\\plugin-sdk\\runtime\\cdts_wrapper.cpp",
        "metaffi-core\\plugin-sdk\\runtime\\metaffi_primitives.cpp",
        "metaffi-core\\plugin-sdk\\runtime\\xllr_capi_loader.c",
        "metaffi-core\\plugin-sdk\\runtime\\xllr_static_capi_loader.cpp",
        "metaffi-core\\plugin-sdk\\utils\\entity_path_parser.cpp",
        "metaffi-core\\plugin-sdk\\utils\\expand_env.cpp",
        "metaffi-core\\plugin-sdk\\utils\\library_loader.cpp",
        "metaffi-core\\plugin-sdk\\utils\\xllr_api_wrapper.cpp"
      ],
      "depends_on": [],
      "externals": [
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_filesystem-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_program_options-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_system-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_container-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "kernel32.lib user32.lib gdi32.lib winspool.lib shell32.lib ole32.lib oleaut32.lib uuid.lib comdlg32.lib advapi32.lib"
        }
      ],
      "evidence": [
        {
          "call_stack": [
            "cmake/CPP.cmake#L73-L73",
            "metaffi-core/CLI/CMakeLists.txt#L6-L6",
            "metaffi-core/CLI/CMakeLists.txt#L1-L1"
          ]
        }
      ],
      "test_link_id": null,
      "test_link_name": null
    },
    {
      "id": 2,
      "name": "metaffi.compiler.go",
      "type": "shared_library",
      "language": "go",
      "runtime": "Runtime.GO",
      "output": "metaffi.compiler.go.dll",
      "output_path": "output\\windows\\x64\\Debug\\go\\metaffi.compiler.go.dll",
      "source_files": [],
      "depends_on": [],
      "externals": [],
      "evidence": [
        {
          "call_stack": [
            "cmake/Go.cmake#L57-L57",
            "lang-plugin-go/compiler/CMakeLists.txt#L7-L7",
            "lang-plugin-go/compiler/CMakeLists.txt#L1-L1"
          ]
        }
      ],
      "test_link_id": null,
      "test_link_name": null
    },
    {
      "id": 3,
      "name": "metaffi.compiler.openjdk",
      "type": "shared_library",
      "language": "go",
      "runtime": "Runtime.GO",
      "output": "metaffi.compiler.openjdk.dll",
      "output_path": "output\\windows\\x64\\Debug\\openjdk\\metaffi.compiler.openjdk.dll",
      "source_files": [],
      "depends_on": [],
      "externals": [],
      "evidence": [
        {
          "call_stack": [
            "cmake/Go.cmake#L57-L57",
            "lang-plugin-openjdk/compiler/CMakeLists.txt#L4-L4",
            "lang-plugin-openjdk/compiler/CMakeLists.txt#L1-L1"
          ]
        }
      ],
      "test_link_id": null,
      "test_link_name": null
    },
    {
      "id": 4,
      "name": "metaffi.compiler.python311",
      "type": "shared_library",
      "language": "go",
      "runtime": "Runtime.GO",
      "output": "metaffi.compiler.python311.dll",
      "output_path": "output\\windows\\x64\\Debug\\python311\\metaffi.compiler.python311.dll",
      "source_files": [],
      "depends_on": [],
      "externals": [],
      "evidence": [
        {
          "call_stack": [
            "cmake/Go.cmake#L57-L57",
            "lang-plugin-python311/compiler/CMakeLists.txt#L6-L6",
            "lang-plugin-python311/compiler/CMakeLists.txt#L1-L1"
          ]
        }
      ],
      "test_link_id": null,
      "test_link_name": null
    },
    {
      "id": 5,
      "name": "metaffi.idl.go",
      "type": "shared_library",
      "language": "go",
      "runtime": "Runtime.GO",
      "output": "metaffi.idl.go.dll",
      "output_path": "output\\windows\\x64\\Debug\\go\\metaffi.idl.go.dll",
      "source_files": [],
      "depends_on": [],
      "externals": [],
      "evidence": [
        {
          "call_stack": [
            "cmake/Go.cmake#L57-L57",
            "lang-plugin-go/idl/CMakeLists.txt#L3-L3",
            "lang-plugin-go/idl/CMakeLists.txt#L1-L1"
          ]
        }
      ],
      "test_link_id": null,
      "test_link_name": null
    },
    {
      "id": 6,
      "name": "metaffi.idl.openjdk",
      "type": "shared_library",
      "language": "cxx",
      "runtime": "native",
      "output": "metaffi.idl.openjdk.dll",
      "output_path": "cmake-build-debug\\lang-plugin-openjdk\\idl\\metaffi.idl.openjdk.dll",
      "source_files": [
        "lang-plugin-openjdk\\idl\\openjdk_idl_plugin.cpp"
      ],
      "depends_on": [],
      "externals": [
        {
          "mgr": "system",
          "pkg": "kernel32.lib user32.lib gdi32.lib winspool.lib shell32.lib ole32.lib oleaut32.lib uuid.lib comdlg32.lib advapi32.lib"
        }
      ],
      "evidence": [
        {
          "call_stack": [
            "cmake/CPP.cmake#L133-L133",
            "lang-plugin-openjdk/idl/CMakeLists.txt#L23-L23",
            "lang-plugin-openjdk/idl/CMakeLists.txt#L1-L1"
          ]
        }
      ],
      "test_link_id": null,
      "test_link_name": null
    },
    {
      "id": 7,
      "name": "metaffi.idl.python311",
      "type": "shared_library",
      "language": "cxx",
      "runtime": "native",
      "output": "metaffi.idl.python311.dll",
      "output_path": "cmake-build-debug\\lang-plugin-python311\\idl\\metaffi.idl.python311.dll",
      "source_files": [
        "lang-plugin-python311\\plugin-sdk\\runtime\\cdt.cpp",
        "lang-plugin-python311\\plugin-sdk\\runtime\\cdts_traverse_construct.cpp",
        "lang-plugin-python311\\plugin-sdk\\runtime\\cdts_wrapper.cpp",
        "lang-plugin-python311\\plugin-sdk\\runtime\\metaffi_primitives.cpp",
        "lang-plugin-python311\\plugin-sdk\\runtime\\xllr_capi_loader.c",
        "lang-plugin-python311\\plugin-sdk\\runtime\\xllr_static_capi_loader.cpp",
        "lang-plugin-python311\\plugin-sdk\\utils\\entity_path_parser.cpp",
        "lang-plugin-python311\\plugin-sdk\\utils\\expand_env.cpp",
        "lang-plugin-python311\\plugin-sdk\\utils\\library_loader.cpp",
        "lang-plugin-python311\\plugin-sdk\\utils\\xllr_api_wrapper.cpp",
        "lang-plugin-python311\\runtime\\python3_api_wrapper.cpp"
      ],
      "depends_on": [],
      "externals": [
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_filesystem-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_system-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "kernel32.lib user32.lib gdi32.lib winspool.lib shell32.lib ole32.lib oleaut32.lib uuid.lib comdlg32.lib advapi32.lib"
        }
      ],
      "evidence": [
        {
          "call_stack": [
            "cmake/CPP.cmake#L133-L133",
            "lang-plugin-python311/idl/CMakeLists.txt#L13-L13",
            "lang-plugin-python311/idl/CMakeLists.txt#L1-L1"
          ]
        }
      ],
      "test_link_id": null,
      "test_link_name": null
    },
    {
      "id": 8,
      "name": "openjdk_idl_extractor",
      "type": "executable",
      "language": "UNKNOWN",
      "runtime": "native",
      "output": "openjdk_idl_extractor",
      "output_path": "openjdk_idl_extractor",
      "source_files": [],
      "depends_on": [],
      "externals": [],
      "evidence": [
        {
          "call_stack": [
            "cmake/JVM.cmake#L38-L38",
            "lang-plugin-openjdk/idl/CMakeLists.txt#L15-L15",
            "lang-plugin-openjdk/idl/CMakeLists.txt#L1-L1"
          ]
        }
      ],
      "test_link_id": null,
      "test_link_name": null
    },
    {
      "id": 9,
      "name": "xllr",
      "type": "shared_library",
      "language": "cxx",
      "runtime": "native",
      "output": "xllr.dll",
      "output_path": "cmake-build-debug\\metaffi-core\\XLLR\\xllr.dll",
      "source_files": [
        "metaffi-core\\XLLR\\cdts_alloc.cpp",
        "metaffi-core\\XLLR\\runtime_plugin.cpp",
        "metaffi-core\\XLLR\\runtime_plugin_interface_wrapper.cpp",
        "metaffi-core\\XLLR\\runtime_plugin_repository.cpp",
        "metaffi-core\\XLLR\\xllr_api.cpp",
        "metaffi-core\\plugin-sdk\\runtime\\cdt.cpp",
        "metaffi-core\\plugin-sdk\\runtime\\cdts_traverse_construct.cpp",
        "metaffi-core\\plugin-sdk\\runtime\\cdts_wrapper.cpp",
        "metaffi-core\\plugin-sdk\\runtime\\metaffi_primitives.cpp",
        "metaffi-core\\plugin-sdk\\runtime\\xllr_capi_loader.c",
        "metaffi-core\\plugin-sdk\\runtime\\xllr_static_capi_loader.cpp",
        "metaffi-core\\plugin-sdk\\utils\\entity_path_parser.cpp",
        "metaffi-core\\plugin-sdk\\utils\\expand_env.cpp",
        "metaffi-core\\plugin-sdk\\utils\\library_loader.cpp",
        "metaffi-core\\plugin-sdk\\utils\\xllr_api_wrapper.cpp"
      ],
      "depends_on": [],
      "externals": [
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_filesystem-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_thread-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_atomic-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "synchronization.lib"
        },
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_chrono-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_system-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_date_time-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_container-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "kernel32.lib user32.lib gdi32.lib winspool.lib shell32.lib ole32.lib oleaut32.lib uuid.lib comdlg32.lib advapi32.lib"
        }
      ],
      "evidence": [
        {
          "call_stack": [
            "cmake/CPP.cmake#L133-L133",
            "metaffi-core/XLLR/CMakeLists.txt#L7-L7",
            "metaffi-core/XLLR/CMakeLists.txt#L1-L1"
          ]
        }
      ],
      "test_link_id": null,
      "test_link_name": null
    },
    {
      "id": 10,
      "name": "xllr.go",
      "type": "shared_library",
      "language": "cxx",
      "runtime": "native",
      "output": "xllr.go.dll",
      "output_path": "cmake-build-debug\\lang-plugin-go\\runtime\\xllr.go.dll",
      "source_files": [
        "lang-plugin-go\\runtime\\functions_repository.cpp",
        "lang-plugin-go\\runtime\\go_api.cpp",
        "lang-plugin-go\\runtime\\objects_table.cpp",
        "lang-plugin-go\\plugin-sdk\\runtime\\cdt.cpp",
        "lang-plugin-go\\plugin-sdk\\runtime\\cdts_traverse_construct.cpp",
        "lang-plugin-go\\plugin-sdk\\runtime\\cdts_wrapper.cpp",
        "lang-plugin-go\\plugin-sdk\\runtime\\metaffi_primitives.cpp",
        "lang-plugin-go\\plugin-sdk\\runtime\\xllr_capi_loader.c",
        "lang-plugin-go\\plugin-sdk\\runtime\\xllr_static_capi_loader.cpp",
        "lang-plugin-go\\plugin-sdk\\utils\\entity_path_parser.cpp",
        "lang-plugin-go\\plugin-sdk\\utils\\expand_env.cpp",
        "lang-plugin-go\\plugin-sdk\\utils\\library_loader.cpp",
        "lang-plugin-go\\plugin-sdk\\utils\\xllr_api_wrapper.cpp"
      ],
      "depends_on": [],
      "externals": [
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_filesystem-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_system-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "kernel32.lib user32.lib gdi32.lib winspool.lib shell32.lib ole32.lib oleaut32.lib uuid.lib comdlg32.lib advapi32.lib"
        }
      ],
      "evidence": [
        {
          "call_stack": [
            "cmake/CPP.cmake#L133-L133",
            "lang-plugin-go/runtime/CMakeLists.txt#L11-L11",
            "lang-plugin-go/runtime/CMakeLists.txt#L1-L1"
          ]
        }
      ],
      "test_link_id": null,
      "test_link_name": null
    },
    {
      "id": 11,
      "name": "xllr.openjdk",
      "type": "shared_library",
      "language": "cxx",
      "runtime": "native",
      "output": "xllr.openjdk.dll",
      "output_path": "cmake-build-debug\\lang-plugin-openjdk\\runtime\\xllr.openjdk.dll",
      "source_files": [
        "lang-plugin-openjdk\\runtime\\api.cpp",
        "lang-plugin-openjdk\\runtime\\argument_definition.cpp",
        "lang-plugin-openjdk\\runtime\\cdts_java_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\class_loader.cpp",
        "lang-plugin-openjdk\\runtime\\jarray_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jboolean_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jbyte_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jchar_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jdouble_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jfloat_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jint_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jlong_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jni_caller.cpp",
        "lang-plugin-openjdk\\runtime\\jni_class.cpp",
        "lang-plugin-openjdk\\runtime\\jni_metaffi_handle.cpp",
        "lang-plugin-openjdk\\runtime\\jobject_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jshort_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jstring_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jvalue_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jvm.cpp",
        "lang-plugin-openjdk\\runtime\\objects_table.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\runtime\\cdt.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\runtime\\cdts_traverse_construct.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\runtime\\cdts_wrapper.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\runtime\\metaffi_primitives.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\runtime\\xllr_capi_loader.c",
        "lang-plugin-openjdk\\plugin-sdk\\runtime\\xllr_static_capi_loader.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\utils\\entity_path_parser.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\utils\\expand_env.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\utils\\library_loader.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\utils\\xllr_api_wrapper.cpp"
      ],
      "depends_on": [],
      "externals": [
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_filesystem-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_system-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "kernel32.lib user32.lib gdi32.lib winspool.lib shell32.lib ole32.lib oleaut32.lib uuid.lib comdlg32.lib advapi32.lib"
        }
      ],
      "evidence": [
        {
          "call_stack": [
            "cmake/CPP.cmake#L133-L133",
            "lang-plugin-openjdk/runtime/CMakeLists.txt#L10-L10",
            "lang-plugin-openjdk/runtime/CMakeLists.txt#L1-L1"
          ]
        }
      ],
      "test_link_id": null,
      "test_link_name": null
    },
    {
      "id": 12,
      "name": "xllr.python311",
      "type": "shared_library",
      "language": "cxx",
      "runtime": "native",
      "output": "xllr.python311.dll",
      "output_path": "cmake-build-debug\\lang-plugin-python311\\runtime\\xllr.python311.dll",
      "source_files": [
        "lang-plugin-python311\\runtime\\call_xcall.cpp",
        "lang-plugin-python311\\runtime\\cdts_python3.cpp",
        "lang-plugin-python311\\runtime\\host_cdts_converter.cpp",
        "lang-plugin-python311\\runtime\\metaffi_package_importer.cpp",
        "lang-plugin-python311\\runtime\\py_bool.cpp",
        "lang-plugin-python311\\runtime\\py_bytes.cpp",
        "lang-plugin-python311\\runtime\\py_float.cpp",
        "lang-plugin-python311\\runtime\\py_int.cpp",
        "lang-plugin-python311\\runtime\\py_list.cpp",
        "lang-plugin-python311\\runtime\\py_metaffi_callable.cpp",
        "lang-plugin-python311\\runtime\\py_metaffi_handle.cpp",
        "lang-plugin-python311\\runtime\\py_object.cpp",
        "lang-plugin-python311\\runtime\\py_str.cpp",
        "lang-plugin-python311\\runtime\\py_tuple.cpp",
        "lang-plugin-python311\\runtime\\python3_api_wrapper.cpp",
        "lang-plugin-python311\\runtime\\python_api.cpp",
        "lang-plugin-python311\\runtime\\utils.cpp",
        "lang-plugin-python311\\plugin-sdk\\runtime\\cdt.cpp",
        "lang-plugin-python311\\plugin-sdk\\runtime\\cdts_traverse_construct.cpp",
        "lang-plugin-python311\\plugin-sdk\\runtime\\cdts_wrapper.cpp",
        "lang-plugin-python311\\plugin-sdk\\runtime\\metaffi_primitives.cpp",
        "lang-plugin-python311\\plugin-sdk\\runtime\\xllr_capi_loader.c",
        "lang-plugin-python311\\plugin-sdk\\runtime\\xllr_static_capi_loader.cpp",
        "lang-plugin-python311\\plugin-sdk\\utils\\entity_path_parser.cpp",
        "lang-plugin-python311\\plugin-sdk\\utils\\expand_env.cpp",
        "lang-plugin-python311\\plugin-sdk\\utils\\library_loader.cpp",
        "lang-plugin-python311\\plugin-sdk\\utils\\xllr_api_wrapper.cpp"
      ],
      "depends_on": [],
      "externals": [
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_filesystem-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_system-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "kernel32.lib user32.lib gdi32.lib winspool.lib shell32.lib ole32.lib oleaut32.lib uuid.lib comdlg32.lib advapi32.lib"
        }
      ],
      "evidence": [
        {
          "call_stack": [
            "cmake/CPP.cmake#L133-L133",
            "lang-plugin-python311/runtime/CMakeLists.txt#L10-L10",
            "lang-plugin-python311/runtime/CMakeLists.txt#L1-L1"
          ]
        }
      ],
      "test_link_id": null,
      "test_link_name": null
    },
    {
      "id": 13,
      "name": "xllr_capi_test",
      "type": "executable",
      "language": "cxx",
      "runtime": "native",
      "output": "xllr_capi_test.exe",
      "output_path": "cmake-build-debug\\metaffi-core\\xllr_capi_test.exe",
      "source_files": [
        "metaffi-core\\plugin-sdk\\runtime\\xllr_capi_test.cpp",
        "metaffi-core\\plugin-sdk\\runtime\\cdt.cpp",
        "metaffi-core\\plugin-sdk\\runtime\\cdts_traverse_construct.cpp",
        "metaffi-core\\plugin-sdk\\runtime\\cdts_wrapper.cpp",
        "metaffi-core\\plugin-sdk\\runtime\\metaffi_primitives.cpp",
        "metaffi-core\\plugin-sdk\\runtime\\xllr_capi_loader.c",
        "metaffi-core\\plugin-sdk\\runtime\\xllr_static_capi_loader.cpp",
        "metaffi-core\\plugin-sdk\\utils\\entity_path_parser.cpp",
        "metaffi-core\\plugin-sdk\\utils\\expand_env.cpp",
        "metaffi-core\\plugin-sdk\\utils\\library_loader.cpp",
        "metaffi-core\\plugin-sdk\\utils\\xllr_api_wrapper.cpp"
      ],
      "depends_on": [],
      "externals": [
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_filesystem-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_system-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "kernel32.lib user32.lib gdi32.lib winspool.lib shell32.lib ole32.lib oleaut32.lib uuid.lib comdlg32.lib advapi32.lib"
        }
      ],
      "evidence": [
        {
          "call_stack": [
            "cmake/CPP.cmake#L73-L73",
            "metaffi-core/plugin-sdk/run_sdk_tests.cmake#L15-L15",
            "metaffi-core/plugin-sdk/run_sdk_tests.cmake#L1-L1",
            "metaffi-core/CMakeLists.txt#L12-L12",
            "metaffi-core/CMakeLists.txt#L1-L1"
          ]
        }
      ],
      "test_link_id": 2,
      "test_link_name": "xllr_capi_test"
    },
    {
      "id": 14,
      "name": "python311_idl_plugin_test",
      "type": "executable",
      "language": "cxx",
      "runtime": "native",
      "output": "python311_idl_plugin_test.exe",
      "output_path": "cmake-build-debug\\lang-plugin-python311\\idl\\python311_idl_plugin_test.exe",
      "source_files": [
        "lang-plugin-python311\\idl\\idl_plugin_test.cpp",
        "lang-plugin-python311\\idl\\python_idl_plugin.cpp",
        "lang-plugin-python311\\plugin-sdk\\runtime\\xllr_capi_loader.c",
        "lang-plugin-python311\\runtime\\python3_api_wrapper.cpp"
      ],
      "depends_on": [
        "metaffi.idl.python311"
      ],
      "externals": [
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_filesystem-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_system-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "kernel32.lib user32.lib gdi32.lib winspool.lib shell32.lib ole32.lib oleaut32.lib uuid.lib comdlg32.lib advapi32.lib"
        }
      ],
      "evidence": [
        {
          "call_stack": [
            "cmake/CPP.cmake#L73-L73",
            "lang-plugin-python311/idl/CMakeLists.txt#L22-L22",
            "lang-plugin-python311/idl/CMakeLists.txt#L1-L1"
          ]
        }
      ],
      "test_link_id": null,
      "test_link_name": null
    },
    {
      "id": 15,
      "name": "go_api_test",
      "type": "executable",
      "language": "cxx",
      "runtime": "native",
      "output": "go_api_test.exe",
      "output_path": "cmake-build-debug\\lang-plugin-go\\runtime\\go_api_test.exe",
      "source_files": [
        "lang-plugin-go\\plugin-sdk\\runtime\\cdt.cpp",
        "lang-plugin-go\\plugin-sdk\\runtime\\cdts_traverse_construct.cpp",
        "lang-plugin-go\\plugin-sdk\\runtime\\cdts_wrapper.cpp",
        "lang-plugin-go\\plugin-sdk\\runtime\\metaffi_primitives.cpp",
        "lang-plugin-go\\plugin-sdk\\runtime\\xllr_capi_loader.c",
        "lang-plugin-go\\plugin-sdk\\runtime\\xllr_static_capi_loader.cpp",
        "lang-plugin-go\\plugin-sdk\\utils\\entity_path_parser.cpp",
        "lang-plugin-go\\plugin-sdk\\utils\\expand_env.cpp",
        "lang-plugin-go\\plugin-sdk\\utils\\library_loader.cpp",
        "lang-plugin-go\\plugin-sdk\\utils\\xllr_api_wrapper.cpp",
        "lang-plugin-go\\runtime\\go_api_test.cpp"
      ],
      "depends_on": [
        "xllr.go",
        "build_go_guest"
      ],
      "externals": [
        {
          "mgr": "system",
          "pkg": "lang-plugin-go\\runtime\\xllr.go.lib"
        },
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_filesystem-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_system-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "kernel32.lib user32.lib gdi32.lib winspool.lib shell32.lib ole32.lib oleaut32.lib uuid.lib comdlg32.lib advapi32.lib"
        }
      ],
      "evidence": [
        {
          "call_stack": [
            "cmake/CPP.cmake#L73-L73",
            "lang-plugin-go/runtime/CMakeLists.txt#L29-L29",
            "lang-plugin-go/runtime/CMakeLists.txt#L1-L1"
          ]
        }
      ],
      "test_link_id": 13,
      "test_link_name": "go_api_test"
    },
    {
      "id": 16,
      "name": "cdts_java_test",
      "type": "executable",
      "language": "cxx",
      "runtime": "native",
      "output": "cdts_java_test.exe",
      "output_path": "cmake-build-debug\\lang-plugin-openjdk\\runtime\\cdts_java_test.exe",
      "source_files": [
        "lang-plugin-openjdk\\runtime\\api.cpp",
        "lang-plugin-openjdk\\runtime\\argument_definition.cpp",
        "lang-plugin-openjdk\\runtime\\cdts_java_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\class_loader.cpp",
        "lang-plugin-openjdk\\runtime\\jarray_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jboolean_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jbyte_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jchar_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jdouble_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jfloat_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jint_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jlong_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jni_caller.cpp",
        "lang-plugin-openjdk\\runtime\\jni_class.cpp",
        "lang-plugin-openjdk\\runtime\\jni_metaffi_handle.cpp",
        "lang-plugin-openjdk\\runtime\\jobject_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jshort_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jstring_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jvalue_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jvm.cpp",
        "lang-plugin-openjdk\\runtime\\objects_table.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\runtime\\cdt.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\runtime\\cdts_traverse_construct.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\runtime\\cdts_wrapper.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\runtime\\metaffi_primitives.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\runtime\\xllr_capi_loader.c",
        "lang-plugin-openjdk\\plugin-sdk\\runtime\\xllr_static_capi_loader.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\utils\\entity_path_parser.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\utils\\expand_env.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\utils\\library_loader.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\utils\\xllr_api_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\cdts_java_test.cpp"
      ],
      "depends_on": [
        "xllr.openjdk"
      ],
      "externals": [
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_filesystem-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_system-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "kernel32.lib user32.lib gdi32.lib winspool.lib shell32.lib ole32.lib oleaut32.lib uuid.lib comdlg32.lib advapi32.lib"
        }
      ],
      "evidence": [
        {
          "call_stack": [
            "cmake/CPP.cmake#L73-L73",
            "lang-plugin-openjdk/runtime/CMakeLists.txt#L19-L19",
            "lang-plugin-openjdk/runtime/CMakeLists.txt#L1-L1"
          ]
        }
      ],
      "test_link_id": 10,
      "test_link_name": "cdts_java_test"
    },
    {
      "id": 17,
      "name": "openjdk_api_test",
      "type": "executable",
      "language": "cxx",
      "runtime": "native",
      "output": "openjdk_api_test.exe",
      "output_path": "cmake-build-debug\\lang-plugin-openjdk\\runtime\\openjdk_api_test.exe",
      "source_files": [
        "lang-plugin-openjdk\\runtime\\api.cpp",
        "lang-plugin-openjdk\\runtime\\argument_definition.cpp",
        "lang-plugin-openjdk\\runtime\\cdts_java_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\class_loader.cpp",
        "lang-plugin-openjdk\\runtime\\jarray_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jboolean_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jbyte_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jchar_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jdouble_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jfloat_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jint_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jlong_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jni_caller.cpp",
        "lang-plugin-openjdk\\runtime\\jni_class.cpp",
        "lang-plugin-openjdk\\runtime\\jni_metaffi_handle.cpp",
        "lang-plugin-openjdk\\runtime\\jobject_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jshort_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jstring_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jvalue_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\jvm.cpp",
        "lang-plugin-openjdk\\runtime\\objects_table.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\runtime\\cdt.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\runtime\\cdts_traverse_construct.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\runtime\\cdts_wrapper.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\runtime\\metaffi_primitives.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\runtime\\xllr_capi_loader.c",
        "lang-plugin-openjdk\\plugin-sdk\\runtime\\xllr_static_capi_loader.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\utils\\entity_path_parser.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\utils\\expand_env.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\utils\\library_loader.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\utils\\xllr_api_wrapper.cpp",
        "lang-plugin-openjdk\\runtime\\cdts_java_test.cpp"
      ],
      "depends_on": [
        "xllr.openjdk"
      ],
      "externals": [
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_filesystem-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_system-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "kernel32.lib user32.lib gdi32.lib winspool.lib shell32.lib ole32.lib oleaut32.lib uuid.lib comdlg32.lib advapi32.lib"
        }
      ],
      "evidence": [
        {
          "call_stack": [
            "cmake/CPP.cmake#L73-L73",
            "lang-plugin-openjdk/runtime/CMakeLists.txt#L28-L28",
            "lang-plugin-openjdk/runtime/CMakeLists.txt#L1-L1"
          ]
        }
      ],
      "test_link_id": 11,
      "test_link_name": "openjdk_api_test"
    },
    {
      "id": 18,
      "name": "xllr.openjdk.jni.bridge",
      "type": "shared_library",
      "language": "cxx",
      "runtime": "native",
      "output": "xllr.openjdk.jni.bridge.dll",
      "output_path": "cmake-build-debug\\lang-plugin-openjdk\\xllr-openjdk-bridge\\xllr.openjdk.jni.bridge.dll",
      "source_files": [
        "lang-plugin-openjdk\\xllr-openjdk-bridge\\metaffi_bridge.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\runtime\\cdt.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\runtime\\cdts_traverse_construct.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\runtime\\cdts_wrapper.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\runtime\\metaffi_primitives.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\runtime\\xllr_capi_loader.c",
        "lang-plugin-openjdk\\plugin-sdk\\runtime\\xllr_static_capi_loader.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\utils\\entity_path_parser.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\utils\\expand_env.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\utils\\library_loader.cpp",
        "lang-plugin-openjdk\\plugin-sdk\\utils\\xllr_api_wrapper.cpp"
      ],
      "depends_on": [
        "xllr.openjdk"
      ],
      "externals": [
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_filesystem-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "lang-plugin-openjdk\\runtime\\xllr.openjdk.lib"
        },
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_system-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "kernel32.lib user32.lib gdi32.lib winspool.lib shell32.lib ole32.lib oleaut32.lib uuid.lib comdlg32.lib advapi32.lib"
        }
      ],
      "evidence": [
        {
          "call_stack": [
            "cmake/CPP.cmake#L133-L133",
            "lang-plugin-openjdk/xllr-openjdk-bridge/CMakeLists.txt#L9-L9",
            "lang-plugin-openjdk/xllr-openjdk-bridge/CMakeLists.txt#L1-L1"
          ]
        }
      ],
      "test_link_id": null,
      "test_link_name": null
    },
    {
      "id": 19,
      "name": "python311.publish",
      "type": "executable",
      "language": "UNKNOWN",
      "runtime": "native",
      "output": "python311.publish",
      "output_path": "python311.publish",
      "source_files": [],
      "depends_on": [
        "xllr.python311"
      ],
      "externals": [],
      "evidence": [
        {
          "call_stack": [
            "lang-plugin-python311/api/CMakeLists.txt#L19-L19",
            "lang-plugin-python311/api/CMakeLists.txt#L1-L1"
          ]
        }
      ],
      "test_link_id": null,
      "test_link_name": null
    },
    {
      "id": 20,
      "name": "python_runtime_test",
      "type": "executable",
      "language": "cxx",
      "runtime": "native",
      "output": "python_runtime_test.exe",
      "output_path": "cmake-build-debug\\lang-plugin-python311\\runtime\\python_runtime_test.exe",
      "source_files": [
        "lang-plugin-python311\\runtime\\call_xcall.cpp",
        "lang-plugin-python311\\runtime\\cdts_python3.cpp",
        "lang-plugin-python311\\runtime\\host_cdts_converter.cpp",
        "lang-plugin-python311\\runtime\\metaffi_package_importer.cpp",
        "lang-plugin-python311\\runtime\\py_bool.cpp",
        "lang-plugin-python311\\runtime\\py_bytes.cpp",
        "lang-plugin-python311\\runtime\\py_float.cpp",
        "lang-plugin-python311\\runtime\\py_int.cpp",
        "lang-plugin-python311\\runtime\\py_list.cpp",
        "lang-plugin-python311\\runtime\\py_metaffi_callable.cpp",
        "lang-plugin-python311\\runtime\\py_metaffi_handle.cpp",
        "lang-plugin-python311\\runtime\\py_object.cpp",
        "lang-plugin-python311\\runtime\\py_str.cpp",
        "lang-plugin-python311\\runtime\\py_tuple.cpp",
        "lang-plugin-python311\\runtime\\python3_api_wrapper.cpp",
        "lang-plugin-python311\\runtime\\python_api.cpp",
        "lang-plugin-python311\\runtime\\utils.cpp",
        "lang-plugin-python311\\plugin-sdk\\runtime\\cdt.cpp",
        "lang-plugin-python311\\plugin-sdk\\runtime\\cdts_traverse_construct.cpp",
        "lang-plugin-python311\\plugin-sdk\\runtime\\cdts_wrapper.cpp",
        "lang-plugin-python311\\plugin-sdk\\runtime\\metaffi_primitives.cpp",
        "lang-plugin-python311\\plugin-sdk\\runtime\\xllr_capi_loader.c",
        "lang-plugin-python311\\plugin-sdk\\runtime\\xllr_static_capi_loader.cpp",
        "lang-plugin-python311\\plugin-sdk\\utils\\entity_path_parser.cpp",
        "lang-plugin-python311\\plugin-sdk\\utils\\expand_env.cpp",
        "lang-plugin-python311\\plugin-sdk\\utils\\library_loader.cpp",
        "lang-plugin-python311\\plugin-sdk\\utils\\xllr_api_wrapper.cpp",
        "lang-plugin-python311\\runtime\\python_runtime_test.cpp"
      ],
      "depends_on": [
        "xllr.python311"
      ],
      "externals": [
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_filesystem-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_system-vc143-mt-gd-x64-1_87.lib"
        },
        {
          "mgr": "system",
          "pkg": "kernel32.lib user32.lib gdi32.lib winspool.lib shell32.lib ole32.lib oleaut32.lib uuid.lib comdlg32.lib advapi32.lib"
        }
      ],
      "evidence": [
        {
          "call_stack": [
            "cmake/CPP.cmake#L73-L73",
            "lang-plugin-python311/runtime/CMakeLists.txt#L19-L19",
            "lang-plugin-python311/runtime/CMakeLists.txt#L1-L1"
          ]
        }
      ],
      "test_link_id": 3,
      "test_link_name": "python_runtime_test"
    },
    {
      "id": 21,
      "name": "xllr.openjdk.bridge",
      "type": "executable",
      "language": "UNKNOWN",
      "runtime": "native",
      "output": "xllr.openjdk.bridge",
      "output_path": "xllr.openjdk.bridge",
      "source_files": [],
      "depends_on": [
        "xllr.openjdk.jni.bridge"
      ],
      "externals": [],
      "evidence": [
        {
          "call_stack": [
            "cmake/JVM.cmake#L38-L38",
            "lang-plugin-openjdk/xllr-openjdk-bridge/CMakeLists.txt#L19-L19",
            "lang-plugin-openjdk/xllr-openjdk-bridge/CMakeLists.txt#L1-L1"
          ]
        }
      ],
      "test_link_id": null,
      "test_link_name": null
    },
    {
      "id": 22,
      "name": "metaffi.api",
      "type": "executable",
      "language": "UNKNOWN",
      "runtime": "native",
      "output": "metaffi.api",
      "output_path": "metaffi.api",
      "source_files": [],
      "depends_on": [
        "xllr.openjdk.bridge"
      ],
      "externals": [],
      "evidence": [
        {
          "call_stack": [
            "cmake/JVM.cmake#L38-L38",
            "lang-plugin-openjdk/api/CMakeLists.txt#L9-L9",
            "lang-plugin-openjdk/api/CMakeLists.txt#L1-L1"
          ]
        }
      ],
      "test_link_id": null,
      "test_link_name": null
    }
  ],
  "aggregators": [
    {
      "id": 0,
      "name": "MetaFFI",
      "depends_on": [
        "metaffi-core",
        "python311",
        "openjdk",
        "go"
      ],
      "evidence": [
        {
          "call_stack": [
            "CMakeLists.txt#L64-L64",
            "CMakeLists.txt#L1-L1"
          ]
        }
      ]
    },
    {
      "id": 1,
      "name": "build_go_guest",
      "depends_on": [],
      "evidence": [
        {
          "call_stack": [
            "lang-plugin-go/runtime/CMakeLists.txt#L26-L26",
            "lang-plugin-go/runtime/CMakeLists.txt#L1-L1"
          ]
        }
      ]
    },
    {
      "id": 2,
      "name": "go",
      "depends_on": [
        "xllr.go",
        "go_api_test",
        "metaffi.compiler.go",
        "metaffi.idl.go"
      ],
      "evidence": [
        {
          "call_stack": [
            "lang-plugin-go/CMakeLists.txt#L20-L20",
            "lang-plugin-go/CMakeLists.txt#L1-L1"
          ]
        }
      ]
    },
    {
      "id": 3,
      "name": "metaffi-core",
      "depends_on": [
        "cdts_test",
        "xllr_capi_test",
        "xllr",
        "metaffi"
      ],
      "evidence": [
        {
          "call_stack": [
            "metaffi-core/CMakeLists.txt#L15-L15",
            "metaffi-core/CMakeLists.txt#L1-L1"
          ]
        }
      ]
    },
    {
      "id": 4,
      "name": "openjdk",
      "depends_on": [
        "metaffi.idl.openjdk",
        "metaffi.compiler.openjdk",
        "xllr.openjdk",
        "cdts_java_test",
        "openjdk_api_test",
        "xllr.openjdk.jni.bridge",
        "xllr.openjdk.bridge",
        "metaffi.api"
      ],
      "evidence": [
        {
          "call_stack": [
            "lang-plugin-openjdk/CMakeLists.txt#L20-L20",
            "lang-plugin-openjdk/CMakeLists.txt#L1-L1"
          ]
        }
      ]
    }
  ],
  "runners": [
    {
      "id": 0,
      "name": "python311",
      "hint": "lang-plugin-python311/CMakeLists.txt#L18-L18",
      "evidence": [
        {
          "call_stack": [
            "lang-plugin-python311/CMakeLists.txt#L18-L18",
            "lang-plugin-python311/CMakeLists.txt#L1-L1"
          ]
        }
      ]
    }
  ],
  "tests": [
    {
      "id": 0,
      "name": "cdts_test",
      "framework": "Test executable: C:/src/github.com/MetaFFI/output/windows/x64/Debug/cdts_test.exe",
      "exe_component": null,
      "components": [
        "cdts_test"
      ],
      "evidence": [
        {
          "call_stack": [
            "C:/src/github.com/MetaFFI/metaffi-core/plugin-sdk/run_sdk_tests.cmake#L11-L11"
          ]
        }
      ]
    },
    {
      "id": 1,
      "name": "xllr_capi_test",
      "framework": "Test executable: C:/src/github.com/MetaFFI/output/windows/x64/Debug/xllr_capi_test.exe",
      "exe_component": null,
      "components": [
        "xllr_capi_test"
      ],
      "evidence": [
        {
          "call_stack": [
            "C:/src/github.com/MetaFFI/metaffi-core/plugin-sdk/run_sdk_tests.cmake#L20-L20"
          ]
        }
      ]
    },
    {
      "id": 2,
      "name": "python_runtime_test",
      "framework": "Test executable: C:/src/github.com/MetaFFI/output/windows/x64/Debug/python_runtime_test.exe",
      "exe_component": null,
      "components": [
        "python_runtime_test"
      ],
      "evidence": [
        {
          "call_stack": [
            "C:/src/github.com/MetaFFI/lang-plugin-python311/runtime/CMakeLists.txt#L35-L35"
          ]
        }
      ]
    },
    {
      "id": 3,
      "name": "python3_api_unitest",
      "framework": "Test executable: C:/Users/green/AppData/Local/Programs/Python/Python311/python3.exe",
      "exe_component": null,
      "components": [],
      "evidence": [
        {
          "call_stack": [
            "C:/src/github.com/MetaFFI/lang-plugin-python311/api/CMakeLists.txt#L5-L5"
          ]
        }
      ]
    },
    {
      "id": 4,
      "name": "python3_api_cross_pl_tests",
      "framework": "Test executable: C:/Users/green/AppData/Local/Programs/Python/Python311/python3.exe",
      "exe_component": null,
      "components": [],
      "evidence": [
        {
          "call_stack": [
            "C:/src/github.com/MetaFFI/lang-plugin-python311/api/CMakeLists.txt#L12-L12"
          ]
        }
      ]
    },
    {
      "id": 5,
      "name": "idl_plugin_test",
      "framework": "Test executable: C:/src/github.com/MetaFFI/output/windows/x64/Debug/idl_plugin_test.exe",
      "exe_component": null,
      "components": [],
      "evidence": [
        {
          "call_stack": [
            "C:/src/github.com/MetaFFI/lang-plugin-python311/idl/CMakeLists.txt#L32-L32"
          ]
        }
      ]
    },
    {
      "id": 6,
      "name": "metaffi_compiler_python311_test",
      "framework": "Test executable: C:/Program Files/Go/bin/go.exe",
      "exe_component": null,
      "components": [],
      "evidence": [
        {
          "call_stack": [
            "C:/src/github.com/MetaFFI/lang-plugin-python311/compiler/CMakeLists.txt#L19-L19"
          ]
        }
      ]
    },
    {
      "id": 7,
      "name": "openjdk_idl_plugin_java_tests",
      "framework": "JUnit",
      "exe_component": null,
      "components": [],
      "evidence": [
        {
          "call_stack": [
            "C:/src/github.com/MetaFFI/lang-plugin-openjdk/idl/CMakeLists.txt#L78-L78"
          ]
        }
      ]
    },
    {
      "id": 8,
      "name": "(go test) openjdk_compiler_go_tests",
      "framework": "Test executable: C:/Program Files/Go/bin/go.exe",
      "exe_component": null,
      "components": [],
      "evidence": [
        {
          "call_stack": [
            "C:/src/github.com/MetaFFI/cmake/Go.cmake#L74-L74"
          ]
        }
      ]
    },
    {
      "id": 9,
      "name": "cdts_java_test",
      "framework": "Test executable: C:/src/github.com/MetaFFI/output/windows/x64/Debug/cdts_java_test.exe",
      "exe_component": null,
      "components": [
        "cdts_java_test"
      ],
      "evidence": [
        {
          "call_stack": [
            "C:/src/github.com/MetaFFI/lang-plugin-openjdk/runtime/CMakeLists.txt#L25-L25"
          ]
        }
      ]
    },
    {
      "id": 10,
      "name": "openjdk_api_test",
      "framework": "Test executable: C:/src/github.com/MetaFFI/output/windows/x64/Debug/openjdk_api_test.exe",
      "exe_component": null,
      "components": [
        "openjdk_api_test"
      ],
      "evidence": [
        {
          "call_stack": [
            "C:/src/github.com/MetaFFI/lang-plugin-openjdk/runtime/CMakeLists.txt#L34-L34"
          ]
        }
      ]
    },
    {
      "id": 11,
      "name": "openjdk_api_cross_pl_tests",
      "framework": "Test executable: C:/Users/green/AppData/Local/Programs/Python/Python311/python3.exe",
      "exe_component": null,
      "components": [],
      "evidence": [
        {
          "call_stack": [
            "C:/src/github.com/MetaFFI/lang-plugin-openjdk/api/CMakeLists.txt#L23-L23"
          ]
        }
      ]
    },
    {
      "id": 12,
      "name": "go_api_test",
      "framework": "Test executable: C:/Users/green/AppData/Local/Programs/Python/Python311/python3.exe",
      "exe_component": null,
      "components": [],
      "evidence": [
        {
          "call_stack": [
            "C:/src/github.com/MetaFFI/lang-plugin-go/runtime/CMakeLists.txt#L40-L40"
          ]
        }
      ]
    },
    {
      "id": 13,
      "name": "go_runtime_test",
      "framework": "Test executable: C:/Users/green/AppData/Local/Programs/Python/Python311/python3.exe",
      "exe_component": null,
      "components": [],
      "evidence": [
        {
          "call_stack": [
            "C:/src/github.com/MetaFFI/lang-plugin-go/go-runtime/CMakeLists.txt#L7-L7"
          ]
        }
      ]
    },
    {
      "id": 14,
      "name": "metaffi_idl_go_test",
      "framework": "Test executable: C:/Program Files/Go/bin/go.exe",
      "exe_component": null,
      "components": [],
      "evidence": [
        {
          "call_stack": [
            "C:/src/github.com/MetaFFI/lang-plugin-go/idl/CMakeLists.txt#L16-L16"
          ]
        }
      ]
    },
    {
      "id": 15,
      "name": "metaffi_compiler_go_test",
      "framework": "Test executable: C:/Program Files/Go/bin/go.exe",
      "exe_component": null,
      "components": [],
      "evidence": [
        {
          "call_stack": [
            "C:/src/github.com/MetaFFI/lang-plugin-go/compiler/CMakeLists.txt#L21-L21"
          ]
        }
      ]
    },
    {
      "id": 16,
      "name": "go_api_cross_pl_tests",
      "framework": "Test executable: C:/Users/green/AppData/Local/Programs/Python/Python311/python3.exe",
      "exe_component": null,
      "components": [],
      "evidence": [
        {
          "call_stack": [
            "C:/src/github.com/MetaFFI/lang-plugin-go/api/CMakeLists.txt#L7-L7"
          ]
        }
      ]
    }
  ],
  "gaps": {
    "missing_sources": [],
    "missing_outputs": [],
    "orphans": {
      "aggregators": [],
      "tests": []
    },
    "risky_runners": []
  }
}
```