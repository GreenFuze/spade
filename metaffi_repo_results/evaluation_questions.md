You are analyzing the repository “MetaFFI”. Assume Windows x64 Debug.

Return JSON only (a single object). Provide keys "Q01"… "Q14" for the Core (scored). No other keys.

TERMINOLOGY
• component — a named unit in the build (library/executable/JAR or an aggregator).
• aggregator — a grouping/meta component that depends on others and produces no artifact.
• module — a component with sources that may produce an artifact.
• artifact — a produced file (Windows-only here): .exe, .dll, .jar.
• defining_files — files that define or configure the component/artifact (build scripts/manifests/project files).
• dirs — source directory roots associated with a component.
• externals — third-party/system libraries used at build/link time (not repo components).
• declared_in — files where a dependency or external is recorded (build configs, project files, link fragments).
• output_dir — directory that contains the produced artifact.
• dependency graph — directed edges A → B mean “A depends_on B”.
• Windows-only — report only .exe/.dll/.jar (no .so, .dylib).

EVIDENCE POLICY (tool-agnostic)
Use evidence only:
1) Structured build metadata provided at runtime (authoritative).
2) Build-system outputs (target graphs/project files/generated build files/compile–link–test listings) and build logs.
3) Produced artifacts found in the Windows x64 Debug output directories.
If a folder exists (e.g., experimental “honeypots”) but has no build evidence or produced artifacts, treat it as not built and omit it.

GENERAL RULES
• No free text anywhere. Only the fields specified per question are allowed.
• If not findable from the evidence above, return the object with its arrays empty (omit a field only if marked “optional”).
• Use absolute or repo-root–relative paths. Sort arrays lexicographically and deduplicate.
• Use only Windows artifacts (.dll/.exe/.jar). Do not invent values. Omit rather than guess.

--------------------
CORE (Q01–Q14) — Structured fields only
--------------------
Q01  List all built artifacts (.dll, .exe, .jar etc.) that are NOT tests. Include their dependencies and the external packages they use.
{
  "artifacts": [
    { "name": "<string>", "kind": "executable|shared_library|jar", "artifact": "<file>", "output_dir": "<path>",
      "depends_on": ["<component>", ...], "externals": ["<package>", ...], "defining_files": ["<path>", ...] }
  ]
}

Q02  List all MetaFFI XLLR runtime plugins, including XLLR itself. Include their dependencies and external packages.
{
  "xllr_runtimes": [
    { "name": "<string>", "artifact": "<file>", "depends_on": ["<component>", ...],
      "externals": ["<package>", ...], "defining_files": ["<path>", ...] }
  ]
}

Q03  executables — executables with build evidence or produced .exe (including tests).
{
  "executables": [
    { "name": "<string>", "artifact": "<file>", "output_dir": "<path>", "defining_files": ["<path>", ...] }
  ]
}

Q04  IDL plugins — built artifacts only.
{
  "idl_plugins": [
    { "name": "<string>", "artifact": "<file>", "defining_files": ["<path>", ...] }
  ]
}

Q05  Compiler/tooling plugins implemented in Go — built artifacts only.
{
  "go_compilers": [
    { "name": "<string>", "artifact": "<file>", "defining_files": ["<path>", ...] }
  ]
}

Q06  All native components that produce artifacts (executables/shared libraries).
{
  "native": [
    { "name": "<string>", "kind": "executable|shared_library", "artifact": "<file>" }
  ]
}

Q07  VM/JAR artifacts — JARs (and VM outputs) with build evidence or produced files.
{
  "vm_artifacts": [
    { "name": "<string>", "artifact": "<file>", "output_dir": "<path>", "defining_files": ["<path>", ...] }
  ]
}

Q08  List all tests that exercise CDTS.
{
  "cdts_tests": [
    { "name": "<string>", "artifact": "<file>", "defining_files": ["<path>", ...] }
  ]
}

Q09  Which Boost version(s) are used and which Boost libraries?
{
  "boost": {
    "versions": ["<string>", ...],
    "libraries": ["<string>", ...],
    "declared_in": ["<path>", ...]
  }
}

Q10  Map tests → components they exercise — as recorded by build/test metadata.
{
  "test_to_components": [
    { "test": "<string>", "components": ["<component>", ...] }
  ]
}

Q11  go_api_test — declared dependencies and externals (as recorded).
{
  "go_api_test": { "dependencies": ["<component>", ...], "externals": ["<package>", ...] }
}

Q12  xllr.openjdk.jni.bridge — list its dependencies and artifact (verify via dependency evidence and artifact name/path).
{
  "openjdk_jni_bridge": { "depends_on": ["<component>", ...], "artifact": "<file>", "defining_files": ["<path>", ...] }
}

Q13  List all created JARs in MetaFFI.
{
  "jars": [
    { "name": "<string>", "artifact": "<file>", "output_dir": "<path>", "defining_files": ["<path>", ...] }
  ]
}

Q14  List all dynamic libraries that are actually Go runtime binaries.
(Identify runtime .dlls produced by Go, e.g., via build metadata or command evidence.)
{
  "go_runtime_binaries": [
    { "name": "<string>", "artifact": "<file>", "defining_files": ["<path>", ...] }
  ]
}

--------------------
STRICT OUTPUT RULES
--------------------
• Output JSON only (no Markdown, no code fences, no prose).
• If uncertain, leave arrays empty (do not guess).
• Use exact artifact names as evidenced; Windows artifacts only.
• Sort arrays and deduplicate.