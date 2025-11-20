"""
Ground truth generator for Maven task-manager repository.

Creates a RIG with 10 components, 10 external packages, 1 aggregator, and 10 tests
to achieve normalized complexity score of 42 (raw score ~97).
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
    ExternalPackage,
    PackageManager,
    Aggregator,
    RIGValidationError,
)

from tests.test_utils import test_repos_root


def main() -> None:
    rig = RIG()

    # Resolve the repository root for the test repo
    repo_root = test_repos_root / "maven"

    # Set repository and build system info
    rig.set_repository_info(
        RepositoryInfo(
            name="task-manager",
            root_path=repo_root,
            build_directory=repo_root / "target",
            output_directory=repo_root / "target",
            install_directory=None,
            configure_command="mvn clean compile",
            build_command="mvn package",
            install_command="mvn install",
            test_command="mvn test",
        )
    )

    rig.set_build_system_info(
        BuildSystemInfo(
            name="Maven",
            version=None,
            build_type=None,
        )
    )

    # Create external packages (10 total)
    external_packages = [
        ExternalPackage(
            name="guava",
            package_manager=PackageManager(
                name="maven",
                package_name="com.google.guava:guava:32.1.2-jre"
            )
        ),
        ExternalPackage(
            name="slf4j-api",
            package_manager=PackageManager(
                name="maven",
                package_name="org.slf4j:slf4j-api:2.0.9"
            )
        ),
        ExternalPackage(
            name="logback-classic",
            package_manager=PackageManager(
                name="maven",
                package_name="ch.qos.logback:logback-classic:1.4.11"
            )
        ),
        ExternalPackage(
            name="jackson-databind",
            package_manager=PackageManager(
                name="maven",
                package_name="com.fasterxml.jackson.core:jackson-databind:2.15.2"
            )
        ),
        ExternalPackage(
            name="spring-web",
            package_manager=PackageManager(
                name="maven",
                package_name="org.springframework:spring-web:6.0.11"
            )
        ),
        ExternalPackage(
            name="hibernate-core",
            package_manager=PackageManager(
                name="maven",
                package_name="org.hibernate.orm:hibernate-core:6.2.7.Final"
            )
        ),
        ExternalPackage(
            name="h2",
            package_manager=PackageManager(
                name="maven",
                package_name="com.h2database:h2:2.2.224"
            )
        ),
        ExternalPackage(
            name="junit-jupiter",
            package_manager=PackageManager(
                name="maven",
                package_name="org.junit.jupiter:junit-jupiter:5.10.0"
            )
        ),
        ExternalPackage(
            name="mockito-core",
            package_manager=PackageManager(
                name="maven",
                package_name="org.mockito:mockito-core:5.5.0"
            )
        ),
        ExternalPackage(
            name="jakarta-servlet-api",
            package_manager=PackageManager(
                name="maven",
                package_name="jakarta.servlet:jakarta.servlet-api:6.0.0"
            )
        ),
    ]

    # Create components in dependency order (depth 0 to depth 4)
    # External packages will be automatically registered when components reference them
    # Depth 0: common
    common = Component(
        name="common",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="java",
        relative_path=Path("common/target/common.jar"),
        source_files=[
            Path("common/src/main/java/com/example/common/CommonUtils.java")
        ],
        external_packages=[external_packages[0], external_packages[1], external_packages[7], external_packages[8]],  # guava, slf4j-api, junit-jupiter, mockito-core
        evidence=[Evidence(line=["common/pom.xml:14"])],  # artifactId line
        locations=[],
    )

    # Depth 1: domain, integration-email, integration-storage
    domain = Component(
        name="domain",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="java",
        relative_path=Path("domain/target/domain.jar"),
        source_files=[
            Path("domain/src/main/java/com/example/domain/Task.java"),
            Path("domain/src/main/java/com/example/domain/User.java"),
        ],
        external_packages=[external_packages[3]],  # jackson-databind
        evidence=[Evidence(line=["domain/pom.xml:14"])],  # artifactId line
        locations=[],
        depends_on=[common],
    )

    integration_email = Component(
        name="integration-email",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="java",
        relative_path=Path("integration-email/target/integration-email.jar"),
        source_files=[
            Path("integration-email/src/main/java/com/example/email/EmailService.java")
        ],
        external_packages=[],
        evidence=[Evidence(line=["integration-email/pom.xml:14"])],  # artifactId line
        locations=[],
        depends_on=[common],
    )

    integration_storage = Component(
        name="integration-storage",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="java",
        relative_path=Path("integration-storage/target/integration-storage.jar"),
        source_files=[
            Path("integration-storage/src/main/java/com/example/storage/StorageService.java")
        ],
        external_packages=[],
        evidence=[Evidence(line=["integration-storage/pom.xml:14"])],  # artifactId line
        locations=[],
        depends_on=[common],
    )

    # Depth 2: persistence, service-auth, service-notification
    persistence = Component(
        name="persistence",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="java",
        relative_path=Path("persistence/target/persistence.jar"),
        source_files=[
            Path("persistence/src/main/java/com/example/persistence/TaskRepository.java")
        ],
        external_packages=[external_packages[5], external_packages[6]],  # hibernate-core, h2
        evidence=[Evidence(line=["persistence/pom.xml:14"])],  # artifactId line
        locations=[],
        depends_on=[domain, common],
    )

    service_auth = Component(
        name="service-auth",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="java",
        relative_path=Path("service-auth/target/service-auth.jar"),
        source_files=[
            Path("service-auth/src/main/java/com/example/auth/AuthService.java")
        ],
        external_packages=[],
        evidence=[Evidence(line=["service-auth/pom.xml:14"])],  # artifactId line
        locations=[],
        depends_on=[domain, common],
    )

    service_notification = Component(
        name="service-notification",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="java",
        relative_path=Path("service-notification/target/service-notification.jar"),
        source_files=[
            Path("service-notification/src/main/java/com/example/notification/NotificationService.java")
        ],
        external_packages=[],
        evidence=[Evidence(line=["service-notification/pom.xml:14"])],  # artifactId line
        locations=[],
        depends_on=[domain, common],
    )

    # Depth 3: service-task, api-gateway
    service_task = Component(
        name="service-task",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="java",
        relative_path=Path("service-task/target/service-task.jar"),
        source_files=[
            Path("service-task/src/main/java/com/example/task/TaskService.java")
        ],
        external_packages=[],
        evidence=[Evidence(line=["service-task/pom.xml:14"])],  # artifactId line
        locations=[],
        depends_on=[persistence, domain, common],
    )

    api_gateway = Component(
        name="api-gateway",
        type=ComponentType.STATIC_LIBRARY,
        programming_language="java",
        relative_path=Path("api-gateway/target/api-gateway.jar"),
        source_files=[
            Path("api-gateway/src/main/java/com/example/api/TaskController.java")
        ],
        external_packages=[external_packages[4]],  # spring-web
        evidence=[Evidence(line=["api-gateway/pom.xml:14"])],  # artifactId line
        locations=[],
        depends_on=[service_task, service_auth, service_notification, domain, common],
    )

    # Depth 4: app-web
    app_web = Component(
        name="app-web",
        type=ComponentType.SHARED_LIBRARY,  # WAR file
        programming_language="java",
        relative_path=Path("app-web/target/app-web.war"),
        source_files=[
            Path("app-web/src/main/java/com/example/web/WebApplication.java"),
            Path("app-web/src/main/webapp/WEB-INF/web.xml"),
        ],
        external_packages=[external_packages[2], external_packages[9]],  # logback-classic, jakarta-servlet-api
        evidence=[Evidence(line=["app-web/pom.xml:14"])],  # artifactId line
        locations=[],
        depends_on=[api_gateway, integration_email, integration_storage, service_task, service_auth, service_notification, persistence, domain, common],
    )

    # Create root aggregator (Maven multi-module POM)
    task_manager_aggregator = Aggregator(
        name="task-manager",
        depends_on=[common, domain, integration_email, integration_storage,
                    persistence, service_auth, service_notification,
                    service_task, api_gateway, app_web],
        evidence=[Evidence(line=["pom.xml:11"])],  # <packaging>pom</packaging>
    )

    # Add all components to RIG
    rig.add_component(common)
    rig.add_component(domain)
    rig.add_component(integration_email)
    rig.add_component(integration_storage)
    rig.add_component(persistence)
    rig.add_component(service_auth)
    rig.add_component(service_notification)
    rig.add_component(service_task)
    rig.add_component(api_gateway)
    rig.add_component(app_web)

    # Add root aggregator to RIG
    rig.add_aggregator(task_manager_aggregator)

    # Create test definitions (10 tests, one per module)
    # For Maven, the test executable is the component being tested (Maven runs tests as part of component build)
    tests = [
        TestDefinition(
            name="CommonUtilsTest",
            test_executable_component=common,
            test_executable_component_id=None,
            test_components=[],
            components_being_tested=[common],
            test_framework="JUnit5",
            source_files=[Path("common/src/test/java/com/example/common/CommonUtilsTest.java")],
            evidence=[Evidence(line=["common/src/test/java/com/example/common/CommonUtilsTest.java:8"])],  # void testSanitize()
        ),
        TestDefinition(
            name="DomainModelTest",
            test_executable_component=domain,
            test_executable_component_id=None,
            test_components=[],
            components_being_tested=[domain],
            test_framework="JUnit5",
            source_files=[Path("domain/src/test/java/com/example/domain/DomainModelTest.java")],
            evidence=[Evidence(line=["domain/src/test/java/com/example/domain/DomainModelTest.java:8"])],  # void testTask()
        ),
        TestDefinition(
            name="PersistenceServiceTest",
            test_executable_component=persistence,
            test_executable_component_id=None,
            test_components=[],
            components_being_tested=[persistence],
            test_framework="JUnit5",
            source_files=[Path("persistence/src/test/java/com/example/persistence/PersistenceServiceTest.java")],
            evidence=[Evidence(line=["persistence/src/test/java/com/example/persistence/PersistenceServiceTest.java:10"])],  # void testTaskRepository()
        ),
        TestDefinition(
            name="AuthServiceTest",
            test_executable_component=service_auth,
            test_executable_component_id=None,
            test_components=[],
            components_being_tested=[service_auth],
            test_framework="JUnit5",
            source_files=[Path("service-auth/src/test/java/com/example/auth/AuthServiceTest.java")],
            evidence=[Evidence(line=["service-auth/src/test/java/com/example/auth/AuthServiceTest.java:10"])],  # void testAuthenticate()
        ),
        TestDefinition(
            name="TaskServiceTest",
            test_executable_component=service_task,
            test_executable_component_id=None,
            test_components=[],
            components_being_tested=[service_task],
            test_framework="JUnit5",
            source_files=[Path("service-task/src/test/java/com/example/task/TaskServiceTest.java")],
            evidence=[Evidence(line=["service-task/src/test/java/com/example/task/TaskServiceTest.java:11"])],  # void testCreateTask()
        ),
        TestDefinition(
            name="NotificationServiceTest",
            test_executable_component=service_notification,
            test_executable_component_id=None,
            test_components=[],
            components_being_tested=[service_notification],
            test_framework="JUnit5",
            source_files=[Path("service-notification/src/test/java/com/example/notification/NotificationServiceTest.java")],
            evidence=[Evidence(line=["service-notification/src/test/java/com/example/notification/NotificationServiceTest.java:9"])],  # void testSendNotification()
        ),
        TestDefinition(
            name="ApiGatewayTest",
            test_executable_component=api_gateway,
            test_executable_component_id=None,
            test_components=[],
            components_being_tested=[api_gateway],
            test_framework="JUnit5",
            source_files=[Path("api-gateway/src/test/java/com/example/api/ApiGatewayTest.java")],
            evidence=[Evidence(line=["api-gateway/src/test/java/com/example/api/ApiGatewayTest.java:13"])],  # void testTaskController()
        ),
        TestDefinition(
            name="EmailIntegrationTest",
            test_executable_component=integration_email,
            test_executable_component_id=None,
            test_components=[],
            components_being_tested=[integration_email],
            test_framework="JUnit5",
            source_files=[Path("integration-email/src/test/java/com/example/email/EmailIntegrationTest.java")],
            evidence=[Evidence(line=["integration-email/src/test/java/com/example/email/EmailIntegrationTest.java:8"])],  # void testSendEmail()
        ),
        TestDefinition(
            name="StorageIntegrationTest",
            test_executable_component=integration_storage,
            test_executable_component_id=None,
            test_components=[],
            components_being_tested=[integration_storage],
            test_framework="JUnit5",
            source_files=[Path("integration-storage/src/test/java/com/example/storage/StorageIntegrationTest.java")],
            evidence=[Evidence(line=["integration-storage/src/test/java/com/example/storage/StorageIntegrationTest.java:8"])],  # void testSaveFile()
        ),
        TestDefinition(
            name="WebAppIntegrationTest",
            test_executable_component=app_web,
            test_executable_component_id=None,
            test_components=[],
            components_being_tested=[app_web],
            test_framework="JUnit5",
            source_files=[Path("app-web/src/test/java/com/example/web/WebAppIntegrationTest.java")],
            evidence=[Evidence(line=["app-web/src/test/java/com/example/web/WebAppIntegrationTest.java:8"])],  # void testWebApplication()
        ),
    ]

    # Add all tests to RIG
    for test in tests:
        rig.add_test(test)

    # Validate before saving/writing outputs (fail-fast on errors)
    validation_errors = rig.validate()
    if len(validation_errors) > 0:
        # print validation errors
        for error in validation_errors:
            print(f"""Validation Error ({error.category}):
    File: {error.file_path}
    Message: {error.message}
    Node Name: {error.node_name}
""")
        raise RIGValidationError(validation_errors)

    # Note: Complexity calculation can be verified separately using the generated JSON file
    # Expected: 10 components, 1 language, 10 external packages, depth 4, 1 aggregator, no cross-language
    # Raw score: (10×2) + (1×10) + (10×3) + (4×8) + (1×5) + 0 = 20 + 10 + 30 + 32 + 5 + 0 = 97
    # Normalized: (97 / 229) × 100 ≈ 42.4

    # Save to SQLite
    sqlite_path = Path(__file__).parent / "task_manager_ground_truth.sqlite3"
    rig.save(sqlite_path)
    print(f"\nSaved RIG to: {sqlite_path}")

    # Write JSON prompt (unoptimized for readability in ground-truth)
    json_path = Path(__file__).parent / "task_manager_ground_truth.json"
    rig_json_ground_truth = rig.generate_prompts_json_data()
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(rig_json_ground_truth)
    print(f"Saved JSON to: {json_path}")

    # Load from SQLite into a new RIG instance and compare
    # to make sure there's no serialization/deserialization issues
    rig_loaded = RIG.load(sqlite_path)

    # Use the new compare() method
    diff_text = rig.compare(rig_loaded)
    if diff_text:
        raise ValueError(f"Loaded RIG does not match ground truth:\n{diff_text}")



if __name__ == "__main__":
    main()
