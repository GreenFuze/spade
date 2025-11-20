"""
Ground truth generator for high-complexity npm monorepo test repository.

This script creates a RIG that models actual buildable artifacts (dist/*.js, 
bin/*.js, WASM modules, native addons) as Components, not npm packages themselves.
"""

from pathlib import Path

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
    Aggregator,
)

from tests.test_utils import test_repos_root


def main() -> None:
    rig = RIG()

    # Resolve the repository root for the test repo
    repo_root = test_repos_root / "npm"

    # Set repository and build system info
    rig.set_repository_info(
        RepositoryInfo(
            name="npm-complex-monorepo",
            root_path=repo_root,
            build_directory=repo_root / "node_modules",
            output_directory=repo_root / "dist",
            install_directory=None,
            configure_command="npm install",
            build_command="npm run build",
            install_command="npm install",
            test_command="npm test",
        )
    )

    rig.set_build_system_info(
        BuildSystemInfo(
            name="npm",
            version=None,
            build_type="production",
        )
    )

    # Create external packages (npm dependencies)
    external_packages = {}
    
    npm_packages = [
        "axios", "react", "react-dom", "jsonwebtoken", "bcrypt", 
        "winston", "prom-client", "mongoose", "express", "fastify",
        "typescript", "@types/node", "@types/react", "@types/react-dom",
        "@types/jsonwebtoken", "@types/bcrypt", "@types/express",
        "jest", "@types/jest", "webpack", "wasm-pack", "node-gyp"
    ]
    
    for pkg_name in npm_packages:
        package_manager = PackageManager(
            name="npm",
            package_name=pkg_name
        )
        external_packages[pkg_name] = ExternalPackage(
            name=pkg_name,
            package_manager=package_manager
        )

    # Level 0: Core packages (no dependencies)
    # RIG Component: core_lib represents the build artifact packages/core/dist/index.js
    # npm package: @monorepo/core has no internal npm package dependencies
    # Therefore: RIG Component core_lib has no depends_on (base component)
    core_lib = Component(
        name="core.dist.js",
        type=ComponentType.INTERPRETED,
        programming_language="typescript",
        relative_path=Path("packages/core/dist/index.js"),
        source_files=[
            Path("packages/core/src/index.ts")
        ],
        external_packages=[
            external_packages["typescript"],
            external_packages["@types/node"],
            external_packages["jest"],
            external_packages["@types/jest"]
        ],
        evidence=[Evidence(line=["packages/core/package.json:2"])],
        locations=[],
    )

    # Level 1: Packages depending on core
    # RIG Component: utils_lib represents the build artifact packages/utils/dist/index.js
    # npm package: @monorepo/utils depends on npm package @monorepo/core
    # Therefore: RIG Component utils_lib depends_on RIG Component core_lib
    utils_lib = Component(
        name="utils.dist.js",
        type=ComponentType.INTERPRETED,
        programming_language="typescript",
        relative_path=Path("packages/utils/dist/index.js"),
        source_files=[
            Path("packages/utils/src/index.ts"),
            Path("packages/core/src/index.ts")  # Transitive source
        ],
        external_packages=[],
        evidence=[Evidence(line=["packages/utils/package.json:2"])],
        locations=[],
        depends_on=[core_lib]
    )

    # RIG Component: data_models_lib represents the build artifact packages/data-models/dist/index.js
    # npm package: @monorepo/data-models depends on npm package @monorepo/core
    # Therefore: RIG Component data_models_lib depends_on RIG Component core_lib
    data_models_lib = Component(
        name="data-models.dist.js",
        type=ComponentType.INTERPRETED,
        programming_language="typescript",
        relative_path=Path("packages/data-models/dist/index.js"),
        source_files=[
            Path("packages/data-models/src/index.ts"),
            Path("packages/core/src/index.ts")  # Transitive source
        ],
        external_packages=[],
        evidence=[Evidence(line=["packages/data-models/package.json:2"])],
        locations=[],
        depends_on=[core_lib]
    )

    # RIG Component: shared_ui_lib represents the build artifact libs/shared-ui/dist/index.js
    # npm package: @monorepo/shared-ui depends on npm packages @monorepo/core, react
    # Therefore: RIG Component shared_ui_lib depends_on RIG Component core_lib
    # Note: react is an external npm package (not a RIG Component), so it's in external_packages only
    shared_ui_lib = Component(
        name="shared-ui.dist.js",
        type=ComponentType.INTERPRETED,
        programming_language="typescript",
        relative_path=Path("libs/shared-ui/dist/index.js"),
        source_files=[
            Path("libs/shared-ui/src/index.tsx"),
            Path("packages/core/src/index.ts")  # Transitive source
        ],
        external_packages=[
            external_packages["react"],
            external_packages["@types/react"]
        ],
        evidence=[Evidence(line=["libs/shared-ui/package.json:2"])],
        locations=[],
        depends_on=[core_lib]
    )

    # RIG Component: logging_lib represents the build artifact libs/logging-lib/dist/index.js
    # npm package: @monorepo/logging-lib depends on npm packages @monorepo/core, winston
    # Therefore: RIG Component logging_lib depends_on RIG Component core_lib
    # Note: winston is an external npm package (not a RIG Component), so it's in external_packages only
    logging_lib = Component(
        name="logging-lib.dist.js",
        type=ComponentType.INTERPRETED,
        programming_language="typescript",
        relative_path=Path("libs/logging-lib/dist/index.js"),
        source_files=[
            Path("libs/logging-lib/src/index.ts"),
            Path("packages/core/src/index.ts")  # Transitive source
        ],
        external_packages=[external_packages["winston"]],
        evidence=[Evidence(line=["libs/logging-lib/package.json:2"])],
        locations=[],
        depends_on=[core_lib]
    )

    # Level 2: Packages depending on level 1
    # RIG Component: config_lib represents the build artifact packages/config/dist/index.js
    # npm package: @monorepo/config depends on npm packages @monorepo/core, @monorepo/utils
    # Therefore: RIG Component config_lib depends_on RIG Components core_lib, utils_lib
    # Note: Both npm packages map to RIG Components, so both are included in depends_on
    config_lib = Component(
        name="config.dist.js",
        type=ComponentType.INTERPRETED,
        programming_language="typescript",
        relative_path=Path("packages/config/dist/index.js"),
        source_files=[
            Path("packages/config/src/index.ts"),
            Path("packages/utils/src/index.ts"),  # Transitive source
            Path("packages/core/src/index.ts")     # Transitive source
        ],
        external_packages=[],
        evidence=[Evidence(line=["packages/config/package.json:2"])],
        locations=[],
        depends_on=[core_lib, utils_lib]
    )

    # RIG Component: api_client_lib represents the build artifact packages/api-client/dist/index.js
    # npm package: @monorepo/api-client depends on npm packages @monorepo/core, @monorepo/utils, axios
    # Therefore: RIG Component api_client_lib depends_on RIG Components core_lib, utils_lib
    # Note: axios is an external npm package (not a RIG Component), so it's in external_packages only
    api_client_lib = Component(
        name="api-client.dist.js",
        type=ComponentType.INTERPRETED,
        programming_language="typescript",
        relative_path=Path("packages/api-client/dist/index.js"),
        source_files=[
            Path("packages/api-client/src/index.ts"),
            Path("packages/core/src/index.ts"),    # Transitive source
            Path("packages/utils/src/index.ts")    # Transitive source
        ],
        external_packages=[external_packages["axios"]],
        evidence=[Evidence(line=["packages/api-client/package.json:2"])],
        locations=[],
        depends_on=[core_lib, utils_lib]
    )

    # RIG Component: auth_lib represents the build artifact libs/auth-lib/dist/index.js
    # npm package: @monorepo/auth-lib depends on npm packages @monorepo/core, @monorepo/utils, jsonwebtoken, bcrypt
    # Therefore: RIG Component auth_lib depends_on RIG Components core_lib, utils_lib
    # Note: jsonwebtoken and bcrypt are external npm packages (not RIG Components), so they're in external_packages only
    auth_lib = Component(
        name="auth-lib.dist.js",
        type=ComponentType.INTERPRETED,
        programming_language="typescript",
        relative_path=Path("libs/auth-lib/dist/index.js"),
        source_files=[
            Path("libs/auth-lib/src/index.ts"),
            Path("packages/core/src/index.ts"),    # Transitive source
            Path("packages/utils/src/index.ts")    # Transitive source
        ],
        external_packages=[
            external_packages["jsonwebtoken"],
            external_packages["bcrypt"],
            external_packages["@types/jsonwebtoken"],
            external_packages["@types/bcrypt"]
        ],
        evidence=[Evidence(line=["libs/auth-lib/package.json:2"])],
        locations=[],
        depends_on=[core_lib, utils_lib]
    )

    # RIG Component: metrics_lib represents the build artifact libs/metrics-lib/dist/index.js
    # npm package: @monorepo/metrics-lib depends on npm packages @monorepo/core, @monorepo/utils, prom-client
    # Therefore: RIG Component metrics_lib depends_on RIG Components core_lib, utils_lib
    # Note: prom-client is an external npm package (not a RIG Component), so it's in external_packages only
    metrics_lib = Component(
        name="metrics-lib.dist.js",
        type=ComponentType.INTERPRETED,
        programming_language="typescript",
        relative_path=Path("libs/metrics-lib/dist/index.js"),
        source_files=[
            Path("libs/metrics-lib/src/index.ts"),
            Path("packages/core/src/index.ts"),    # Transitive source
            Path("packages/utils/src/index.ts")   # Transitive source
        ],
        external_packages=[external_packages["prom-client"]],
        evidence=[Evidence(line=["libs/metrics-lib/package.json:2"])],
        locations=[],
        depends_on=[core_lib, utils_lib]
    )

    # RIG Component: data_access_lib represents the build artifact libs/data-access/dist/index.js
    # npm package: @monorepo/data-access depends on npm packages @monorepo/core, @monorepo/utils, @monorepo/data-models, mongoose
    # Therefore: RIG Component data_access_lib depends_on RIG Components core_lib, utils_lib, data_models_lib
    # Note: mongoose is an external npm package (not a RIG Component), so it's in external_packages only
    data_access_lib = Component(
        name="data-access.dist.js",
        type=ComponentType.INTERPRETED,
        programming_language="typescript",
        relative_path=Path("libs/data-access/dist/index.js"),
        source_files=[
            Path("libs/data-access/src/index.ts"),
            Path("packages/core/src/index.ts"),         # Transitive source
            Path("packages/utils/src/index.ts"),        # Transitive source
            Path("packages/data-models/src/index.ts")   # Transitive source
        ],
        external_packages=[external_packages["mongoose"]],
        evidence=[Evidence(line=["libs/data-access/package.json:2"])],
        locations=[],
        depends_on=[core_lib, utils_lib, data_models_lib]
    )

    # Level 3: Services with cross-language dependencies
    # RIG Component: wasm_module represents the build artifact modules/wasm-module/pkg/wasm_module.wasm
    # npm package: @monorepo/wasm-module has no internal npm package dependencies (standalone Rust module)
    # Therefore: RIG Component wasm_module has no depends_on (standalone component)
    # Note: wasm-pack is a build tool (external npm package), not a runtime dependency
    wasm_module = Component(
        name="wasm_module.wasm",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="rust",
        relative_path=Path("modules/wasm-module/pkg/wasm_module.wasm"),
        source_files=[
            Path("modules/wasm-module/src/lib.rs")
        ],
        external_packages=[external_packages["wasm-pack"]],
        evidence=[Evidence(line=["modules/wasm-module/package.json:2"])],
        locations=[],
    )

    # RIG Component: native_addon represents the build artifact modules/native-addon/build/Release/native_addon.node
    # npm package: @monorepo/native-addon has no internal npm package dependencies (standalone Go module)
    # Therefore: RIG Component native_addon has no depends_on (standalone component)
    # Note: node-gyp is a build tool (external npm package), not a runtime dependency
    native_addon = Component(
        name="native_addon.node",
        type=ComponentType.SHARED_LIBRARY,
        programming_language="go",
        relative_path=Path("modules/native-addon/build/Release/native_addon.node"),
        source_files=[
            Path("modules/native-addon/main.go")
        ],
        external_packages=[external_packages["node-gyp"]],
        evidence=[Evidence(line=["modules/native-addon/package.json:2"])],
        locations=[],
    )

    # RIG Component: python_bridge represents the runtime script modules/python-bridge/bridge.py
    # npm package: @monorepo/python-bridge has no internal npm package dependencies (standalone Python script)
    # Therefore: RIG Component python_bridge has no depends_on (standalone component)
    # Note: This is a runtime-only component, called via execSync at runtime, not a build-time artifact dependency
    python_bridge = Component(
        name="python-bridge",
        type=ComponentType.INTERPRETED,
        programming_language="python",
        relative_path=Path("modules/python-bridge/bridge.py"),
        source_files=[
            Path("modules/python-bridge/bridge.py"),
            Path("modules/python-bridge/setup.py"),
            Path("modules/python-bridge/index.js")  # Entry point (main in package.json)
        ],
        external_packages=[],
        evidence=[Evidence(line=["modules/python-bridge/package.json:2"])],
        locations=[],
    )

    # RIG Component: auth_service represents the build artifact services/auth-service/dist/index.js
    # npm package: @monorepo/auth-service depends on npm packages @monorepo/core, @monorepo/utils,
    # @monorepo/auth-lib, @monorepo/data-models, @monorepo/python-bridge
    # Therefore: RIG Component auth_service depends_on RIG Components core_lib, utils_lib, auth_lib, data_models_lib, python_bridge
    # Note: Uses Python bridge for validation - build-time dependency
    auth_service = Component(
        name="auth-service.dist.js",
        type=ComponentType.INTERPRETED,
        programming_language="typescript",
        relative_path=Path("services/auth-service/dist/index.js"),
        source_files=[
            Path("services/auth-service/src/index.ts"),
            Path("services/auth-service/scripts/validate.py"),  # Local runtime script
            Path("packages/core/src/index.ts"),         # Transitive source
            Path("packages/utils/src/index.ts"),        # Transitive source
            Path("libs/auth-lib/src/index.ts"),        # Transitive source
            Path("packages/data-models/src/index.ts")  # Transitive source
        ],
        external_packages=[],
        evidence=[Evidence(line=["services/auth-service/package.json:2"])],
        locations=[],
        depends_on=[core_lib, utils_lib, auth_lib, data_models_lib, python_bridge]
    )

    # RIG Component: data_processor represents the build artifact services/data-processor/dist/index.js
    # npm package: @monorepo/data-processor depends on npm packages @monorepo/core, @monorepo/utils, 
    # @monorepo/data-models, @monorepo/wasm-module
    # Therefore: RIG Component data_processor depends_on RIG Components core_lib, utils_lib, data_models_lib, wasm_module
    # Note: @monorepo/wasm-module maps to RIG Component wasm_module (build artifact dependency)
    data_processor = Component(
        name="data-processor.dist.js",
        type=ComponentType.INTERPRETED,
        programming_language="typescript",
        relative_path=Path("services/data-processor/dist/index.js"),
        source_files=[
            Path("services/data-processor/src/index.ts"),
            Path("packages/core/src/index.ts"),         # Transitive source
            Path("packages/utils/src/index.ts"),        # Transitive source
            Path("packages/data-models/src/index.ts")   # Transitive source
        ],
        external_packages=[],
        evidence=[Evidence(line=["services/data-processor/package.json:2"])],
        locations=[],
        depends_on=[core_lib, utils_lib, data_models_lib, wasm_module]
    )

    # RIG Component: analytics represents the build artifact services/analytics/dist/index.js
    # npm package: @monorepo/analytics depends on npm packages @monorepo/core, @monorepo/utils, 
    # @monorepo/metrics-lib, @monorepo/native-addon
    # Therefore: RIG Component analytics depends_on RIG Components core_lib, utils_lib, metrics_lib, native_addon
    # Note: @monorepo/native-addon maps to RIG Component native_addon (build artifact dependency)
    analytics = Component(
        name="analytics.dist.js",
        type=ComponentType.INTERPRETED,
        programming_language="typescript",
        relative_path=Path("services/analytics/dist/index.js"),
        source_files=[
            Path("services/analytics/src/index.ts"),
            Path("packages/core/src/index.ts"),         # Transitive source
            Path("packages/utils/src/index.ts"),        # Transitive source
            Path("libs/metrics-lib/src/index.ts")       # Transitive source
        ],
        external_packages=[],
        evidence=[Evidence(line=["services/analytics/package.json:2"])],
        locations=[],
        depends_on=[core_lib, utils_lib, metrics_lib, native_addon]
    )

    # RIG Component: notification represents the build artifact services/notification/dist/index.js
    # npm package: @monorepo/notification depends on npm packages @monorepo/core, @monorepo/utils, 
    # @monorepo/data-models
    # Therefore: RIG Component notification depends_on RIG Components core_lib, utils_lib, data_models_lib
    notification = Component(
        name="notification.dist.js",
        type=ComponentType.INTERPRETED,
        programming_language="typescript",
        relative_path=Path("services/notification/dist/index.js"),
        source_files=[
            Path("services/notification/src/index.ts"),
            Path("packages/core/src/index.ts"),         # Transitive source
            Path("packages/utils/src/index.ts"),        # Transitive source
            Path("packages/data-models/src/index.ts")   # Transitive source
        ],
        external_packages=[],
        evidence=[Evidence(line=["services/notification/package.json:2"])],
        locations=[],
        depends_on=[core_lib, utils_lib, data_models_lib]
    )

    # Level 4: Applications
    # RIG Component: web_app represents the build artifact apps/web-app/dist/bundle.js
    # npm package: @monorepo/web-app depends on npm packages @monorepo/shared-ui, @monorepo/auth-lib, 
    # @monorepo/api-client, @monorepo/auth-service, @monorepo/data-processor, react, react-dom
    # Therefore: RIG Component web_app depends_on RIG Components shared_ui_lib, auth_lib, api_client_lib, 
    # auth_service, data_processor
    # Note: react and react-dom are external npm packages (not RIG Components), so they're in external_packages only.
    # webpack is a build tool (external npm package), not a runtime dependency.
    web_app = Component(
        name="web-app.bundle.js",
        type=ComponentType.INTERPRETED,
        programming_language="typescript",
        relative_path=Path("apps/web-app/dist/bundle.js"),
        source_files=[
            Path("apps/web-app/src/index.tsx"),
            Path("libs/shared-ui/src/index.tsx"),        # Transitive source
            Path("libs/auth-lib/src/index.ts"),         # Transitive source
            Path("packages/api-client/src/index.ts"),   # Transitive source
            Path("services/auth-service/src/index.ts"), # Transitive source
            Path("services/data-processor/src/index.ts"), # Transitive source
            Path("packages/core/src/index.ts"),         # Transitive source
            Path("packages/utils/src/index.ts"),        # Transitive source
            Path("packages/data-models/src/index.ts")   # Transitive source
        ],
        external_packages=[
            external_packages["react"],
            external_packages["react-dom"],
            external_packages["webpack"],
            external_packages["@types/react-dom"]
        ],
        evidence=[Evidence(line=["apps/web-app/package.json:2"])],
        locations=[],
        depends_on=[shared_ui_lib, auth_lib, api_client_lib, auth_service, data_processor]
    )

    # RIG Component: admin_portal represents the build artifact apps/admin-portal/dist/bundle.js
    # npm package: @monorepo/admin-portal depends on npm packages @monorepo/shared-ui, @monorepo/auth-lib, 
    # @monorepo/api-client, @monorepo/analytics, @monorepo/notification, react, react-dom
    # Therefore: RIG Component admin_portal depends_on RIG Components shared_ui_lib, auth_lib, api_client_lib, 
    # analytics, notification
    # Note: react and react-dom are external npm packages (not RIG Components), so they're in external_packages only.
    # webpack is a build tool (external npm package), not a runtime dependency.
    admin_portal = Component(
        name="admin-portal.bundle.js",
        type=ComponentType.INTERPRETED,
        programming_language="typescript",
        relative_path=Path("apps/admin-portal/dist/bundle.js"),
        source_files=[
            Path("apps/admin-portal/src/index.tsx"),
            Path("libs/shared-ui/src/index.tsx"),        # Transitive source
            Path("libs/auth-lib/src/index.ts"),           # Transitive source
            Path("packages/api-client/src/index.ts"),    # Transitive source
            Path("services/analytics/src/index.ts"),     # Transitive source
            Path("services/notification/src/index.ts"),  # Transitive source
            Path("packages/core/src/index.ts"),          # Transitive source
            Path("packages/utils/src/index.ts"),         # Transitive source
            Path("packages/data-models/src/index.ts"),   # Transitive source
            Path("libs/metrics-lib/src/index.ts")        # Transitive source
        ],
        external_packages=[
            external_packages["react"],
            external_packages["react-dom"],
            external_packages["webpack"]
        ],
        evidence=[Evidence(line=["apps/admin-portal/package.json:2"])],
        locations=[],
        depends_on=[shared_ui_lib, auth_lib, api_client_lib, analytics, notification]
    )

    # RIG Component: api_server represents the build artifact apps/api-server/dist/index.js
    # npm package: @monorepo/api-server depends on npm packages @monorepo/auth-service, @monorepo/data-processor,
    # @monorepo/analytics, @monorepo/notification, @monorepo/data-access, @monorepo/python-bridge, express, fastify
    # Therefore: RIG Component api_server depends_on RIG Components auth_service, data_processor, analytics,
    # notification, data_access_lib, python_bridge
    # Note: express and fastify are external npm packages (not RIG Components), so they're in external_packages only.
    # Uses python-bridge - build-time dependency
    api_server = Component(
        name="api-server.dist.js",
        type=ComponentType.INTERPRETED,
        programming_language="typescript",
        relative_path=Path("apps/api-server/dist/index.js"),
        source_files=[
            Path("apps/api-server/src/index.ts"),
            Path("services/auth-service/src/index.ts"),  # Transitive source
            Path("services/data-processor/src/index.ts"), # Transitive source
            Path("services/analytics/src/index.ts"),      # Transitive source
            Path("services/notification/src/index.ts"),  # Transitive source
            Path("libs/data-access/src/index.ts"),       # Transitive source
            Path("packages/core/src/index.ts"),          # Transitive source
            Path("packages/utils/src/index.ts"),         # Transitive source
            Path("packages/data-models/src/index.ts"),   # Transitive source
            Path("libs/auth-lib/src/index.ts"),          # Transitive source
            Path("libs/metrics-lib/src/index.ts")        # Transitive source
        ],
        external_packages=[
            external_packages["express"],
            external_packages["fastify"],
            external_packages["@types/express"]
        ],
        evidence=[Evidence(line=["apps/api-server/package.json:2"])],
        locations=[],
        depends_on=[auth_service, data_processor, analytics, notification, data_access_lib, python_bridge]
    )

    # Tools
    # tools/build-aggregator: TypeScript build aggregation tool
    # Produces: tools/build-aggregator/dist/index.js
    # Dependencies: @monorepo/core (npm package → core_lib RIG Component)
    build_aggregator = Component(
        name="build-aggregator.dist.js",
        type=ComponentType.INTERPRETED,
        programming_language="typescript",
        relative_path=Path("tools/build-aggregator/dist/index.js"),
        source_files=[
            Path("tools/build-aggregator/src/index.ts"),
            Path("packages/core/src/index.ts")  # Transitive source from @monorepo/core
        ],
        external_packages=[],
        evidence=[Evidence(line=["tools/build-aggregator/package.json:2"])],
        locations=[],
        depends_on=[core_lib]
    )

    # tools/codegen: Python code generation tool
    # Entry point: tools/codegen/main.py
    # No dependencies
    codegen = Component(
        name="codegen",
        type=ComponentType.INTERPRETED,
        programming_language="python",
        relative_path=Path("tools/codegen/main.py"),
        source_files=[
            Path("tools/codegen/main.py")
        ],
        external_packages=[],
        evidence=[Evidence(line=["tools/codegen/package.json:2"])],
        locations=[],
    )

    # =========================================================================
    # Aggregators
    # =========================================================================

    # Aggregator 1: build-all
    # Builds all major TypeScript components (17 components)
    build_all_aggregator = Aggregator(
        name="@monorepo/build-all",
        depends_on=[
            core_lib, utils_lib, config_lib, api_client_lib, data_models_lib,
            shared_ui_lib, auth_lib, logging_lib, metrics_lib, data_access_lib,
            auth_service, data_processor, analytics, notification,
            web_app, admin_portal, api_server
        ],
        evidence=[Evidence(line=["aggregators/build-all/package.json:2"])]
    )

    # Aggregator 2: test-all
    # Tests all major TypeScript components (17 components)
    test_all_aggregator = Aggregator(
        name="@monorepo/test-all",
        depends_on=[
            core_lib, utils_lib, config_lib, api_client_lib, data_models_lib,
            shared_ui_lib, auth_lib, logging_lib, metrics_lib, data_access_lib,
            auth_service, data_processor, analytics, notification,
            web_app, admin_portal, api_server
        ],
        evidence=[Evidence(line=["aggregators/test-all/package.json:2"])]
    )

    # Aggregator 3: deploy-all
    # Deploys the 3 main applications
    deploy_all_aggregator = Aggregator(
        name="@monorepo/deploy-all",
        depends_on=[web_app, admin_portal, api_server],
        evidence=[Evidence(line=["aggregators/deploy-all/package.json:2"])]
    )

    # Add all components to RIG
    all_components = [
        core_lib, utils_lib, data_models_lib, shared_ui_lib, logging_lib,
        config_lib, api_client_lib, auth_lib, metrics_lib, data_access_lib,
        wasm_module, native_addon, python_bridge,
        auth_service, data_processor, analytics, notification,
        web_app, admin_portal, api_server,
        build_aggregator, codegen
    ]
    
    for component in all_components:
        rig.add_component(component)

    # Add aggregators to RIG
    rig.add_aggregator(build_all_aggregator)
    rig.add_aggregator(test_all_aggregator)
    rig.add_aggregator(deploy_all_aggregator)

    # Add test definitions
    test_files = [
        (Path("packages/core/src/index.test.ts"), core_lib, "jest"),
        (Path("packages/utils/src/index.test.ts"), utils_lib, "jest"),
    ]
    
    for test_file, component, framework in test_files:
        # Determine line number for first test function
        if "core" in str(test_file):
            line_num = 4  # packages/core/src/index.test.ts first test at line 4
        else:
            line_num = 5  # packages/utils/src/index.test.ts first test at line 5

        test_def = TestDefinition(
            name=test_file.stem,
            test_executable_component=component,
            test_executable_component_id=None,
            test_components=[component],
            test_framework=framework,
            source_files=[test_file],
            evidence=[Evidence(line=[f"{test_file}:{line_num}"])],
        )
        rig.add_test(test_def)

    # Validate before saving
    validation_errors = rig.validate()
    if len(validation_errors) > 0:
        for error in validation_errors:
            print(f"""Validation Error ({error.category}):
    File: {error.file_path}
    Message: {error.message}
    Node Name: {error.node_name}
""")
        raise RIGValidationError(validation_errors)

    # Save to SQLite
    sqlite_path = Path(__file__).parent / "npm_ground_truth.sqlite3"
    rig.save(sqlite_path)

    # Write JSON prompt
    json_path = Path(__file__).parent / "npm_ground_truth.json"
    rig_json_ground_truth = rig.generate_prompts_json_data()
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(rig_json_ground_truth)
        
    # Load from SQLite and compare
    rig_loaded = RIG.load(sqlite_path)
    diff_text = rig.compare(rig_loaded)
    if diff_text:
        raise ValueError(f"Loaded RIG does not match ground truth:\n{diff_text}")
    
    print("Ground truth generated successfully!")


if __name__ == "__main__":
    main()
