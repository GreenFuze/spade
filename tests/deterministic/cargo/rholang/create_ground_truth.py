#!/usr/bin/env python3
"""
Ground truth generator for Cargo rholang test repository.

This script creates the canonical RIG (Repository Information Graph) for the
rholang test repository, which demonstrates:
- Cargo workspace with 21 crates
- Procedural macros for AST generation
- Bidirectional C FFI integration
- Deep dependency chains (depth 11)
- Mixed Rust/C codebase with cross-language dependencies
- Compiler/interpreter architecture
"""

from pathlib import Path

from core.rig import RIG
from core.schemas import (
    Component, TestDefinition, Evidence, ComponentType,
    RepositoryInfo, BuildSystemInfo, ExternalPackage,
    PackageManager
)
from tests.test_utils import test_repos_root


def main() -> None:
    rig = RIG()

    # Repository information
    repo_root = test_repos_root / "cargo" / "rholang"
    rig.set_repository_info(
        RepositoryInfo(
            name="rholang",
            root_path=repo_root,
            build_directory=repo_root / "target",
            output_directory=repo_root / "target" / "release",
            install_directory=None,
            configure_command="cargo build",
            build_command="cargo build --release",
            install_command=None,
            test_command="cargo test",
        )
    )

    # Build system information
    rig.set_build_system_info(
        BuildSystemInfo(
            name="cargo",
            version="1.75+",
            build_type="Release",
        )
    )

    # =========================================================================
    # External Packages (27 total)
    # =========================================================================

    external_packages = []
    package_managers = {
        "logos": PackageManager(name="cargo", package_name="logos"),
        "lalrpop-util": PackageManager(name="cargo", package_name="lalrpop-util"),
        "codespan-reporting": PackageManager(name="cargo", package_name="codespan-reporting"),
        "ariadne": PackageManager(name="cargo", package_name="ariadne"),
        "unicode-xid": PackageManager(name="cargo", package_name="unicode-xid"),
        "dashmap": PackageManager(name="cargo", package_name="dashmap"),
        "indexmap": PackageManager(name="cargo", package_name="indexmap"),
        "smallvec": PackageManager(name="cargo", package_name="smallvec"),
        "bumpalo": PackageManager(name="cargo", package_name="bumpalo"),
        "petgraph": PackageManager(name="cargo", package_name="petgraph"),
        "tokio": PackageManager(name="cargo", package_name="tokio"),
        "async-trait": PackageManager(name="cargo", package_name="async-trait"),
        "serde": PackageManager(name="cargo", package_name="serde"),
        "serde_json": PackageManager(name="cargo", package_name="serde_json"),
        "bincode": PackageManager(name="cargo", package_name="bincode"),
        "anyhow": PackageManager(name="cargo", package_name="anyhow"),
        "thiserror": PackageManager(name="cargo", package_name="thiserror"),
        "libc": PackageManager(name="cargo", package_name="libc"),
        "cc": PackageManager(name="cargo", package_name="cc"),
        "bindgen": PackageManager(name="cargo", package_name="bindgen"),
        "syn": PackageManager(name="cargo", package_name="syn"),
        "quote": PackageManager(name="cargo", package_name="quote"),
        "proc-macro2": PackageManager(name="cargo", package_name="proc-macro2"),
        "clap": PackageManager(name="cargo", package_name="clap"),
        "tracing": PackageManager(name="cargo", package_name="tracing"),
        "tracing-subscriber": PackageManager(name="cargo", package_name="tracing-subscriber"),
        "criterion": PackageManager(name="cargo", package_name="criterion"),
    }

    for name, pm in package_managers.items():
        external_packages.append(ExternalPackage(name=name, package_manager=pm))

    # Reference external packages by index
    logos_pkg = external_packages[0]
    lalrpop_pkg = external_packages[1]
    codespan_pkg = external_packages[2]
    ariadne_pkg = external_packages[3]
    unicode_xid_pkg = external_packages[4]
    dashmap_pkg = external_packages[5]
    indexmap_pkg = external_packages[6]
    smallvec_pkg = external_packages[7]
    bumpalo_pkg = external_packages[8]
    petgraph_pkg = external_packages[9]
    tokio_pkg = external_packages[10]
    async_trait_pkg = external_packages[11]
    serde_pkg = external_packages[12]
    serde_json_pkg = external_packages[13]
    bincode_pkg = external_packages[14]
    anyhow_pkg = external_packages[15]
    thiserror_pkg = external_packages[16]
    libc_pkg = external_packages[17]
    cc_pkg = external_packages[18]
    bindgen_pkg = external_packages[19]
    syn_pkg = external_packages[20]
    quote_pkg = external_packages[21]
    proc_macro2_pkg = external_packages[22]
    clap_pkg = external_packages[23]
    tracing_pkg = external_packages[24]
    tracing_sub_pkg = external_packages[25]
    criterion_pkg = external_packages[26]

    # =========================================================================
    # Tier 0 - Foundation (Depth 0, 3 components)
    # =========================================================================

    # Component 1: common-types
    common_types = Component(
        name="common-types",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="rust",
        relative_path=Path("target/release/libcommon_types.rlib"),
        source_files=[
            Path("crates/common-types/src/lib.rs"),
            Path("crates/common-types/src/span.rs"),
            Path("crates/common-types/src/symbol.rs"),
        ],
        external_packages=[serde_pkg, serde_json_pkg],
        evidence=[Evidence(line=["crates/common-types/Cargo.toml:2"])],
        locations=[],
    )
    rig.add_component(common_types)

    # Component 2: error-reporting
    error_reporting = Component(
        name="error-reporting",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="rust",
        relative_path=Path("target/release/liberror_reporting.rlib"),
        source_files=[
            Path("crates/error-reporting/src/lib.rs"),
            Path("crates/error-reporting/src/diagnostic.rs"),
        ],
        external_packages=[codespan_pkg, ariadne_pkg, thiserror_pkg],
        evidence=[Evidence(line=["crates/error-reporting/Cargo.toml:2"])],
        locations=[],
    )
    rig.add_component(error_reporting)

    # Component 3: rholang-macros (proc-macro)
    rholang_macros = Component(
        name="rholang-macros",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="rust",
        relative_path=Path("target/release/librholang_macros.so"),
        source_files=[
            Path("crates/rholang-macros/src/lib.rs"),
            Path("crates/rholang-macros/src/ast_node.rs"),
            Path("crates/rholang-macros/src/visitor.rs"),
        ],
        external_packages=[syn_pkg, quote_pkg, proc_macro2_pkg],
        evidence=[Evidence(line=["crates/rholang-macros/Cargo.toml:2"])],
        locations=[],
    )
    rig.add_component(rholang_macros)

    # =========================================================================
    # Tier 1 - Frontend (Depth 1-2, 4 components)
    # =========================================================================

    # Component 4: lexer
    lexer = Component(
        name="lexer",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="rust",
        relative_path=Path("target/release/liblexer.rlib"),
        source_files=[
            Path("crates/lexer/src/lib.rs"),
            Path("crates/lexer/src/token.rs"),
            Path("crates/lexer/src/scanner.rs"),
        ],
        external_packages=[logos_pkg, unicode_xid_pkg],
        depends_on=[common_types, error_reporting],
        evidence=[Evidence(line=["crates/lexer/Cargo.toml:2"])],
        locations=[],
    )
    rig.add_component(lexer)

    # Component 5: parser
    parser = Component(
        name="parser",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="rust",
        relative_path=Path("target/release/libparser.rlib"),
        source_files=[
            Path("crates/parser/src/lib.rs"),
            Path("crates/parser/src/expr.rs"),
            Path("crates/parser/src/stmt.rs"),
            Path("crates/parser/src/decl.rs"),
        ],
        external_packages=[lalrpop_pkg, smallvec_pkg],
        depends_on=[lexer, common_types, error_reporting],
        evidence=[Evidence(line=["crates/parser/Cargo.toml:2"])],
        locations=[],
    )
    rig.add_component(parser)

    # Component 6: ast
    ast = Component(
        name="ast",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="rust",
        relative_path=Path("target/release/libast.rlib"),
        source_files=[
            Path("crates/ast/src/lib.rs"),
            Path("crates/ast/src/nodes.rs"),
            Path("crates/ast/src/visitor.rs"),
            Path("crates/ast/src/pretty_print.rs"),
        ],
        external_packages=[serde_pkg, indexmap_pkg],
        depends_on=[common_types, error_reporting, rholang_macros],
        evidence=[Evidence(line=["crates/ast/Cargo.toml:2"])],
        locations=[],
    )
    rig.add_component(ast)

    # Component 7: span-interner
    span_interner = Component(
        name="span-interner",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="rust",
        relative_path=Path("target/release/libspan_interner.rlib"),
        source_files=[
            Path("crates/span-interner/src/lib.rs"),
            Path("crates/span-interner/src/interner.rs"),
        ],
        external_packages=[dashmap_pkg, indexmap_pkg],
        depends_on=[common_types],
        evidence=[Evidence(line=["crates/span-interner/Cargo.toml:2"])],
        locations=[],
    )
    rig.add_component(span_interner)

    # =========================================================================
    # Tier 2 - Analysis (Depth 3-6, 4 components)
    # =========================================================================

    # Component 8: semantic-analyzer (only DIRECT dependencies)
    semantic_analyzer = Component(
        name="semantic-analyzer",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="rust",
        relative_path=Path("target/release/libsemantic_analyzer.rlib"),
        source_files=[
            Path("crates/semantic-analyzer/src/lib.rs"),
            Path("crates/semantic-analyzer/src/scope.rs"),
            Path("crates/semantic-analyzer/src/resolver.rs"),
        ],
        external_packages=[petgraph_pkg, indexmap_pkg],
        depends_on=[ast, parser],  # Direct deps only
        evidence=[Evidence(line=["crates/semantic-analyzer/Cargo.toml:2"])],
        locations=[],
    )
    rig.add_component(semantic_analyzer)

    # Component 9: type-checker (only DIRECT dependencies)
    type_checker = Component(
        name="type-checker",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="rust",
        relative_path=Path("target/release/libtype_checker.rlib"),
        source_files=[
            Path("crates/type-checker/src/lib.rs"),
            Path("crates/type-checker/src/inference.rs"),
            Path("crates/type-checker/src/unification.rs"),
        ],
        external_packages=[petgraph_pkg, smallvec_pkg],
        depends_on=[ast, semantic_analyzer],  # Direct deps only
        evidence=[Evidence(line=["crates/type-checker/Cargo.toml:2"])],
        locations=[],
    )
    rig.add_component(type_checker)

    # Component 10: ir-gen (only DIRECT dependencies)
    ir_gen = Component(
        name="ir-gen",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="rust",
        relative_path=Path("target/release/libir_gen.rlib"),
        source_files=[
            Path("crates/ir-gen/src/lib.rs"),
            Path("crates/ir-gen/src/lower.rs"),
            Path("crates/ir-gen/src/ir.rs"),
        ],
        external_packages=[indexmap_pkg, smallvec_pkg],
        depends_on=[type_checker],  # Direct dep only
        evidence=[Evidence(line=["crates/ir-gen/Cargo.toml:2"])],
        locations=[],
    )
    rig.add_component(ir_gen)

    # Component 11: optimizer (only DIRECT dependencies)
    optimizer = Component(
        name="optimizer",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="rust",
        relative_path=Path("target/release/liboptimizer.rlib"),
        source_files=[
            Path("crates/optimizer/src/lib.rs"),
            Path("crates/optimizer/src/passes.rs"),
            Path("crates/optimizer/src/dead_code.rs"),
            Path("crates/optimizer/src/constant_folding.rs"),
        ],
        external_packages=[petgraph_pkg, smallvec_pkg],
        depends_on=[ir_gen],  # Direct dep only
        evidence=[Evidence(line=["crates/optimizer/Cargo.toml:2"])],
        locations=[],
    )
    rig.add_component(optimizer)

    # =========================================================================
    # Tier 3 - Backends & Runtime (Depth 7-9, 5 components)
    # =========================================================================

    # Component 12: codegen-c (only DIRECT dependencies)
    codegen_c = Component(
        name="codegen-c",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="rust",
        relative_path=Path("target/release/libcodegen_c.rlib"),
        source_files=[
            Path("crates/codegen-c/src/lib.rs"),
            Path("crates/codegen-c/src/emitter.rs"),
            Path("crates/codegen-c/src/c_types.rs"),
        ],
        external_packages=[indexmap_pkg],
        depends_on=[optimizer],  # Direct dep only
        evidence=[Evidence(line=["crates/codegen-c/Cargo.toml:2"])],
        locations=[],
    )
    rig.add_component(codegen_c)

    # Component 13: codegen-bytecode (only DIRECT dependencies)
    codegen_bytecode = Component(
        name="codegen-bytecode",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="rust",
        relative_path=Path("target/release/libcodegen_bytecode.rlib"),
        source_files=[
            Path("crates/codegen-bytecode/src/lib.rs"),
            Path("crates/codegen-bytecode/src/instruction.rs"),
            Path("crates/codegen-bytecode/src/assembler.rs"),
        ],
        external_packages=[bincode_pkg, serde_pkg],
        depends_on=[optimizer],  # Direct dep only
        evidence=[Evidence(line=["crates/codegen-bytecode/Cargo.toml:2"])],
        locations=[],
    )
    rig.add_component(codegen_bytecode)

    # Component 14: vm-runtime (only DIRECT dependencies)
    vm_runtime = Component(
        name="vm-runtime",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="rust",
        relative_path=Path("target/release/libvm_runtime.rlib"),
        source_files=[
            Path("crates/vm-runtime/src/lib.rs"),
            Path("crates/vm-runtime/src/vm.rs"),
            Path("crates/vm-runtime/src/stack.rs"),
            Path("crates/vm-runtime/src/heap.rs"),
        ],
        external_packages=[bumpalo_pkg, dashmap_pkg],
        depends_on=[codegen_bytecode, common_types],  # Direct deps only
        evidence=[Evidence(line=["crates/vm-runtime/Cargo.toml:2"])],
        locations=[],
    )
    rig.add_component(vm_runtime)

    # Component 15: ffi-bridge (with C FFI - only DIRECT dependencies)
    ffi_bridge = Component(
        name="ffi-bridge",
        type=ComponentType.SHARED_LIBRARY,
        programming_language="rust",
        relative_path=Path("target/release/libffi_bridge.so"),
        source_files=[
            Path("crates/ffi-bridge/src/lib.rs"),
            Path("crates/ffi-bridge/src/native.c"),
            Path("crates/ffi-bridge/build.rs"),
            Path("crates/ffi-bridge/include/rholang.h"),
        ],
        external_packages=[libc_pkg, cc_pkg, bindgen_pkg],
        depends_on=[vm_runtime],  # Direct dep only
        evidence=[Evidence(line=["crates/ffi-bridge/Cargo.toml:2"])],
        locations=[],
    )
    rig.add_component(ffi_bridge)

    # Component 16: stdlib (only DIRECT dependencies)
    stdlib = Component(
        name="stdlib",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="rust",
        relative_path=Path("target/release/libstdlib.rlib"),
        source_files=[
            Path("crates/stdlib/src/lib.rs"),
            Path("crates/stdlib/src/collections.rs"),
            Path("crates/stdlib/src/io.rs"),
            Path("crates/stdlib/src/string.rs"),
        ],
        external_packages=[indexmap_pkg, smallvec_pkg],
        depends_on=[vm_runtime],  # Direct dep only
        evidence=[Evidence(line=["crates/stdlib/Cargo.toml:2"])],
        locations=[],
    )
    rig.add_component(stdlib)

    # =========================================================================
    # Tier 4 - Tools (Depth 5-10, 3 components)
    # =========================================================================

    # Component 17: rholang-cli (only DIRECT dependencies)
    rholang_cli = Component(
        name="rholang-cli",
        type=ComponentType.EXECUTABLE,
        programming_language="rust",
        relative_path=Path("target/release/rholang-cli.exe"),
        source_files=[
            Path("crates/rholang-cli/src/main.rs"),
            Path("crates/rholang-cli/src/compile.rs"),
        ],
        external_packages=[clap_pkg, anyhow_pkg, tracing_pkg, tracing_sub_pkg],
        depends_on=[codegen_c, codegen_bytecode],  # Direct deps only
        evidence=[Evidence(line=["crates/rholang-cli/Cargo.toml:2"])],
        locations=[],
    )
    rig.add_component(rholang_cli)

    # Component 18: repl (only DIRECT dependencies)
    repl = Component(
        name="repl",
        type=ComponentType.EXECUTABLE,
        programming_language="rust",
        relative_path=Path("target/release/repl.exe"),
        source_files=[
            Path("crates/repl/src/main.rs"),
            Path("crates/repl/src/eval.rs"),
        ],
        external_packages=[clap_pkg, anyhow_pkg],
        depends_on=[vm_runtime, stdlib],  # Direct deps only
        evidence=[Evidence(line=["crates/repl/Cargo.toml:2"])],
        locations=[],
    )
    rig.add_component(repl)

    # Component 19: lsp-server (only DIRECT dependencies)
    lsp_server = Component(
        name="lsp-server",
        type=ComponentType.EXECUTABLE,
        programming_language="rust",
        relative_path=Path("target/release/lsp-server.exe"),
        source_files=[
            Path("crates/lsp-server/src/main.rs"),
            Path("crates/lsp-server/src/protocol.rs"),
            Path("crates/lsp-server/src/handlers.rs"),
        ],
        external_packages=[tokio_pkg, async_trait_pkg, serde_json_pkg, anyhow_pkg],
        depends_on=[type_checker, span_interner],  # Direct deps only
        evidence=[Evidence(line=["crates/lsp-server/Cargo.toml:2"])],
        locations=[],
    )
    rig.add_component(lsp_server)

    # =========================================================================
    # Tier 5 - Testing & Utilities (Depth 9-11, 2 components)
    # =========================================================================

    # Component 20: integration-tests (only DIRECT dependencies)
    integration_tests = Component(
        name="integration-tests",
        type=ComponentType.EXECUTABLE,
        programming_language="rust",
        relative_path=Path("target/release/integration-tests.exe"),
        source_files=[
            Path("crates/integration-tests/src/main.rs"),
            Path("crates/integration-tests/src/test_runner.rs"),
            Path("crates/integration-tests/tests/compile_tests.rs"),
        ],
        external_packages=[anyhow_pkg],
        depends_on=[rholang_cli, repl, ffi_bridge, common_types],  # Direct deps only
        evidence=[Evidence(line=["crates/integration-tests/Cargo.toml:2"])],
        locations=[],
    )
    rig.add_component(integration_tests)

    # Component 21: benchmark-suite (only DIRECT dependencies)
    benchmark_suite = Component(
        name="benchmark-suite",
        type=ComponentType.EXECUTABLE,
        programming_language="rust",
        relative_path=Path("target/release/benchmark-suite.exe"),
        source_files=[
            Path("crates/benchmark-suite/src/main.rs"),
            Path("crates/benchmark-suite/benches/lexer_bench.rs"),
            Path("crates/benchmark-suite/benches/parser_bench.rs"),
        ],
        external_packages=[criterion_pkg, anyhow_pkg],
        depends_on=[semantic_analyzer, vm_runtime],  # Direct deps only
        evidence=[Evidence(line=["crates/benchmark-suite/Cargo.toml:2"])],
        locations=[],
    )
    rig.add_component(benchmark_suite)

    # List of all components for complexity calculation
    all_components = [
        common_types, error_reporting, rholang_macros,
        lexer, parser, ast, span_interner,
        semantic_analyzer, type_checker, ir_gen, optimizer,
        codegen_c, codegen_bytecode, vm_runtime, ffi_bridge, stdlib,
        rholang_cli, repl, lsp_server,
        integration_tests, benchmark_suite
    ]

    # =========================================================================
    # Tests
    # =========================================================================

    # Test 1: Lexer Unit Tests (via library component)
    test_lexer = TestDefinition(
        name="Lexer Unit Tests",
        test_executable_component=lexer,  # Tests run via the library
        test_framework="rust",
        source_files=[Path("crates/lexer/src/lib.rs")],
        evidence=[Evidence(line=["crates/lexer/src/lib.rs:28"])]
    )
    rig.add_test(test_lexer)

    # Test 2: Parser Unit Tests (via library component)
    test_parser = TestDefinition(
        name="Parser Unit Tests",
        test_executable_component=parser,  # Tests run via the library
        test_framework="rust",
        source_files=[Path("crates/parser/src/lib.rs")],
        evidence=[Evidence(line=["crates/parser/src/lib.rs:17"])]
    )
    rig.add_test(test_parser)

    # Test 3: Integration Tests
    test_integration = TestDefinition(
        name="Integration Tests",
        test_executable_component=integration_tests,
        test_framework="rust",
        source_files=[Path("crates/integration-tests/tests/compile_tests.rs")],
        evidence=[Evidence(line=["crates/integration-tests/tests/compile_tests.rs:3"])]
    )
    rig.add_test(test_integration)

    # Test 4: Performance Benchmarks
    test_benchmarks = TestDefinition(
        name="Performance Benchmarks",
        test_executable_component=benchmark_suite,
        test_framework="criterion",
        source_files=[
            Path("crates/benchmark-suite/benches/lexer_bench.rs"),
            Path("crates/benchmark-suite/benches/parser_bench.rs"),
        ],
        evidence=[Evidence(line=["crates/benchmark-suite/Cargo.toml:16"])]
    )
    rig.add_test(test_benchmarks)

    # =========================================================================
    # Validation and save
    # =========================================================================

    # Validate RIG
    validation_errors = rig.validate()
    if validation_errors:
        print("RIG Validation Errors:")
        for error in validation_errors:
            print(f"  - {error}")
        raise ValueError("RIG validation failed")

    # Save to SQLite
    sqlite_path = Path(__file__).parent / "rholang_ground_truth.sqlite3"
    rig.save(sqlite_path)
    print(f"[OK] Saved RIG to: {sqlite_path}")

    # Save to JSON
    json_path = Path(__file__).parent / "rholang_ground_truth.json"
    rig_json_ground_truth = rig.generate_prompts_json_data()
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(rig_json_ground_truth)
    print(f"[OK] Saved JSON to: {json_path}")

    # Reload and compare (determinism check)
    rig_loaded = RIG.load(sqlite_path)
    diff_text = rig.compare(rig_loaded)
    if diff_text:
        raise ValueError(f"Loaded RIG does not match original:\n{diff_text}")
    print("[OK] Determinism check passed")

    # =========================================================================
    # Complexity calculation
    # =========================================================================

    component_count = len(all_components)
    programming_languages = set(c.programming_language for c in all_components)
    programming_language_count = len(programming_languages)

    external_packages_set = set()
    for c in all_components:
        external_packages_set.update(pkg.name for pkg in c.external_packages)
    external_package_count = len(external_packages_set)

    # Calculate max dependency depth
    def get_depth(component, memo=None):
        if memo is None:
            memo = {}
        if component.name in memo:
            return memo[component.name]
        if not component.depends_on:
            memo[component.name] = 0
            return 0
        max_dep_depth = max(get_depth(dep, memo) for dep in component.depends_on)
        memo[component.name] = max_dep_depth + 1
        return max_dep_depth + 1

    max_dependency_depth = max(get_depth(c) for c in all_components)

    aggregator_count = 0  # No aggregators in this workspace

    has_cross_language_dependencies = len(programming_languages) > 1

    # Calculate raw score
    raw_score = (
        component_count * 2 +
        programming_language_count * 10 +
        external_package_count * 3 +
        max_dependency_depth * 8 +
        aggregator_count * 5 +
        (15 if has_cross_language_dependencies else 0)
    )

    # Normalize to 0-100 scale (229 is the maximum from metaffi)
    normalized_score = (raw_score / 229) * 100

    print("\n" + "=" * 70)
    print("COMPLEXITY ANALYSIS")
    print("=" * 70)
    print(f"Components:              {component_count:>3} × 2  = {component_count * 2:>3}")
    print(f"Programming Languages:   {programming_language_count:>3} × 10 = {programming_language_count * 10:>3}")
    print(f"  Languages: {', '.join(sorted(programming_languages))}")
    print(f"External Packages:       {external_package_count:>3} × 3  = {external_package_count * 3:>3}")
    print(f"  Packages: {', '.join(sorted(list(external_packages_set)[:10]))}...")
    print(f"Max Dependency Depth:    {max_dependency_depth:>3} × 8  = {max_dependency_depth * 8:>3}")
    print(f"Aggregators:             {aggregator_count:>3} × 5  = {aggregator_count * 5:>3}")
    print(f"Cross-language:         {'Yes' if has_cross_language_dependencies else 'No':>4} × 1  = {15 if has_cross_language_dependencies else 0:>3}")
    print("-" * 70)
    print(f"RAW SCORE:                      = {raw_score:>3}")
    print(f"NORMALIZED SCORE:               = {normalized_score:>6.2f}")
    print("=" * 70)

    # Verify target complexity
    if 90 <= normalized_score <= 95:
        print(f"[OK] Complexity score {normalized_score:.2f} is within target range (90-95)")
    else:
        print(f"[WARNING] Complexity score {normalized_score:.2f} is outside target range (90-95)")

    print("\n[OK] Ground truth generated successfully!")


if __name__ == "__main__":
    main()
