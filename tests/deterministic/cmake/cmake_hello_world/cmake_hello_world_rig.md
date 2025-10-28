# Repository Build Analysis

## Repository Information
- **Repository**: TestProject
- **Root Path**: C:\src\github.com\GreenFuze\spade\tests\test_repos\cmake_hello_world
- **Build System**: CMake
- **Scope**: ['./']
- **Detection Mode**: configure_only
- **Configure Command**: cmake -B C:\src\github.com\GreenFuze\spade\tests\test_repos\cmake_hello_world\spade_build
- **Test Discovery Command**: ctest --test-dir C:\src\github.com\GreenFuze\spade\tests\test_repos\cmake_hello_world\spade_build

## Build Data

The following JSON contains the complete build analysis data:

```json
{
  "repo": {
    "name": "TestProject",
    "root": "C:\\src\\github.com\\GreenFuze\\spade\\tests\\test_repos\\cmake_hello_world"
  },
  "build": {
    "system": "CMake",
    "generator": null,
    "type": null,
    "configure_cmd": "cmake -B C:\\src\\github.com\\GreenFuze\\spade\\tests\\test_repos\\cmake_hello_world\\spade_build",
    "test_cmd": "ctest --test-dir C:\\src\\github.com\\GreenFuze\\spade\\tests\\test_repos\\cmake_hello_world\\spade_build"
  },
  "components": [
    {
      "id": 0,
      "name": "utils",
      "type": "static_library",
      "language": "cxx",
      "runtime": "native",
      "output": "utils.lib",
      "output_path": "spade_build\\Debug\\utils.lib",
      "source_files": [
        "src\\utils.cpp"
      ],
      "depends_on": [],
      "externals": [],
      "evidence": [
        {
          "call_stack": [
            "CMakeLists.txt#L8-L8",
            "CMakeLists.txt#L1-L1"
          ]
        }
      ],
      "test_link_id": null,
      "test_link_name": null
    },
    {
      "id": 1,
      "name": "hello_world",
      "type": "executable",
      "language": "cxx",
      "runtime": "native",
      "output": "hello_world.exe",
      "output_path": "spade_build\\Debug\\hello_world.exe",
      "source_files": [
        "src\\main.cpp"
      ],
      "depends_on": [
        "utils"
      ],
      "externals": [
        {
          "package_manager": "system",
          "package": "debug\\utils.lib"
        },
        {
          "package_manager": "system",
          "package": "kernel32.lib user32.lib gdi32.lib winspool.lib shell32.lib ole32.lib oleaut32.lib uuid.lib comdlg32.lib advapi32.lib"
        }
      ],
      "evidence": [
        {
          "call_stack": [
            "CMakeLists.txt#L5-L5",
            "CMakeLists.txt#L1-L1"
          ]
        }
      ],
      "test_link_id": null,
      "test_link_name": null
    }
  ],
  "aggregators": [],
  "runners": [],
  "tests": [],
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