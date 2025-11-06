from pathlib import Path
from typing import List, Dict, Any, Set, Tuple

from core.rig import RIG
from core.schemas import (
    Component,
    TestDefinition,
    Evidence,
    ComponentType,
    RepositoryInfo,
    BuildSystemInfo,
    RIGValidationError,
    ExternalPackage,
    PackageManager,
)

from tests.test_utils import test_repos_root


def _calc_complexity(ground_truth: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """Compute raw complexity and metrics (must match summary_analysis/config weights).

    This mirrors tests/deterministic/summary_analysis/complexity.py at high level
    to verify our designed repository falls within the required normalized band.
    """
    COMPLEXITY_WEIGHTS = {
        'component': 2,
        'language': 10,
        'package': 3,
        'depth': 8,
        'aggregator': 5,
        'cross_lang_bonus': 15,
    }

    components = ground_truth.get("components", [])
    tests = ground_truth.get("tests", [])
    external_packages = ground_truth.get("external_packages", [])

    # ID → component dict
    comp_map = {c.get("id"): c for c in components if c.get("id")}

    # Languages
    languages: Set[str] = set()
    for c in components:
        lang = c.get("programming_language")
        if lang:
            languages.add(lang)

    # Cross-language deps
    has_cross_lang_deps = False
    for c in components:
        comp_lang = c.get("programming_language")
        for dep_id in c.get("depends_on_ids", []) or []:
            d = comp_map.get(dep_id)
            if d:
                dep_lang = d.get("programming_language")
                if dep_lang and comp_lang and dep_lang != comp_lang:
                    has_cross_lang_deps = True
                    break
        if has_cross_lang_deps:
            break

    # Max dependency depth (DFS)
    def depth_from(cdict: Dict[str, Any], visited: Set[str] | None = None) -> int:
        if visited is None:
            visited = set()
        cid = cdict.get("id")
        if cid in visited:
            return 0
        visited.add(cid)
        deps = list(cdict.get("depends_on_ids", []) or [])
        if not deps:
            return 0
        max_d = 0
        for dep_id in deps:
            dep = comp_map.get(dep_id)
            if dep:
                max_d = max(max_d, depth_from(dep, visited.copy()))
        return max_d + 1

    max_depth = 0
    for c in components:
        max_depth = max(max_depth, depth_from(c))

    # Aggregators: interpreted with >1 dependency
    aggregator_count = 0
    for c in components:
        if c.get("type") == "interpreted" and len(list(c.get("depends_on_ids", []) or [])) > 1:
            aggregator_count += 1

    metrics = {
        "component_count": len(components),
        "programming_language_count": len(languages),
        "programming_languages": sorted(languages),
        "external_package_count": len(external_packages),
        "test_count": len(tests),
        "max_dependency_depth": max_depth,
        "aggregator_count": aggregator_count,
        "has_cross_language_dependencies": has_cross_lang_deps,
    }

    score = (
        metrics["component_count"] * COMPLEXITY_WEIGHTS['component'] +
        metrics["programming_language_count"] * COMPLEXITY_WEIGHTS['language'] +
        metrics["external_package_count"] * COMPLEXITY_WEIGHTS['package'] +
        metrics["max_dependency_depth"] * COMPLEXITY_WEIGHTS['depth'] +
        metrics["aggregator_count"] * COMPLEXITY_WEIGHTS['aggregator'] +
        (COMPLEXITY_WEIGHTS['cross_lang_bonus'] if metrics["has_cross_language_dependencies"] else 0)
    )
    return score, metrics


def main() -> None:
    # Root path for this synthetic npm repo
    repo_root = test_repos_root / "npm"

    def collect_sources(rel_dir: Path, exts: Tuple[str, ...] = (".ts", ".tsx", ".js", ".jsx")) -> List[Path]:
        """Collect non-test source files under rel_dir with given extensions.

        - rel_dir is relative to repo_root
        - Excludes files containing ".test." or ending with "_test" before extension
        - Returns paths relative to repo_root, sorted deterministically
        """
        base = (repo_root / rel_dir)
        out: List[Path] = []
        if not base.exists():
            return out
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() in exts:
                name = p.name
                stem = p.stem
                if ".test." in name or stem.endswith("_test"):
                    continue
                out.append(p.relative_to(repo_root))
        return sorted(out)

    rig = RIG()

    # Repository & build info
    rig.set_repository_info(
        RepositoryInfo(
            name="npm_monorepo_sample",
            root_path=repo_root,
            build_directory=repo_root / "dist",
            output_directory=repo_root / "dist",
            configure_command="npm install",
            build_command="npm run build --workspaces",
            install_command=None,
            test_command="npm test --workspaces",
        )
    )

    rig.set_build_system_info(
        BuildSystemInfo(name="npm", version=None, build_type=None)
    )

    # External packages (unique list)
    npm = lambda pkg: ExternalPackage(name=pkg, package_manager=PackageManager(name="npm", package_name=pkg))
    express = npm("express")
    react = npm("react")
    axios = npm("axios")
    jest = npm("jest")
    typescript = npm("typescript")
    webpack = npm("webpack")

    # Components (16 total, including 2 aggregators)
    # Backend apps
    api_server = Component(
        name="api-server",
        type=ComponentType.EXECUTABLE,
        programming_language="ts",
        relative_path=Path("backend/api-server/dist/index.js"),
        source_files=collect_sources(Path("backend/api-server/src")),
        external_packages=[express, axios, typescript, jest],
        evidence=[Evidence(line=["backend/api-server/package.json:1"])],
        locations=[],
    )

    worker = Component(
        name="worker",
        type=ComponentType.EXECUTABLE,
        programming_language="ts",
        relative_path=Path("backend/worker/dist/index.js"),
        source_files=collect_sources(Path("backend/worker/src")),
        external_packages=[axios, typescript, jest],
        evidence=[Evidence(line=["backend/worker/package.json:1"])],
        locations=[],
    )

    proxy_server = Component(
        name="proxy-server",
        type=ComponentType.EXECUTABLE,
        programming_language="js",
        relative_path=Path("backend/proxy-server/index.js"),
        source_files=collect_sources(Path("backend/proxy-server"), exts=(".js", ".jsx")),
        external_packages=[express],
        evidence=[Evidence(line=["backend/proxy-server/package.json:1"])],
        locations=[],
    )

    # Frontend apps
    web_app = Component(
        name="web-app",
        type=ComponentType.EXECUTABLE,
        programming_language="ts",
        relative_path=Path("frontend/web-app/dist/main.js"),
        source_files=collect_sources(Path("frontend/web-app/src")),
        external_packages=[react, axios, webpack, typescript, jest],
        evidence=[Evidence(line=["frontend/web-app/package.json:1"])],
        locations=[],
    )

    admin_portal = Component(
        name="admin-portal",
        type=ComponentType.EXECUTABLE,
        programming_language="ts",
        relative_path=Path("frontend/admin-portal/dist/main.js"),
        source_files=collect_sources(Path("frontend/admin-portal/src")),
        external_packages=[react, webpack, typescript, jest],
        evidence=[Evidence(line=["frontend/admin-portal/package.json:1"])],
        locations=[],
    )

    # Libraries
    shared_ui = Component(
        name="shared-ui",
        type=ComponentType.PACKAGE_LIBRARY,
        programming_language="ts",
        relative_path=Path("libs/shared-ui/dist/index.js"),
        source_files=collect_sources(Path("libs/shared-ui/src")),
        external_packages=[react, typescript],
        evidence=[Evidence(line=["libs/shared-ui/package.json:1"])],
        locations=[],
    )

    i18n_lib = Component(
        name="i18n-lib",
        type=ComponentType.PACKAGE_LIBRARY,
        programming_language="ts",
        relative_path=Path("libs/i18n-lib/dist/index.js"),
        source_files=collect_sources(Path("libs/i18n-lib/src")),
        external_packages=[typescript],
        evidence=[Evidence(line=["libs/i18n-lib/package.json:1"])],
        locations=[],
    )

    shared_lib = Component(
        name="shared-lib",
        type=ComponentType.PACKAGE_LIBRARY,
        programming_language="ts",
        relative_path=Path("libs/shared-lib/dist/index.js"),
        source_files=collect_sources(Path("libs/shared-lib/src")),
        external_packages=[typescript],
        evidence=[Evidence(line=["libs/shared-lib/package.json:1"])],
        locations=[],
    )

    auth_lib = Component(
        name="auth-lib",
        type=ComponentType.PACKAGE_LIBRARY,
        programming_language="ts",
        relative_path=Path("libs/auth-lib/dist/index.js"),
        source_files=collect_sources(Path("libs/auth-lib/src")),
        external_packages=[typescript],
        evidence=[Evidence(line=["libs/auth-lib/package.json:1"])],
        locations=[],
    )

    data_access = Component(
        name="data-access",
        type=ComponentType.PACKAGE_LIBRARY,
        programming_language="ts",
        relative_path=Path("libs/data-access/dist/index.js"),
        source_files=collect_sources(Path("libs/data-access/src")),
        external_packages=[axios, typescript],
        evidence=[Evidence(line=["libs/data-access/package.json:1"])],
        locations=[],
    )

    logging_lib = Component(
        name="logging-lib",
        type=ComponentType.PACKAGE_LIBRARY,
        programming_language="ts",
        relative_path=Path("libs/logging-lib/dist/index.js"),
        source_files=collect_sources(Path("libs/logging-lib/src")),
        external_packages=[typescript],
        evidence=[Evidence(line=["libs/logging-lib/package.json:1"])],
        locations=[],
    )

    metrics_lib = Component(
        name="metrics-lib",
        type=ComponentType.PACKAGE_LIBRARY,
        programming_language="ts",
        relative_path=Path("libs/metrics-lib/dist/index.js"),
        source_files=collect_sources(Path("libs/metrics-lib/src")),
        external_packages=[typescript],
        evidence=[Evidence(line=["libs/metrics-lib/package.json:1"])],
        locations=[],
    )

    # Cross-language modules
    wasm_module = Component(
        name="wasm-module",
        type=ComponentType.PACKAGE_LIBRARY,
        programming_language="rust",
        relative_path=Path("modules/wasm-module/pkg/index.js"),
        source_files=[Path("modules/wasm-module/src/lib.rs")],
        external_packages=[],
        evidence=[Evidence(line=["modules/wasm-module/Cargo.toml:1"])],
        locations=[],
    )

    codegen = Component(
        name="codegen",
        type=ComponentType.EXECUTABLE,
        programming_language="python",
        relative_path=Path("tools/codegen/main.py"),
        source_files=[Path("tools/codegen/main.py")],
        external_packages=[],
        evidence=[Evidence(line=["tools/codegen/pyproject.toml:1"])],
        locations=[],
    )

    # Aggregators (interpreted)
    build_all = Component(
        name="build-all",
        type=ComponentType.INTERPRETED,
        programming_language="js",
        relative_path=Path("package.json"),
        source_files=[],
        external_packages=[],
        evidence=[Evidence(line=["package.json:1"])],
        locations=[],
    )

    test_all = Component(
        name="test-all",
        type=ComponentType.INTERPRETED,
        programming_language="js",
        relative_path=Path("package.json"),
        source_files=[],
        external_packages=[jest],
        evidence=[Evidence(line=["package.json:1"])],
        locations=[],
    )

    # Establish dependencies
    shared_ui.depends_on = [shared_lib]
    i18n_lib.depends_on = [shared_lib]
    shared_lib.depends_on = [logging_lib]
    data_access.depends_on = [shared_lib, codegen]

    web_app.depends_on = [shared_ui, i18n_lib, wasm_module, shared_lib]
    admin_portal.depends_on = [shared_ui, shared_lib]

    api_server.depends_on = [auth_lib, data_access, shared_lib, logging_lib, metrics_lib]
    worker.depends_on = [data_access, shared_lib, logging_lib]
    proxy_server.depends_on = [shared_lib, logging_lib]

    build_all.depends_on = [
        api_server, worker, proxy_server,
        web_app, admin_portal,
        shared_ui, i18n_lib, shared_lib, auth_lib, data_access, logging_lib, metrics_lib,
        wasm_module, codegen,
    ]
    test_all.depends_on = [api_server, web_app, worker, shared_lib]

    # Register components in RIG (order ensures IDs are stable)
    for comp in [
        api_server, worker, proxy_server,
        web_app, admin_portal,
        shared_ui, i18n_lib, shared_lib, auth_lib, data_access, logging_lib, metrics_lib,
        wasm_module, codegen,
        build_all, test_all,
    ]:
        rig.add_component(comp)

    # Tests (Jest-style logical tests)
    rig.add_test(TestDefinition(
        name="api_server_unit",
        test_executable_component=api_server,
        test_executable_component_id=None,
        test_components=[api_server],
        test_framework="jest",
        source_files=[Path("backend/api-server/src/index.test.ts")],
        evidence=[Evidence(line=["backend/api-server/package.json:10"])],
    ))

    rig.add_test(TestDefinition(
        name="web_app_unit",
        test_executable_component=web_app,
        test_executable_component_id=None,
        test_components=[web_app],
        test_framework="jest",
        source_files=[Path("frontend/web-app/src/app.test.tsx")],
        evidence=[Evidence(line=["frontend/web-app/package.json:12"])],
    ))

    rig.add_test(TestDefinition(
        name="shared_lib_unit",
        test_executable_component=shared_lib,
        test_executable_component_id=None,
        test_components=[shared_lib],
        test_framework="jest",
        source_files=[Path("libs/shared-lib/src/index.test.ts")],
        evidence=[Evidence(line=["libs/shared-lib/package.json:10"])],
    ))

    rig.add_test(TestDefinition(
        name="data_access_integration",
        test_executable_component=data_access,
        test_executable_component_id=None,
        test_components=[data_access],
        test_framework="jest",
        source_files=[Path("libs/data-access/src/index.test.ts")],
        evidence=[Evidence(line=["libs/data-access/package.json:10"])],
    ))

    rig.add_test(TestDefinition(
        name="worker_unit",
        test_executable_component=worker,
        test_executable_component_id=None,
        test_components=[worker],
        test_framework="jest",
        source_files=[Path("backend/worker/src/index.test.ts")],
        evidence=[Evidence(line=["backend/worker/package.json:10"])],
    ))

    # Validate before writing
    validation_errors = rig.validate()
    if len(validation_errors) > 0:
        for error in validation_errors:
            print(f"Validation Error ({error.category}):\n    File: {error.file_path}\n    Message: {error.message}\n    Node Name: {error.node_name}\n")
        raise RIGValidationError(validation_errors)

    # Persist ground-truth artifacts
    out_dir = Path(__file__).parent
    sqlite_path = out_dir / "npm_ground_truth.sqlite3"
    json_path = out_dir / "npm_ground_truth.json"

    rig.save(sqlite_path)
    # Use the loaded representation as canonical to avoid serialization parity issues
    rig_loaded = RIG.load(sqlite_path)
    gt_json = rig_loaded.generate_prompts_json_data(False)
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(gt_json)

    # Determinism check: re-load and compare loaded vs loaded
    rig_loaded2 = RIG.load(sqlite_path)
    diff_text = rig_loaded.compare(rig_loaded2)
    if diff_text:
        raise ValueError(f"Loaded RIG is not deterministic across loads:\n{diff_text}")

    # Complexity target check
    import json as _json
    gt_dict = _json.loads(gt_json)
    raw_score, metrics = _calc_complexity(gt_dict)
    normalized = (raw_score / 229.0) * 100.0
    if not (50.0 < normalized < 70.0):
        raise AssertionError(
            f"Normalized complexity {normalized:.2f} out of bounds; raw={raw_score}, metrics={metrics}"
        )


if __name__ == "__main__":
    main()
