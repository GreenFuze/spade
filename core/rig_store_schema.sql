-- RIG SQLite Database Schema
-- Repository Intelligence Graph storage schema
-- Aligned with schemas.py structure
-- Design: One RIG per database (no rig_id needed)

-- ==============================================
-- CORE METADATA TABLES
-- ==============================================

-- Single row table for RIG metadata
CREATE TABLE rig_metadata (
    id INTEGER PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version TEXT NOT NULL DEFAULT '1.0',
    description TEXT
);

-- Repository-level information
CREATE TABLE repository_info (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    root_path TEXT NOT NULL,
    build_directory TEXT,  -- Optional
    output_directory TEXT,  -- Optional
    install_directory TEXT,  -- Optional
    configure_command TEXT,  -- Optional
    build_command TEXT,  -- Optional
    install_command TEXT,  -- Optional
    test_command TEXT  -- Optional
);

-- Build system information
CREATE TABLE build_system_info (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT,
    build_type TEXT
);

-- ==============================================
-- EVIDENCE AND SUPPORTING DATA TABLES
-- ==============================================

-- Evidence with both line and call_stack (stored as JSON for flexibility)
CREATE TABLE evidence (
    id INTEGER PRIMARY KEY,
    evidence_string_id TEXT NOT NULL,  -- The original string ID from Evidence.id
    line_json TEXT,  -- JSON array of line strings (can be NULL)
    call_stack_json TEXT,  -- JSON array of call stack strings (can be NULL)
    CHECK (line_json IS NOT NULL OR call_stack_json IS NOT NULL)
);

-- Package manager information
CREATE TABLE package_managers (
    id INTEGER PRIMARY KEY,
    pm_string_id TEXT NOT NULL,  -- The original string ID from PackageManager.id
    name TEXT NOT NULL,
    package_name TEXT NOT NULL
);

-- External package dependencies
CREATE TABLE external_packages (
    id INTEGER PRIMARY KEY,
    ep_string_id TEXT NOT NULL,  -- The original string ID from ExternalPackage.id
    name TEXT NOT NULL,
    package_manager_id INTEGER NOT NULL,
    FOREIGN KEY (package_manager_id) REFERENCES package_managers(id) ON DELETE CASCADE
);

-- ==============================================
-- ENTITY TABLES
-- ==============================================

-- Build components (executables, libraries, etc.)
CREATE TABLE components (
    id INTEGER PRIMARY KEY,
    comp_string_id TEXT NOT NULL,  -- The original string ID from Component.id
    name TEXT NOT NULL,
    type TEXT NOT NULL, -- ComponentType enum
    relative_path TEXT NOT NULL,  -- From Artifact.relative_path
    programming_language TEXT NOT NULL
);

-- Build aggregators
CREATE TABLE aggregators (
    id INTEGER PRIMARY KEY,
    agg_string_id TEXT NOT NULL,  -- The original string ID from Aggregator.id
    name TEXT NOT NULL
);

-- Build runners
CREATE TABLE runners (
    id INTEGER PRIMARY KEY,
    runner_string_id TEXT NOT NULL,  -- The original string ID from Runner.id
    name TEXT NOT NULL,
    arguments_json TEXT  -- JSON array of command-line arguments (can be NULL)
);

-- Test definitions
CREATE TABLE tests (
    id INTEGER PRIMARY KEY,
    test_string_id TEXT NOT NULL,  -- The original string ID from TestDefinition.id
    name TEXT NOT NULL,
    test_executable_component_id INTEGER,  -- Can reference component OR runner
    test_executable_type TEXT,  -- 'component' or 'runner'
    test_framework TEXT NOT NULL,
    CHECK (test_executable_type IN ('component', 'runner', NULL))
);

-- ==============================================
-- RELATIONSHIP TABLES
-- ==============================================

-- Node evidence relationships (many-to-many)
-- Each node (component/aggregator/runner/test) can have multiple evidence
CREATE TABLE node_evidence (
    id INTEGER PRIMARY KEY,
    node_type TEXT NOT NULL,  -- 'component', 'aggregator', 'runner', 'test'
    node_id INTEGER NOT NULL,  -- References the appropriate table
    evidence_id INTEGER NOT NULL,
    FOREIGN KEY (evidence_id) REFERENCES evidence(id) ON DELETE CASCADE,
    CHECK (node_type IN ('component', 'aggregator', 'runner', 'test'))
);

-- Component dependencies (many-to-many)
CREATE TABLE component_dependencies (
    id INTEGER PRIMARY KEY,
    component_id INTEGER NOT NULL,
    depends_on_type TEXT NOT NULL,  -- 'component', 'aggregator', 'runner'
    depends_on_id INTEGER NOT NULL,
    FOREIGN KEY (component_id) REFERENCES components(id) ON DELETE CASCADE,
    CHECK (depends_on_type IN ('component', 'aggregator', 'runner'))
);

-- Aggregator dependencies
CREATE TABLE aggregator_dependencies (
    id INTEGER PRIMARY KEY,
    aggregator_id INTEGER NOT NULL,
    depends_on_type TEXT NOT NULL,  -- 'component', 'aggregator', 'runner'
    depends_on_id INTEGER NOT NULL,
    FOREIGN KEY (aggregator_id) REFERENCES aggregators(id) ON DELETE CASCADE,
    CHECK (depends_on_type IN ('component', 'aggregator', 'runner'))
);

-- Runner dependencies
CREATE TABLE runner_dependencies (
    id INTEGER PRIMARY KEY,
    runner_id INTEGER NOT NULL,
    depends_on_type TEXT NOT NULL,  -- 'component', 'aggregator', 'runner'
    depends_on_id INTEGER NOT NULL,
    FOREIGN KEY (runner_id) REFERENCES runners(id) ON DELETE CASCADE,
    CHECK (depends_on_type IN ('component', 'aggregator', 'runner'))
);

-- Runner argument nodes (args_nodes list)
CREATE TABLE runner_args_nodes (
    id INTEGER PRIMARY KEY,
    runner_id INTEGER NOT NULL,
    args_node_type TEXT NOT NULL,  -- 'component', 'aggregator', 'runner', 'test'
    args_node_id INTEGER NOT NULL,
    FOREIGN KEY (runner_id) REFERENCES runners(id) ON DELETE CASCADE,
    CHECK (args_node_type IN ('component', 'aggregator', 'runner', 'test'))
);

-- Test dependencies
CREATE TABLE test_dependencies (
    id INTEGER PRIMARY KEY,
    test_id INTEGER NOT NULL,
    depends_on_type TEXT NOT NULL,  -- 'component', 'aggregator', 'runner'
    depends_on_id INTEGER NOT NULL,
    FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE,
    CHECK (depends_on_type IN ('component', 'aggregator', 'runner'))
);

-- Test components (test_components list)
CREATE TABLE test_components (
    id INTEGER PRIMARY KEY,
    test_id INTEGER NOT NULL,
    component_id INTEGER NOT NULL,
    FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE,
    FOREIGN KEY (component_id) REFERENCES components(id) ON DELETE CASCADE
);

-- Components being tested (components_being_tested list)
CREATE TABLE test_components_being_tested (
    id INTEGER PRIMARY KEY,
    test_id INTEGER NOT NULL,
    component_id INTEGER NOT NULL,
    FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE,
    FOREIGN KEY (component_id) REFERENCES components(id) ON DELETE CASCADE
);

-- Component source files
CREATE TABLE component_source_files (
    id INTEGER PRIMARY KEY,
    component_id INTEGER NOT NULL,
    source_file_path TEXT NOT NULL,
    FOREIGN KEY (component_id) REFERENCES components(id) ON DELETE CASCADE
);

-- Test source files
CREATE TABLE test_source_files (
    id INTEGER PRIMARY KEY,
    test_id INTEGER NOT NULL,
    source_file_path TEXT NOT NULL,
    FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE
);

-- Component external packages
CREATE TABLE component_external_packages (
    id INTEGER PRIMARY KEY,
    component_id INTEGER NOT NULL,
    external_package_id INTEGER NOT NULL,
    FOREIGN KEY (component_id) REFERENCES components(id) ON DELETE CASCADE,
    FOREIGN KEY (external_package_id) REFERENCES external_packages(id) ON DELETE CASCADE
);

-- Component locations (simple list of paths)
CREATE TABLE component_locations (
    id INTEGER PRIMARY KEY,
    component_id INTEGER NOT NULL,
    location_path TEXT NOT NULL,
    FOREIGN KEY (component_id) REFERENCES components(id) ON DELETE CASCADE
);

-- ==============================================
-- INDEXES FOR PERFORMANCE
-- ==============================================

-- Primary entity indexes
CREATE INDEX idx_components_name ON components(name);
CREATE INDEX idx_components_type ON components(type);
CREATE INDEX idx_aggregators_name ON aggregators(name);
CREATE INDEX idx_runners_name ON runners(name);
CREATE INDEX idx_tests_name ON tests(name);

-- String ID indexes for lookups
CREATE INDEX idx_components_string_id ON components(comp_string_id);
CREATE INDEX idx_aggregators_string_id ON aggregators(agg_string_id);
CREATE INDEX idx_runners_string_id ON runners(runner_string_id);
CREATE INDEX idx_tests_string_id ON tests(test_string_id);
CREATE INDEX idx_evidence_string_id ON evidence(evidence_string_id);
CREATE INDEX idx_package_managers_string_id ON package_managers(pm_string_id);
CREATE INDEX idx_external_packages_string_id ON external_packages(ep_string_id);

-- Relationship indexes
CREATE INDEX idx_node_evidence_node ON node_evidence(node_type, node_id);
CREATE INDEX idx_node_evidence_evidence ON node_evidence(evidence_id);
CREATE INDEX idx_component_deps_component ON component_dependencies(component_id);
CREATE INDEX idx_aggregator_deps_aggregator ON aggregator_dependencies(aggregator_id);
CREATE INDEX idx_runner_deps_runner ON runner_dependencies(runner_id);
CREATE INDEX idx_runner_args_nodes_runner ON runner_args_nodes(runner_id);
CREATE INDEX idx_test_deps_test ON test_dependencies(test_id);
CREATE INDEX idx_test_components_test ON test_components(test_id);
CREATE INDEX idx_test_components_being_tested_test ON test_components_being_tested(test_id);

-- ==============================================
-- TRIGGERS FOR UPDATED_AT
-- ==============================================

CREATE TRIGGER update_rig_metadata_updated_at
    AFTER UPDATE ON rig_metadata
    FOR EACH ROW
    BEGIN
        UPDATE rig_metadata SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;
