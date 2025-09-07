awesome — I appended a deep-dive “reference + recipes” section you can drop straight under the previous markdown you have. I verified anything that’s factual against the official CMake docs and Kitware posts, and I cite them with `\cite{}` (see the BibTeX block at the end).

---

# Advanced Reference & Recipes for `cmake_file_api`

> Works with CMake File API **v1** and codemodel **v2**. Tested concepts apply to CMake ≥ 3.14; some minor fields are newer (notes inline). \cite{cmake-file-api-manual}

## Object model (practical cheat-sheet)

### Top level reply

* `.cmake/api/v1/reply/index-*.json` lists all reply files and versions. \cite{cmake-file-api-manual}
* Important kinds you’ll usually read:

  * **`codemodel` v2** → projects, directories, and *per-target* JSONs
  * **`toolchains` v1** → compilers, versions, implicit include/link dirs
  * **`cache` v2** → `CMakeCache.txt` entries (e.g., `CMAKE_SYSTEM_NAME`)
  * **`cmakeFiles` v1** → all `CMakeLists.txt` and included `.cmake` files
    (links and field layouts in manual) \cite{cmake-file-api-manual}

### Codemodel v2, *directory* object (selected members)

* `source` / `build`: absolute paths of the directory
* `projects[]`: project names / ids
* `targets[]`: references to per-target JSON files (`jsonFile`)
* `backtraceGraph`: graph mapping integer ids → file paths + line numbers
  (shared by other objects that store `backtrace` indices) \cite{codemodel-dir,backtrace-graph}

### Codemodel v2, *target* object (selected members)

* `name`, `id`, `type` (e.g., `EXECUTABLE`, `STATIC_LIBRARY`, …)
* `nameOnDisk`: final filename for the target output
* `artifacts[]`: paths to built outputs (exe/lib), absolute or relative to top build dir
* `dependencies[]`: other **CMake** targets this target depends on
* `compileGroups[]`:

  * `language` (e.g., `C`, `CXX`)
  * `compileCommandFragments[]` (compiler flags)
  * `includes[]`, `defines[]`, *etc.*
* `sources[]` and `sourceGroups[]`
* `link`: `language`, `commandFragments[]` (linker, library args, search paths), frameworks (Apple), *etc.*
* `folder` (target’s IDE folder if set)
* `workingDirectory` (since 2.8; from `DEBUGGER_WORKING_DIRECTORY`)
* `backtraceGraph` (for this target) \cite{codemodel-target,ubuntu-manpage}

> **Note:** codemodel v2 **does not** enumerate *imported* (third-party) targets; external libs are exposed via **link command fragments** (libraries/flags) instead. \cite{discourse-imported}

### Toolchains v1 (selected members)

* `toolchains[]`:

  * `language`
  * `compiler.path`, `compiler.id`, `compiler.version`
  * `compiler.implicit.includeDirectories[]`, `linkDirectories[]`, `linkLibraries[]`
  * `sourceFileExtensions[]` \cite{toolchains}

### Cache v2

* `entries[]`: `name`, `value`, `type`, `properties[]` for all cache vars (e.g., `CMAKE_SYSTEM_NAME`, `CMAKE_<LANG>_COMPILER`). \cite{cache}

### Tests (CTest JSON)

* CTest provides `--show-only=json-v1` with:

  * `tests[]`: `name`, `command[]`, `properties[]`, `backtrace` (maps through a test-local `backtraceGraph` with file+line)
  * Use to *discover tests*, their commands, labels, and environment. \cite{ctest-json}

---

## Python: loading the model

Below are **two interchangeable loaders**: the `cmake_file_api` package (preferred), and a pure-JSON fallback if the package is missing. All downstream code assumes the simple dict shape returned by `load_reply()`.

```python
# loader.py
from __future__ import annotations
import json, os, glob, pathlib, subprocess, sys
from typing import Any, Dict

def _build_dir_to_index(build_dir: str) -> str:
    reply = pathlib.Path(build_dir) / ".cmake" / "api" / "v1" / "reply"
    idx = sorted(reply.glob("index-*.json"))[-1]  # latest
    return str(idx)

def load_reply(build_dir: str) -> Dict[str, Any]:
    """
    Returns:
      {
        "index": <index-json>,
        "codemodel": <codemodel-json>,
        "targets": { <target-id>: <target-json>, ... },
        "toolchains": <toolchains-json or None>,
        "cache": <cache-json or None>,
        "cmakeFiles": <cmakeFiles-json or None>,
      }
    """
    # ---- Preferred: python 'cmake_file_api' package ----
    try:
        import cmake_file_api  # type: ignore
        # The package mirrors the JSON; let’s normalize to dicts
        proj = cmake_file_api.load(build_dir)  # returns a facade with .index/.objects
        index = proj.index  # dict-like
        objs = { (o["kind"], o["version"]["major"]) : o for o in index["objects"] }

        def _read(ref):
            p = pathlib.Path(build_dir, ".cmake", "api", "v1", "reply", ref["jsonFile"])
            return json.loads(p.read_text(encoding="utf-8"))

        cm = _read(objs[("codemodel", 2)])
        # Pull all target jsons referenced by codemodel
        targets = {}
        for cfg in cm["configurations"]:
            for t in cfg.get("targets", []):
                tj = _read(t)
                targets[tj["id"]] = tj

        toolchains = _read(objs[("toolchains", 1)]) if ("toolchains", 1) in objs else None
        cache = _read(objs[("cache", 2)]) if ("cache", 2) in objs else None
        cmakeFiles = _read(objs[("cmakeFiles", 1)]) if ("cmakeFiles", 1) in objs else None
        return {"index": index, "codemodel": cm, "targets": targets,
                "toolchains": toolchains, "cache": cache, "cmakeFiles": cmakeFiles}

    except Exception:
        # ---- Fallback: pure JSON ----
        index_path = _build_dir_to_index(build_dir)
        index = json.loads(open(index_path, "r", encoding="utf-8").read())

        # helper to open any reply ref
        reply_root = os.path.dirname(index_path)
        def _open_ref(ref):
            return json.loads(open(os.path.join(reply_root, ref["jsonFile"]), "r", encoding="utf-8").read())

        kinds = {}
        for o in index["objects"]:
            kinds[(o["kind"], o["version"]["major"])] = o

        cm = _open_ref(kinds[("codemodel", 2)])
        targets = {}
        for cfg in cm.get("configurations", []):
            for t in cfg.get("targets", []):
                tj = _open_ref(t)
                targets[tj["id"]] = tj

        toolchains = _open_ref(kinds[("toolchains", 1)]) if ("toolchains", 1) in kinds else None
        cache = _open_ref(kinds[("cache", 2)]) if ("cache", 2) in kinds else None
        cmakeFiles = _open_ref(kinds[("cmakeFiles", 1)]) if ("cmakeFiles", 1) in kinds else None
        return {"index": index, "codemodel": cm, "targets": targets,
                "toolchains": toolchains, "cache": cache, "cmakeFiles": cmakeFiles}
```

*(The field names and object kinds match the official spec.)* \cite{cmake-file-api-manual}

---

## Recipe: extract **package dependencies** from targets

There are **two** sources of dependency data:

1. **CMake-target dependencies** (in-tree) → `target["dependencies"][]` (ids of other codemodel targets). \cite{codemodel-target}

2. **External/package libs** (from `find_package`, system libs, etc.) → **link command fragments** (`target["link"]["commandFragments"][]`) and frameworks. Imported targets are **not** listed as targets in codemodel v2. \cite{discourse-imported}

```python
def target_deps(project, tgt):
    """Return (cmake_targets, external_libs)"""
    cmake_targets = []
    for dep in tgt.get("dependencies", []):
        dep_id = dep["id"]
        cmake_targets.append(project["targets"].get(dep_id, {"id": dep_id}))

    external_libs = []
    link = tgt.get("link") or {}
    for frag in link.get("commandFragments", []):
        if frag.get("role") in ("libraries", "flags", "libraryPath", "frameworkPath", "linker"):
            external_libs.append(frag.get("fragment", ""))

    # Also scan artifacts of deps for actual file paths
    lib_artifacts = []
    for dep_t in cmake_targets:
        for a in dep_t.get("artifacts", []):
            lib_artifacts.append(a["path"])
    return cmake_targets, external_libs, lib_artifacts
```

> Tip: normalize relative artifact paths against the *top-level build dir* (codemodel directory “build” path) before resolving. \cite{ubuntu-manpage}

---

## Recipe: identify **test frameworks** and test info

Use **CTest** JSON; it includes *every* test with command + properties + a backtrace graph to the `add_test()` site. \cite{ctest-json}

```python
import json, subprocess, shlex

def list_ctest(build_dir: str):
    out = subprocess.check_output(["ctest", "--show-only=json-v1"], cwd=build_dir)
    info = json.loads(out)
    tests = info.get("tests", [])
    return info, tests  # info has its own backtraceGraph
```

Framework heuristics:

* If `test["command"][0]` is a GoogleTest exe (common flags: `--gtest_list_tests`) or contains `gtest` in its path/name → GTest.
* Catch2 often accepts `-l`/`--list-tests`.
* Pytest/ctest-driven runs have `python`, `pytest`, or `ctest` wrappers.
* Labels may encode framework (`LABELS` property). All are available in `test["properties"]`. \cite{ctest-json}

You can also **map a test back to a codemodel target** by matching the executable path in `tests[*].command[0]` with any `target["artifacts"][*]["path"]` (after path normalization). Then read that target’s `sources[]` (see below).

---

## Recipe: get **line numbers** (evidence/snippets)

Wherever a JSON object has a `backtrace` integer, resolve it through the **nearest** `backtraceGraph`:

```python
def resolve_backtrace(backtrace_idx: int, btg: dict):
    node = btg["nodes"][backtrace_idx]
    file_idx = node["file"]
    file_path = btg["files"][file_idx]
    line = node.get("line")  # may be absent
    return file_path, line

def target_creation_site(tgt: dict):
    # Example: the 'artifacts' or 'dependencies' may carry backtraces
    btg = tgt.get("backtraceGraph")
    sites = []
    for dep in tgt.get("dependencies", []):
        if "backtrace" in dep and btg:
            sites.append(resolve_backtrace(dep["backtrace"], btg))
    return sites
```

* CTest JSON has its *own* `backtraceGraph` (separate from codemodel). Use it to find the line of the `add_test()` call. \cite{ctest-json}
* Codemodel **directory** and **target** objects embed their own backtrace graphs. \cite{backtrace-graph}

---

## Recipe: extract **output directories** and build artifacts

```python
from pathlib import Path

def target_outputs(project: dict, tgt: dict):
    outs = []
    for art in tgt.get("artifacts", []):
        p = Path(art["path"])
        outs.append(p)
    # If relative, make it absolute using top-level build dir
    # by traversing from codemodel directories if needed.
    return outs, tgt.get("nameOnDisk")
```

Notes:

* `artifacts[].path` is either absolute or relative to the top build dir; `nameOnDisk` is the base filename. \cite{ubuntu-manpage}
* Some generators/platforms may place per-config outputs in subdirs (e.g., `Debug/`, `Release/`). The path in `artifacts` reflects that. \cite{ubuntu-manpage}

---

## Recipe: determine **runtime environment** and **languages**

**Languages per target**

* Read `compileGroups[*].language` (often one group per language). \cite{codemodel-target}

**Compilers, versions, implicit env**

* From `toolchains.toolchains[]`: `compiler.id`, `compiler.version`, `implicit.includeDirectories`/`linkDirectories`/`linkLibraries`. \cite{toolchains}

**OS/Platform & generator**

* From reply index `cmake.version.string`, `cmake.generator.name`, and `cache` entries (`CMAKE_SYSTEM_NAME`, `CMAKE_<LANG>_COMPILER`). \cite{cmake-file-api-manual,cache}

```python
def target_languages(tgt: dict) -> set[str]:
    return { cg.get("language") for cg in tgt.get("compileGroups", []) if cg.get("language") }

def toolchain_summary(project: dict) -> list[dict]:
    tc = project.get("toolchains") or {}
    return tc.get("toolchains", [])
```

**Per-test runtime environment**

* CTest JSON `tests[*].properties` can include `ENVIRONMENT` / `ENVIRONMENT_MODIFICATION`, timeouts, labels, fixtures. \cite{ctest-json}

---

## Recipe: **distinguish test targets** vs regular targets

There isn’t a “test” flag on codemodel targets. Use a robust mapping:

1. Ask CTest for tests → `tests[*]`. \cite{ctest-json}
2. Normalize `tests[*].command[0]` to an absolute path.
3. Match it to any `target["artifacts"][*]["path"]`. That target is **a test executable target**.

Fallback heuristics (if needed):

* IDE “Folder”/group names such as `folder: "tests"` (not guaranteed). \cite{codemodel-target}
* Target name patterns (`.*test.*`, `.*_test`), labels in CTest.
* Link to known testing libs (e.g., `gtest`, `Catch2`) via link fragments. \cite{discourse-imported}

---

## Recipe: list **test-specific source files**

Once you’ve mapped a CTest entry back to its target (above), read `target["sources"]` (and/or grouped via `sourceGroups`). That typically contains the **test sources** for frameworks like GTest/Catch2 (they’re compiled into the executable). \cite{codemodel-target}

```python
def test_sources_for(project: dict, test_exe_path: str):
    # 1) find matching target
    resolved = None
    for t in project["targets"].values():
        for a in t.get("artifacts", []):
            if Path(a["path"]).name == Path(test_exe_path).name or Path(a["path"]) == Path(test_exe_path):
                resolved = t
                break
    if not resolved:
        return []

    # 2) return source file list (flattened)
    out = []
    for s in resolved.get("sources", []):
        path = s.get("path") or s.get("compileGroupIndex")  # path is what we want; guard for shape
        if isinstance(path, str):
            out.append(path)
    return out
```

> Caveat: When a “test” is a driver script that runs another tool (e.g., `python -m pytest`), there may be **no** 1:1 target mapping. In that case, inspect the CTest `command[]` args and `properties[]` to resolve the instrumentation. \cite{ctest-json}

---

## Worked end-to-end example

```python
def analyze(build_dir: str):
    proj = load_reply(build_dir)

    # 1) enumerate targets and languages
    for t in proj["targets"].values():
        langs = target_languages(t)
        outs, name_on_disk = target_outputs(proj, t)
        print(f"[{t['type']}] {t['name']}  langs={sorted(langs)}  out={name_on_disk} -> {', '.join(map(str, outs))}")

    # 2) dependencies and external packages
    for t in proj["targets"].values():
        cmake_deps, ext_frags, dep_artifacts = target_deps(proj, t)
        if cmake_deps or ext_frags:
            print(f"\nDeps for {t['name']}:")
            print("  cmake targets:", [d.get("name", d["id"]) for d in cmake_deps])
            print("  external/link:", ext_frags[:8], "..." if len(ext_frags) > 8 else "")

    # 3) tests + mapping to targets + lines of add_test()
    info, tests = list_ctest(build_dir)
    btg = info.get("backtraceGraph")
    for test in tests:
        cmd0 = (test.get("command") or [""])[0]
        bt_idx = test.get("backtrace")
        loc = resolve_backtrace(bt_idx, btg) if (btg and bt_idx is not None) else None
        print(f"\nCTest: {test['name']}")
        print(f"  cmd: {cmd0}")
        if loc:
            print(f"  defined at: {loc[0]}:{loc[1]}")

        # link back to target (if it’s an exe produced by the build)
        owning = None
        for t in proj["targets"].values():
            if any(Path(a["path"]).name == Path(cmd0).name for a in t.get("artifacts", [])):
                owning = t
                break
        if owning:
            print(f"  => built by target: {owning['name']}")
            print(f"  test sources (first 5): {[s.get('path') for s in owning.get('sources', [])][:5]}")
```

---

## Notes & limitations (so you don’t get surprised)

* **Imported targets** (from `find_package`) are **not** listed as targets in codemodel v2; use **link command fragments** to see their effect on the link line. \cite{discourse-imported}
* Test info is provided by **CTest**, not the codemodel. Use `ctest --show-only=json-v1` for a machine-readable list, including **backtraces** to `add_test()`. \cite{ctest-json}
* Exact fields sometimes gain minor additions across CMake versions (e.g., `workingDirectory` on targets in codemodel ≥ 2.8). Prefer feature-tests in code.


---

### Provenance (key doc cites)

* Object kinds, indices, and examples, including `toolchains` and `cache`. \cite{cmake-file-api-manual,toolchains,cache}
* Codemodel v2 objects and backtrace graph. \cite{codemodel-dir,codemodel-target,backtrace-graph}
* `artifacts`/`nameOnDisk` and path semantics. \cite{ubuntu-manpage}
* Tests JSON (`--show-only=json-v1`), test properties, and backtrace model. \cite{ctest-json}
* Imported target caveat and link fragments for external deps. \cite{discourse-imported}

If you want, I can fold this into your existing file for you and tweak code to your project’s shape (e.g., specific frameworks you expect like GTest/Catch2/QtTest).





-----------------

# more information:

Great — your 6 “what to implement” bullets are exactly the right way to use the File API/CTest model (with one caveat: `ctest --show-only=json-v1` won’t include test `command[]` until the targets are built). \cite{ctest-json} ([cmake.org][1], [GitLab][2])

Below is a drop-in section you can append under the “Advanced Reference & Recipes” you already have.

---

# FAQ: what’s in vs. out of the File API (with docs)

## 1) Runtime environment detection (JVM, .NET, Go, …)

**What the File API gives you:**

* Languages per target via `codemodel(v2) → target.compileGroups[].language` and per-toolchain info via `toolchains(v1) → toolchains[].language/compiler.{id,version,path}`. These reflect CMake **first-class** languages only. \cite{cmake-file-api-manual,toolchains} ([cmake.org][3])
* First-class languages are those CMake recognizes in `project(... LANGUAGES ...)` / `enable_language(...)` (C, CXX, CSharp, CUDA, OBJC, OBJCXX, Fortran, HIP, ISPC, Swift, ASM variants, …). \cite{project,enable\_language} ([cmake.org][4])

**.NET (C#):** CMake has first-class `CSharp` since 3.8, so you will see `compileGroups[].language == "CSharp"` and a matching entry in `toolchains.toolchains[]`. That reliably indicates a .NET/C# target (under VS generators). \cite{relnotes38,project} ([cmake.org][5])

**JVM (Java):** Java is **not** a first-class language; it’s supported via modules like `FindJava` and `UseJava` (e.g., `add_jar`). Consequently, you won’t see `compileGroups[].language == "Java"`. Instead, detect it by:

* looking for `cmakeFiles(v1).inputs[]` that include `UseJava.cmake` / `FindJava.cmake`;
* checking target `artifacts[].path` for `.jar` outputs;
* inspecting CTest `tests[*].command[]` for `java`/`-jar`.
  \cite{usejava,findjava,cmakefiles} ([cmake.org][6])

**Go:** Not first-class either. Teams typically drive Go via custom commands/modules; there’s active community discussion about adding Go as a language, but it isn’t official. Use the same style of heuristics (included modules, `go` in test commands, `.a`/executables built via `go build`). \cite{go-discussion} ([CMake Discourse][7])

**Bottom line:** File API + Toolchains tell you **CMake’s** languages (and compilers). Runtimes like JVM/Go require **heuristics** (included modules, artifact extensions, test commands) plus cache inspection; there’s no single canonical “runtime” field in the File API. \cite{cmake-file-api-manual,cmakefiles} ([cmake.org][3])

## 2) “Which component is this test testing?”

There’s no standard “component-under-test” mapping in File API/CTest. A test is an arbitrary command with optional properties/labels. Recommended approach:

1. Use CTest JSON (`--show-only=json-v1`) for the **test list**, properties, and the `backtraceGraph` to the `add_test()` line. \cite{ctest-json} ([cmake.org][1])
2. Map the test’s command path to a **built target** by matching `tests[*].command[0]` to any `codemodel(v2) → target.artifacts[].path`. That tells you the **executable target** behind the test. \cite{codemodel-target,ubuntu-manpage} ([android.googlesource.com][8])
3. From there, infer “components” by **convention**, e.g., directory/target names, or **labels** (`LABELS` test property) that *you* (or the project) assign. CTest labels are first-class, but purely user-defined. \cite{ctest-labels,add-test} ([cmake.org][9])

> Note: CTest JSON v1 historically omitted some things (e.g., commands before build, or custom properties). Build first, and don’t rely on custom properties being serialized in older versions. \cite{ctest-json,ctest-json-issue} ([cmake.org][1], [GitLab][2])

## 3) “Which package manager (vcpkg, Conan) provided this dep?”

Not encoded in the File API. Use **cache/toolchain** signals:

* **vcpkg:** Projects integrate via the vcpkg **toolchain file**; you’ll usually see

  * `CMAKE_TOOLCHAIN_FILE` set to `.../vcpkg.cmake`;
  * `VCPKG_ROOT`, `VCPKG_TARGET_TRIPLET`, and sometimes `VCPKG_CHAINLOAD_TOOLCHAIN_FILE` in the cache/environment or presets. \cite{vcpkg-cmake,vcpkg-triplets,vcpkg-chainload} ([learn.microsoft.com][10], [Stack Overflow][11])

* **Conan 2:** Generates `conan_toolchain.cmake` (passed via `-DCMAKE_TOOLCHAIN_FILE=conan_toolchain.cmake`) and uses **CMakeDeps** to populate `CMAKE_PREFIX_PATH` with `*Config.cmake` packages. Look for those files/paths in cache and `cmakeFiles.inputs[]`. \cite{conan-toolchain,cmakedeps} ([docs.conan.io][12])

* **Generic `find_package`**: remember CMake has two modes—**Config mode** (`<Pkg>Config.cmake` via `CMAKE_PREFIX_PATH`) and **Module mode** (`Find<Pkg>.cmake` via `CMAKE_MODULE_PATH`). You can sometimes infer “package manager” from where configs were found (vcpkg install tree vs. Conan generators dir), but it’s not standardized. \cite{find-package,mastering-find} ([cmake.org][13])

## 4) “How do I identify the test framework (GTest/Catch2/etc.)?”

There’s **no standard property** in CTest that says “this is GTest” or “this is Catch2”. Use:

* **Official CMake modules/wrappers**:

  * `gtest_discover_tests()` (GoogleTest) registers tests by querying the test binary; you’ll typically see GTest-style flags in `tests[*].command[]` or the helper used in the CMake files. \cite{gtest-module} ([cmake.org][14])
  * `catch_discover_tests()` (Catch2) does the same (`--list-test-names-only`), so the test **command/exe** is your clue. \cite{catch2-cmake} ([android.googlesource.com][15])

* **Labels/Conventions:** Many projects add `LABELS` like `gtest`, `catch2`, `boost.test`, etc. This is project-specific; CTest only defines that labels exist and how to filter them. \cite{ctest-labels} ([cmake.org][9])

> Practical rule: look at `tests[*].command[]` and `LABELS`. If you control the build, standardize labels per framework to make downstream tooling deterministic. \cite{add-test,ctest-json} ([cmake.org][16])

---

## Minimal, doc-backed heuristics you can implement now

```python
def detect_runtime_env(reply: dict, tgt: dict, test_cmd0: str | None) -> dict:
    """
    Return a dict like {"dotnet": bool, "jvm": bool, "go": bool, "signals": {...}}
    Uses only file-api + ctest + cache/toolchain hints (no guessing beyond docs).
    """
    signals = {}
    langs = {cg.get("language") for cg in tgt.get("compileGroups", []) if cg.get("language")}
    signals["languages"] = sorted(langs)

    # .NET (C# is first-class)
    dotnet = "CSharp" in langs

    # Look at cmakeFiles for UseJava/FindJava; jars in artifacts; 'java' in test command
    cmf = reply.get("cmakeFiles") or {}
    inputs = {i.get("path", "") for i in cmf.get("inputs", [])}
    artifacts = [a["path"] for a in tgt.get("artifacts", []) if "path" in a]
    jvm = any(p.endswith(".jar") for p in artifacts) \
          or any("UseJava.cmake" in p or "FindJava.cmake" in p for p in inputs) \
          or (test_cmd0 and (" java" in f" {test_cmd0}" or test_cmd0.endswith(".jar")))

    # Go: no first-class support -> only weak hints from commands/files/modules
    go = test_cmd0 and (" go " in f" {test_cmd0} " or test_cmd0.endswith("go"))

    return {"dotnet": bool(dotnet), "jvm": bool(jvm), "go": bool(go), "signals": signals}
```

These checks align with the docs: CSharp is first-class; Java/Go aren’t (so you won’t see them in `compileGroups.language`) and must be inferred from modules/files/commands. \cite{project,relnotes38,usejava,findjava,go-discussion} ([cmake.org][4], [CMake Discourse][7])

```python
def detect_pkg_manager(cache_entries: dict[str, str]) -> dict:
    """
    Look only at documented knobs used by vcpkg / Conan to integrate with CMake.
    """
    toolchain = cache_entries.get("CMAKE_TOOLCHAIN_FILE", "")
    is_vcpkg = "vcpkg.cmake" in toolchain or "VCPKG_ROOT" in cache_entries or "VCPKG_TARGET_TRIPLET" in cache_entries
    is_conan = "conan_toolchain.cmake" in toolchain

    return {
        "vcpkg": bool(is_vcpkg),
        "conan": bool(is_conan),
        "signals": {k:v for k,v in cache_entries.items() if k in (
            "CMAKE_TOOLCHAIN_FILE", "VCPKG_ROOT", "VCPKG_TARGET_TRIPLET", "VCPKG_CHAINLOAD_TOOLCHAIN_FILE")}
    }
```

These keys (toolchain file, triplets) are the **official** integration points documented by vcpkg and Conan. \cite{vcpkg-cmake,vcpkg-triplets,vcpkg-chainload,conan-toolchain,cmakedeps} ([learn.microsoft.com][10], [Stack Overflow][11], [docs.conan.io][12])

---

## Should you rewrite `CMakeEntrypoint` now?

**Yes — for the 6 core items you listed, you already have complete, doc-supported APIs:**

* Tests: CTest JSON (`--show-only=json-v1`) + backtraceGraph. \cite{ctest-json} ([cmake.org][1])
* External packages: `codemodel(v2) → target.link.commandFragments` (+ artifacts of deps). \cite{codemodel-target,ubuntu-manpage} ([android.googlesource.com][8])
* Lines: resolve `backtrace` via the corresponding `backtraceGraph`. \cite{backtrace-graph,ctest-json} ([cmake.org][3])
* Outputs: `target.artifacts[].path` and `nameOnDisk`. \cite{ubuntu-manpage} ([android.googlesource.com][8])
* Languages: `target.compileGroups[].language` and `toolchains.toolchains[]`. \cite{cmake-file-api-manual,toolchains} ([cmake.org][3])
* Map tests↔targets: match `tests[*].command[0]` to `target.artifacts[].path` (after build). \cite{ctest-json,ubuntu-manpage} ([cmake.org][1], [android.googlesource.com][8])

For the 4 “open” questions (runtimes, components, pkg manager, framework IDs), keep a **separate optional pass** with explicit “heuristic” flags in your RIG (so it’s transparent that these are best-effort). All recommendations above are straight from the official docs.

If you want, I can sketch the `CMakeEntrypoint` patch outline next pass (methods, inputs/outputs, and where each of these lookups lands in your SQLite schema).

---

## References (BibTeX)

```bibtex
@manual{cmake-file-api-manual,
  title  = {cmake-file-api(7) — CMake Documentation},
  year   = {2025},
  url    = {https://cmake.org/cmake/help/latest/manual/cmake-file-api.7.html}
}
@manual{toolchains,
  title  = {Object Kind "toolchains" (v1)},
  year   = {2025},
  url    = {https://cmake.org/cmake/help/latest/manual/cmake-file-api.7.html}
}
@manual{project,
  title  = {project() — Supported LANGUAGES},
  year   = {2025},
  url    = {https://cmake.org/cmake/help/latest/command/project.html}
}
@manual{enable_language,
  title  = {enable_language() — Enable named languages},
  year   = {2025},
  url    = {https://cmake.org/cmake/help/latest/command/enable_language.html}
}
@manual{relnotes38,
  title  = {CMake 3.8 Release Notes — CSharp as first-class language},
  year   = {2017},
  url    = {https://cmake.org/cmake/help/latest/release/3.8.html}
}
@manual{usejava,
  title  = {UseJava — Java support in CMake (add_jar, etc.)},
  year   = {2025},
  url    = {https://cmake.org/cmake/help/latest/module/UseJava.html}
}
@manual{findjava,
  title  = {FindJava — Locate Java runtime/tools},
  year   = {2025},
  url    = {https://cmake.org/cmake/help/latest/module/FindJava.html}
}
@manual{cmakefiles,
  title  = {File API: Object Kind "cmakeFiles"},
  year   = {2025},
  url    = {https://cmake.org/cmake/help/latest/manual/cmake-file-api.7.html}
}
@manual{ctest-json,
  title  = {ctest(1) — --show-only=json-v1 object model},
  year   = {2025},
  url    = {https://cmake.org/cmake/help/latest/manual/ctest.1.html}
}
@online{ctest-json-issue,
  title  = {ctest --show-only=json-v1 may omit commands before build},
  year   = {2023},
  url    = {https://gitlab.kitware.com/cmake/cmake/-/issues/24668}
}
@manual{ctest-labels,
  title  = {LABELS — CTest test property},
  year   = {2025},
  url    = {https://cmake.org/cmake/help/latest/prop_test/LABELS.html}
}
@manual{add-test,
  title  = {add_test — define a test command},
  year   = {2025},
  url    = {https://cmake.org/cmake/help/latest/command/add_test.html}
}
@manual{codemodel-target,
  title  = {File API: codemodel v2 target (artifacts, link, deps, etc.)},
  year   = {2025},
  url    = {https://cmake.org/cmake/help/latest/manual/cmake-file-api.7.html}
}
@online{ubuntu-manpage,
  title  = {Ubuntu manpage: cmake-file-api(7) — details for target fields},
  year   = {2020},
  url    = {https://manpages.ubuntu.com/manpages/focal/man7/cmake-file-api.7.html}
}
@manual{gtest-module,
  title  = {GoogleTest — gtest_discover_tests()},
  year   = {2025},
  url    = {https://cmake.org/cmake/help/latest/module/GoogleTest.html}
}
@online{catch2-cmake,
  title  = {Catch2: cmake integration — catch_discover_tests()},
  year   = {2020},
  url    = {https://android.googlesource.com/platform/external/catch2/+/15150c7/docs/cmake-integration.md}
}
@online{vcpkg-cmake,
  title  = {vcpkg: CMake integration via CMAKE_TOOLCHAIN_FILE},
  year   = {2024},
  url    = {https://learn.microsoft.com/en-us/vcpkg/users/buildsystems/cmake-integration}
}
@online{vcpkg-triplets,
  title  = {vcpkg: Triplet variables (VCPKG_TARGET_TRIPLET, etc.)},
  year   = {2024},
  url    = {https://learn.microsoft.com/en-us/vcpkg/users/triplets}
}
@online{vcpkg-chainload,
  title  = {Using VCPKG_CHAINLOAD_TOOLCHAIN_FILE with vcpkg toolchain},
  year   = {2023},
  url    = {https://stackoverflow.com/questions/74422058/how-to-use-vcpkg-with-clang-on-linux}
}
@manual{conan-toolchain,
  title  = {Conan 2: CMakeToolchain generator (conan_toolchain.cmake)},
  year   = {2025},
  url    = {https://docs.conan.io/2/reference/tools/cmake/cmaketoolchain.html}
}
@manual{cmakedeps,
  title  = {Conan 2: CMakeDeps generator (config packages, prefix paths)},
  year   = {2025},
  url    = {https://docs.conan.io/2/reference/tools/cmake/cmakedeps.html}
}
@online{go-discussion,
  title  = {CMake Discourse: Adding support for Go (not first-class today)},
  year   = {2025},
  url    = {https://discourse.cmake.org/t/adding-support-for-go/13518}
}
```

---

If you’d like, I can fold this into your existing markdown verbatim and add a tiny `CMakeEntrypoint` diff (methods + unit-test shims) next.

[1]: https://cmake.org/cmake/help/latest/manual/ctest.1.html?utm_source=chatgpt.com "ctest(1) — CMake 4.1.1 Documentation"
[2]: https://gitlab.kitware.com/cmake/cmake/-/issues/24668?utm_source=chatgpt.com "ctest --show-only=json-v1 does not contain command ..."
[3]: https://cmake.org/cmake/help/latest/manual/cmake-file-api.7.html?utm_source=chatgpt.com "cmake-file-api(7) — CMake 4.1.1 Documentation"
[4]: https://cmake.org/cmake/help/latest/command/project.html?utm_source=chatgpt.com "project — CMake 4.1.1 Documentation"
[5]: https://cmake.org/cmake/help/latest/release/3.8.html?utm_source=chatgpt.com "CMake 3.8 Release Notes"
[6]: https://cmake.org/cmake/help/latest/module/UseJava.html?utm_source=chatgpt.com "UseJava — CMake 4.1.1 Documentation"
[7]: https://discourse.cmake.org/t/adding-support-for-go/13518?utm_source=chatgpt.com "Adding support for go - Code"
[8]: https://android.googlesource.com/platform/prebuilts/cmake/darwin-x86/%2B/d09ee7574f3e46668b23b3b6efebd0ea75de85b2/share/cmake-3.18/Help/manual/cmake-file-api.7.rst?utm_source=chatgpt.com "cmake-file-api.7.rst"
[9]: https://cmake.org/cmake/help/latest/prop_test/LABELS.html?utm_source=chatgpt.com "LABELS — CMake 4.1.1 Documentation"
[10]: https://learn.microsoft.com/en-us/vcpkg/users/buildsystems/cmake-integration?utm_source=chatgpt.com "vcpkg in CMake projects"
[11]: https://stackoverflow.com/questions/74422058/how-to-use-vcpkg-with-clang-on-linux?utm_source=chatgpt.com "How to use vcpkg with clang on linux?"
[12]: https://docs.conan.io/2/reference/tools/cmake/cmaketoolchain.html?utm_source=chatgpt.com "CMakeToolchain — conan 2.19.1 documentation"
[13]: https://cmake.org/cmake/help/latest/command/find_package.html?utm_source=chatgpt.com "find_package — CMake 4.1.1 Documentation"
[14]: https://cmake.org/cmake/help/latest/module/GoogleTest.html?utm_source=chatgpt.com "GoogleTest — CMake 4.1.1 Documentation"
[15]: https://android.googlesource.com/platform/external/catch2/%2B/15150c7/docs/cmake-integration.md?utm_source=chatgpt.com "CMake integration"
[16]: https://cmake.org/cmake/help/latest/command/add_test.html?utm_source=chatgpt.com "add_test — CMake 4.1.1 Documentation"
