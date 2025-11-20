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
)

from tests.test_utils import test_repos_root


def main() -> None:
    rig = RIG()

    # Resolve the repository root for the test repo
    repo_root = test_repos_root / "go" / "microservices"

    # Set repository and build system info
    rig.set_repository_info(
        RepositoryInfo(
            name="GoMicroservices",
            root_path=repo_root,
            build_directory=repo_root / "bin",
            output_directory=repo_root / "bin",
            install_directory=None,
            configure_command=None,
            build_command="go build",
            install_command=None,
            test_command="go test",
        )
    )

    rig.set_build_system_info(
        BuildSystemInfo(
            name="go",
            version="1.21",
            build_type="Release",
        )
    )

    # Create external packages (13 defined, 11 used by components)
    # testify and crypto are defined but not directly used by any component
    external_packages = []
    package_managers = {
        "gin": PackageManager(name="go", package_name="github.com/gin-gonic/gin"),
        "pq": PackageManager(name="go", package_name="github.com/lib/pq"),
        "redis": PackageManager(name="go", package_name="github.com/redis/go-redis/v9"),
        "jwt": PackageManager(name="go", package_name="github.com/golang-jwt/jwt/v5"),
        "uuid": PackageManager(name="go", package_name="github.com/google/uuid"),
        "testify": PackageManager(name="go", package_name="github.com/stretchr/testify"),
        "zap": PackageManager(name="go", package_name="go.uber.org/zap"),
        "prometheus": PackageManager(name="go", package_name="github.com/prometheus/client_golang"),
        "crypto": PackageManager(name="go", package_name="golang.org/x/crypto"),
        "validator": PackageManager(name="go", package_name="github.com/go-playground/validator/v10"),
        "viper": PackageManager(name="go", package_name="github.com/spf13/viper"),
        "nats": PackageManager(name="go", package_name="github.com/nats-io/nats.go"),
        "jni": PackageManager(name="system", package_name="JNI"),
    }

    for name, pm in package_managers.items():
        external_packages.append(ExternalPackage(name=name, package_manager=pm))

    # Create scala-utils library component
    scala_utils = Component(
        name="scala-utils",
        type=ComponentType.PACKAGE_LIBRARY,
        programming_language="scala",
        relative_path=Path("internal/common/utils/scalautils.jar"),
        source_files=[
            Path("internal/common/utils/ScalaUtils.scala"),
        ],
        external_packages=[],
        evidence=[Evidence(line=["internal/common/utils/ScalaUtils.scala:3"])],
        locations=[],
        depends_on=[],
    )

    # Create java-utils library component
    java_utils = Component(
        name="java-utils",
        type=ComponentType.PACKAGE_LIBRARY,
        programming_language="java",
        relative_path=Path("internal/common/utils/textutils.jar"),
        source_files=[
            Path("internal/common/utils/TextUtils.java"),
        ],
        external_packages=[],  # No external Java packages
        evidence=[Evidence(line=["internal/common/utils/TextUtils.java:3"])],
        locations=[],
        depends_on=[scala_utils],  # Dependency on scala-utils component
    )

    # Create 6 executable components + 2 library components (scala-utils, java-utils)
    # Each executable includes ALL transitive source files and ONLY external packages actually used

    # api-gateway.exe
    api_gateway = Component(
        name="api-gateway",
        type=ComponentType.EXECUTABLE,
        programming_language="go",
        relative_path=Path("bin/api-gateway.exe"),
        source_files=[
            Path("cmd/api-gateway/main.go"),
            Path("internal/common/config/config.go"),
            Path("internal/common/http/http.go"),
            Path("internal/common/logger/logger.go"),
            Path("internal/common/validation/validation.go"),
        ],
        external_packages=[
            external_packages[0],  # gin
            external_packages[6],  # zap
            external_packages[10],  # viper
            external_packages[9],  # validator
        ],
        evidence=[Evidence(line=["cmd/api-gateway/main.go:10"])],
        locations=[],
        depends_on=[],
    )

    # auth-service.exe
    auth_service = Component(
        name="auth-service",
        type=ComponentType.EXECUTABLE,
        programming_language="go",
        relative_path=Path("bin/auth-service.exe"),
        source_files=[
            Path("cmd/auth-service/main.go"),
            Path("pkg/auth/auth.go"),
            Path("internal/common/config/config.go"),
            Path("internal/common/http/http.go"),
            Path("internal/common/logger/logger.go"),
            Path("internal/common/validation/validation.go"),
        ],
        external_packages=[
            external_packages[0],  # gin
            external_packages[4],  # uuid
            external_packages[3],  # jwt
            external_packages[6],  # zap
            external_packages[10],  # viper
            external_packages[9],  # validator
        ],
        evidence=[Evidence(line=["cmd/auth-service/main.go:12"])],
        locations=[],
        depends_on=[],
    )

    # user-service.exe
    user_service = Component(
        name="user-service",
        type=ComponentType.EXECUTABLE,
        programming_language="go,c",  # Includes C (via CGo for JNI)
        relative_path=Path("bin/user-service.exe"),
        source_files=[
            Path("cmd/user-service/main.go"),
            Path("pkg/models/models.go"),
            Path("internal/common/config/config.go"),
            Path("internal/common/http/http.go"),
            Path("internal/common/logger/logger.go"),
            Path("internal/common/validation/validation.go"),
            Path("internal/common/database/database.go"),
            Path("internal/common/utils/java_wrapper.go"),  # Go wrapper using CGo
            Path("internal/common/utils/jni_wrapper.c"),     # C wrapper using JNI
        ],
        external_packages=[
            external_packages[0],  # gin
            external_packages[4],  # uuid
            external_packages[1],  # pq
            external_packages[6],  # zap
            external_packages[10],  # viper
            external_packages[9],  # validator
            external_packages[12],  # jni (JNI external package)
        ],
        evidence=[Evidence(line=["cmd/user-service/main.go:14"])],
        locations=[],
        depends_on=[java_utils],  # Dependency on java-utils component
    )

    # order-service.exe
    order_service = Component(
        name="order-service",
        type=ComponentType.EXECUTABLE,
        programming_language="go",
        relative_path=Path("bin/order-service.exe"),
        source_files=[
            Path("cmd/order-service/main.go"),
            Path("pkg/models/models.go"),
            Path("internal/common/config/config.go"),
            Path("internal/common/http/http.go"),
            Path("internal/common/logger/logger.go"),
            Path("internal/common/validation/validation.go"),
            Path("internal/common/database/database.go"),
            Path("internal/common/messaging/messaging.go"),
            Path("internal/common/cache/cache.go"),
            Path("internal/common/errors/errors.go"),
        ],
        external_packages=[
            external_packages[0],  # gin
            external_packages[4],  # uuid
            external_packages[2],  # redis
            external_packages[1],  # pq
            external_packages[11],  # nats
            external_packages[6],  # zap
            external_packages[10],  # viper
            external_packages[9],  # validator
        ],
        evidence=[Evidence(line=["cmd/order-service/main.go:16"])],
        locations=[],
        depends_on=[],
    )

    # payment-service.exe
    payment_service = Component(
        name="payment-service",
        type=ComponentType.EXECUTABLE,
        programming_language="go",
        relative_path=Path("bin/payment-service.exe"),
        source_files=[
            Path("cmd/payment-service/main.go"),
            Path("pkg/models/models.go"),
            Path("internal/common/config/config.go"),
            Path("internal/common/http/http.go"),
            Path("internal/common/logger/logger.go"),
            Path("internal/common/validation/validation.go"),
            Path("internal/common/database/database.go"),
            Path("internal/common/messaging/messaging.go"),
            Path("internal/common/metrics/metrics.go"),
        ],
        external_packages=[
            external_packages[0],  # gin
            external_packages[4],  # uuid
            external_packages[7],  # prometheus
            external_packages[1],  # pq
            external_packages[11],  # nats
            external_packages[6],  # zap
            external_packages[10],  # viper
            external_packages[9],  # validator
        ],
        evidence=[Evidence(line=["cmd/payment-service/main.go:14"])],
        locations=[],
        depends_on=[],
    )

    # notification-service.exe
    notification_service = Component(
        name="notification-service",
        type=ComponentType.EXECUTABLE,
        programming_language="go",
        relative_path=Path("bin/notification-service.exe"),
        source_files=[
            Path("cmd/notification-service/main.go"),
            Path("internal/common/config/config.go"),
            Path("internal/common/http/http.go"),
            Path("internal/common/logger/logger.go"),
            Path("internal/common/validation/validation.go"),
            Path("internal/common/messaging/messaging.go"),
        ],
        external_packages=[
            external_packages[0],  # gin
            external_packages[6],  # zap
            external_packages[10],  # viper
            external_packages[9],  # validator
            external_packages[11],  # nats
        ],
        evidence=[Evidence(line=["cmd/notification-service/main.go:11"])],
        locations=[],
        depends_on=[],
    )

    # Add all components (6 executables + 2 libraries)
    all_components = [
        scala_utils,  # Library component
        java_utils,  # Library component
        api_gateway,
        auth_service,
        user_service,
        order_service,
        payment_service,
        notification_service,
    ]

    for comp in all_components:
        rig.add_component(comp)

    # Create test definitions
    # Map test files to executable components that use those packages
    # Map test file paths to the line number of their first test function
    test_evidence_lines = {
        Path("internal/common/crypto/crypto_test.go"): 5,  # func TestHashPassword
        Path("internal/common/validation/validation_test.go"): 5,  # func TestValidateEmail
        Path("internal/common/logger/logger_test.go"): 5,  # func TestGetLogger
        Path("internal/common/config/config_test.go"): 5,  # func TestLoadConfig
        Path("internal/common/database/database_test.go"): 5,  # func TestGetDB
        Path("internal/common/messaging/messaging_test.go"): 5,  # func TestGetConn
        Path("internal/common/http/http_test.go"): 5,  # func TestSetupRouter
        Path("internal/common/cache/cache_test.go"): 5,  # func TestGetClient
        Path("internal/common/metrics/metrics_test.go"): 5,  # func TestRecordRequest
        Path("pkg/auth/auth_test.go"): 8,  # func TestGenerateToken
    }

    test_files = [
        # crypto_test.go -> auth-service (since auth uses crypto via pkg/auth)
        ("crypto", auth_service, Path("internal/common/crypto/crypto_test.go")),
        # validation_test.go -> all services that use config (all services)
        ("validation_api_gateway", api_gateway, Path("internal/common/validation/validation_test.go")),
        ("validation_auth_service", auth_service, Path("internal/common/validation/validation_test.go")),
        ("validation_user_service", user_service, Path("internal/common/validation/validation_test.go")),
        ("validation_order_service", order_service, Path("internal/common/validation/validation_test.go")),
        ("validation_payment_service", payment_service, Path("internal/common/validation/validation_test.go")),
        ("validation_notification_service", notification_service, Path("internal/common/validation/validation_test.go")),
        # logger_test.go -> all services
        ("logger_api_gateway", api_gateway, Path("internal/common/logger/logger_test.go")),
        ("logger_auth_service", auth_service, Path("internal/common/logger/logger_test.go")),
        ("logger_user_service", user_service, Path("internal/common/logger/logger_test.go")),
        ("logger_order_service", order_service, Path("internal/common/logger/logger_test.go")),
        ("logger_payment_service", payment_service, Path("internal/common/logger/logger_test.go")),
        ("logger_notification_service", notification_service, Path("internal/common/logger/logger_test.go")),
        # config_test.go -> all services that use config (all services)
        ("config_api_gateway", api_gateway, Path("internal/common/config/config_test.go")),
        ("config_auth_service", auth_service, Path("internal/common/config/config_test.go")),
        ("config_user_service", user_service, Path("internal/common/config/config_test.go")),
        ("config_order_service", order_service, Path("internal/common/config/config_test.go")),
        ("config_payment_service", payment_service, Path("internal/common/config/config_test.go")),
        ("config_notification_service", notification_service, Path("internal/common/config/config_test.go")),
        # database_test.go -> user-service, order-service, payment-service
        ("database_user_service", user_service, Path("internal/common/database/database_test.go")),
        ("database_order_service", order_service, Path("internal/common/database/database_test.go")),
        ("database_payment_service", payment_service, Path("internal/common/database/database_test.go")),
        # messaging_test.go -> order-service, payment-service, notification-service
        ("messaging_order_service", order_service, Path("internal/common/messaging/messaging_test.go")),
        ("messaging_payment_service", payment_service, Path("internal/common/messaging/messaging_test.go")),
        ("messaging_notification_service", notification_service, Path("internal/common/messaging/messaging_test.go")),
        # http_test.go -> all services
        ("http_api_gateway", api_gateway, Path("internal/common/http/http_test.go")),
        ("http_auth_service", auth_service, Path("internal/common/http/http_test.go")),
        ("http_user_service", user_service, Path("internal/common/http/http_test.go")),
        ("http_order_service", order_service, Path("internal/common/http/http_test.go")),
        ("http_payment_service", payment_service, Path("internal/common/http/http_test.go")),
        ("http_notification_service", notification_service, Path("internal/common/http/http_test.go")),
        # cache_test.go -> order-service
        ("cache_order_service", order_service, Path("internal/common/cache/cache_test.go")),
        # metrics_test.go -> payment-service
        ("metrics_payment_service", payment_service, Path("internal/common/metrics/metrics_test.go")),
        # auth_test.go -> auth-service
        ("auth_auth_service", auth_service, Path("pkg/auth/auth_test.go")),
    ]

    for test_name, component, test_file in test_files:
        # Get the correct line number for this test file's first test function
        evidence_line = test_evidence_lines.get(test_file, 1)
        test_def = TestDefinition(
            name=f"test_{test_name}",
            test_executable_component=component,
            test_executable_component_id=None,
            test_components=[],
            test_framework="Go",
            source_files=[test_file],
            evidence=[Evidence(line=[str(test_file) + ":" + str(evidence_line)])],
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
    sqlite_path = Path(__file__).parent / "go_microservices_ground_truth.sqlite3"
    rig.save(sqlite_path)

    # Write JSON prompt
    json_path = Path(__file__).parent / "go_microservices_ground_truth.json"
    rig_json_ground_truth = rig.generate_prompts_json_data()
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(rig_json_ground_truth)

    # Load from SQLite and compare
    rig_loaded = RIG.load(sqlite_path)
    diff_text = rig.compare(rig_loaded)
    if diff_text:
        raise ValueError(f"Loaded RIG does not match ground truth:\n{diff_text}")

    # Calculate and verify complexity score
    import json

    with open(json_path, "r", encoding="utf-8") as f:
        ground_truth_data = json.load(f)

    # Calculate complexity score inline (weights from config.py)
    COMPLEXITY_WEIGHTS = {
        'component': 2,
        'language': 10,
        'package': 3,
        'depth': 8,
        'aggregator': 5,
        'cross_lang_bonus': 15,
    }

    components = ground_truth_data.get("components", [])
    external_packages = ground_truth_data.get("external_packages", [])
    aggregators = ground_truth_data.get("aggregators", [])

    # Count languages (split comma-separated languages)
    languages = set()
    for comp in components:
        lang = comp.get("programming_language", "")
        if lang:
            # Split comma-separated languages (e.g., "go,c" -> ["go", "c"])
            for l in lang.split(','):
                languages.add(l.strip())

    # Calculate max dependency depth
    comp_map = {c.get("id"): c for c in components if c.get("id")}
    
    def get_dependency_depth(comp, visited=None):
        if visited is None:
            visited = set()
        comp_id = comp.get("id")
        if comp_id in visited:
            return 0
        visited.add(comp_id)
        depends_on_ids = comp.get("depends_on_ids", [])
        if not depends_on_ids:
            return 0
        max_depth = 0
        for dep_id in depends_on_ids:
            dep_comp = comp_map.get(dep_id)
            if dep_comp:
                depth = get_dependency_depth(dep_comp, visited.copy())
                max_depth = max(max_depth, depth)
        return max_depth + 1

    max_depth = 0
    for comp in components:
        depth = get_dependency_depth(comp)
        max_depth = max(max_depth, depth)

    # Check cross-language dependencies
    # This includes both component-to-component dependencies AND components with multiple languages
    has_cross_lang_deps = False
    
    # First check: components with multiple languages (e.g., "go,c")
    for comp in components:
        comp_lang = comp.get("programming_language", "")
        if ',' in comp_lang:
            has_cross_lang_deps = True
            break
    
    # Second check: component-to-component dependencies with different languages
    if not has_cross_lang_deps:
        for comp in components:
            comp_lang = comp.get("programming_language", "")
            comp_langs = set(comp_lang.split(',')) if comp_lang else set()
            depends_on_ids = comp.get("depends_on_ids", [])
            for dep_id in depends_on_ids:
                dep_comp = comp_map.get(dep_id, {})
                dep_lang = dep_comp.get("programming_language", "")
                dep_langs = set(dep_lang.split(',')) if dep_lang else set()
                # Check if there's any language difference
                if comp_langs and dep_langs and comp_langs != dep_langs:
                    has_cross_lang_deps = True
                    break
            if has_cross_lang_deps:
                break

    # Calculate raw score
    raw_score = (
        len(components) * COMPLEXITY_WEIGHTS['component'] +
        len(languages) * COMPLEXITY_WEIGHTS['language'] +
        len(external_packages) * COMPLEXITY_WEIGHTS['package'] +
        max_depth * COMPLEXITY_WEIGHTS['depth'] +
        len(aggregators) * COMPLEXITY_WEIGHTS['aggregator'] +
        (COMPLEXITY_WEIGHTS['cross_lang_bonus'] if has_cross_lang_deps else 0)
    )

    max_raw_score = 229  # From metaffi
    normalized_score = (raw_score / max_raw_score) * 100

    metrics = {
        'component_count': len(components),
        'programming_language_count': len(languages),
        'external_package_count': len(external_packages),
        'max_dependency_depth': max_depth,
        'aggregator_count': len(aggregators),
        'has_cross_language_dependencies': has_cross_lang_deps,
    }

    print(f"\nComplexity Score Verification:")
    print(f"  Raw Score: {raw_score}")
    print(f"  Normalized Score: {normalized_score:.1f}")
    print(f"  Components: {metrics['component_count']}")
    print(f"  Languages: {metrics['programming_language_count']}")
    print(f"  External Packages: {metrics['external_package_count']}")
    print(f"  Max Depth: {metrics['max_dependency_depth']}")
    print(f"  Aggregators: {metrics['aggregator_count']}")
    print(f"  Cross-language: {metrics['has_cross_language_dependencies']}")

    # Removed complexity range check - just inform user
    if normalized_score < 60:
        print(f"\nWARNING: Complexity score {normalized_score:.1f} is below target range 60-70")
    elif normalized_score > 70:
        print(f"\nWARNING: Complexity score {normalized_score:.1f} is above target range 60-70")


if __name__ == "__main__":
    main()
