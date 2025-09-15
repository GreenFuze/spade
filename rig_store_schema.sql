-- RIG SQLite Database Schema
-- Repository Intelligence Graph storage schema

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
    rig_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    root_path TEXT NOT NULL,
    build_directory TEXT NOT NULL,
    output_directory TEXT NOT NULL,
    configure_command TEXT NOT NULL,
    build_command TEXT NOT NULL,
    install_command TEXT NOT NULL,
    test_command TEXT NOT NULL,
    FOREIGN KEY (rig_id) REFERENCES rig_metadata(id) ON DELETE CASCADE
);

-- Build system information
CREATE TABLE build_system_info (
    id INTEGER PRIMARY KEY,
    rig_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    version TEXT,
    build_type TEXT,
    FOREIGN KEY (rig_id) REFERENCES rig_metadata(id) ON DELETE CASCADE
);

-- ==============================================
-- EVIDENCE AND SUPPORTING DATA TABLES
-- ==============================================

-- Evidence with call stacks (stored as JSON for flexibility)
CREATE TABLE evidence (
    id INTEGER PRIMARY KEY,
    rig_id INTEGER NOT NULL,
    call_stack_json TEXT NOT NULL, -- JSON array of call stack strings
    FOREIGN KEY (rig_id) REFERENCES rig_metadata(id) ON DELETE CASCADE
);

-- Package manager information
CREATE TABLE package_managers (
    id INTEGER PRIMARY KEY,
    rig_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    package_name TEXT NOT NULL,
    FOREIGN KEY (rig_id) REFERENCES rig_metadata(id) ON DELETE CASCADE
);

-- External package dependencies
CREATE TABLE external_packages (
    id INTEGER PRIMARY KEY,
    rig_id INTEGER NOT NULL,
    package_manager_id INTEGER NOT NULL,
    FOREIGN KEY (rig_id) REFERENCES rig_metadata(id) ON DELETE CASCADE,
    FOREIGN KEY (package_manager_id) REFERENCES package_managers(id) ON DELETE CASCADE
);

-- Component locations
CREATE TABLE component_locations (
    id INTEGER PRIMARY KEY,
    rig_id INTEGER NOT NULL,
    path TEXT NOT NULL,
    action TEXT NOT NULL,
    source_location_id INTEGER,
    evidence_id INTEGER NOT NULL,
    FOREIGN KEY (rig_id) REFERENCES rig_metadata(id) ON DELETE CASCADE,
    FOREIGN KEY (source_location_id) REFERENCES component_locations(id) ON DELETE SET NULL,
    FOREIGN KEY (evidence_id) REFERENCES evidence(id) ON DELETE CASCADE
);

-- ==============================================
-- ENTITY TABLES
-- ==============================================

-- Build components (executables, libraries, etc.)
CREATE TABLE components (
    id INTEGER PRIMARY KEY,
    rig_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL, -- ComponentType enum
    runtime TEXT, -- Runtime enum
    output TEXT NOT NULL,
    output_path TEXT NOT NULL,
    programming_language TEXT NOT NULL,
    evidence_id INTEGER NOT NULL,
    test_link_id INTEGER,
    test_link_name TEXT,
    FOREIGN KEY (rig_id) REFERENCES rig_metadata(id) ON DELETE CASCADE,
    FOREIGN KEY (evidence_id) REFERENCES evidence(id) ON DELETE CASCADE,
    FOREIGN KEY (test_link_id) REFERENCES tests(id) ON DELETE SET NULL
);

-- Build aggregators
CREATE TABLE aggregators (
    id INTEGER PRIMARY KEY,
    rig_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    evidence_id INTEGER NOT NULL,
    FOREIGN KEY (rig_id) REFERENCES rig_metadata(id) ON DELETE CASCADE,
    FOREIGN KEY (evidence_id) REFERENCES evidence(id) ON DELETE CASCADE
);

-- Build runners
CREATE TABLE runners (
    id INTEGER PRIMARY KEY,
    rig_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    evidence_id INTEGER NOT NULL,
    FOREIGN KEY (rig_id) REFERENCES rig_metadata(id) ON DELETE CASCADE,
    FOREIGN KEY (evidence_id) REFERENCES evidence(id) ON DELETE CASCADE
);

-- Build utilities
CREATE TABLE utilities (
    id INTEGER PRIMARY KEY,
    rig_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    evidence_id INTEGER NOT NULL,
    FOREIGN KEY (rig_id) REFERENCES rig_metadata(id) ON DELETE CASCADE,
    FOREIGN KEY (evidence_id) REFERENCES evidence(id) ON DELETE CASCADE
);

-- Test definitions
CREATE TABLE tests (
    id INTEGER PRIMARY KEY,
    rig_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    test_executable_id INTEGER,
    test_runner_id INTEGER,
    test_framework TEXT NOT NULL,
    evidence_id INTEGER NOT NULL,
    FOREIGN KEY (rig_id) REFERENCES rig_metadata(id) ON DELETE CASCADE,
    FOREIGN KEY (test_executable_id) REFERENCES components(id) ON DELETE SET NULL,
    FOREIGN KEY (test_runner_id) REFERENCES runners(id) ON DELETE SET NULL,
    FOREIGN KEY (evidence_id) REFERENCES evidence(id) ON DELETE CASCADE
);

-- ==============================================
-- RELATIONSHIP TABLES
-- ==============================================

-- Component dependencies (many-to-many)
CREATE TABLE component_dependencies (
    id INTEGER PRIMARY KEY,
    rig_id INTEGER NOT NULL,
    component_id INTEGER NOT NULL,
    depends_on_component_id INTEGER,
    depends_on_aggregator_id INTEGER,
    depends_on_runner_id INTEGER,
    depends_on_utility_id INTEGER,
    FOREIGN KEY (rig_id) REFERENCES rig_metadata(id) ON DELETE CASCADE,
    FOREIGN KEY (component_id) REFERENCES components(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_component_id) REFERENCES components(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_aggregator_id) REFERENCES aggregators(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_runner_id) REFERENCES runners(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_utility_id) REFERENCES utilities(id) ON DELETE CASCADE,
    CHECK (
        (depends_on_component_id IS NOT NULL AND depends_on_aggregator_id IS NULL AND depends_on_runner_id IS NULL AND depends_on_utility_id IS NULL) OR
        (depends_on_component_id IS NULL AND depends_on_aggregator_id IS NOT NULL AND depends_on_runner_id IS NULL AND depends_on_utility_id IS NULL) OR
        (depends_on_component_id IS NULL AND depends_on_aggregator_id IS NULL AND depends_on_runner_id IS NOT NULL AND depends_on_utility_id IS NULL) OR
        (depends_on_component_id IS NULL AND depends_on_aggregator_id IS NULL AND depends_on_runner_id IS NULL AND depends_on_utility_id IS NOT NULL)
    )
);

-- Aggregator dependencies
CREATE TABLE aggregator_dependencies (
    id INTEGER PRIMARY KEY,
    rig_id INTEGER NOT NULL,
    aggregator_id INTEGER NOT NULL,
    depends_on_component_id INTEGER,
    depends_on_aggregator_id INTEGER,
    depends_on_runner_id INTEGER,
    depends_on_utility_id INTEGER,
    FOREIGN KEY (rig_id) REFERENCES rig_metadata(id) ON DELETE CASCADE,
    FOREIGN KEY (aggregator_id) REFERENCES aggregators(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_component_id) REFERENCES components(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_aggregator_id) REFERENCES aggregators(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_runner_id) REFERENCES runners(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_utility_id) REFERENCES utilities(id) ON DELETE CASCADE,
    CHECK (
        (depends_on_component_id IS NOT NULL AND depends_on_aggregator_id IS NULL AND depends_on_runner_id IS NULL AND depends_on_utility_id IS NULL) OR
        (depends_on_component_id IS NULL AND depends_on_aggregator_id IS NOT NULL AND depends_on_runner_id IS NULL AND depends_on_utility_id IS NULL) OR
        (depends_on_component_id IS NULL AND depends_on_aggregator_id IS NULL AND depends_on_runner_id IS NOT NULL AND depends_on_utility_id IS NULL) OR
        (depends_on_component_id IS NULL AND depends_on_aggregator_id IS NULL AND depends_on_runner_id IS NULL AND depends_on_utility_id IS NOT NULL)
    )
);

-- Runner dependencies
CREATE TABLE runner_dependencies (
    id INTEGER PRIMARY KEY,
    rig_id INTEGER NOT NULL,
    runner_id INTEGER NOT NULL,
    depends_on_component_id INTEGER,
    depends_on_aggregator_id INTEGER,
    depends_on_runner_id INTEGER,
    depends_on_utility_id INTEGER,
    FOREIGN KEY (rig_id) REFERENCES rig_metadata(id) ON DELETE CASCADE,
    FOREIGN KEY (runner_id) REFERENCES runners(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_component_id) REFERENCES components(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_aggregator_id) REFERENCES aggregators(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_runner_id) REFERENCES runners(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_utility_id) REFERENCES utilities(id) ON DELETE CASCADE,
    CHECK (
        (depends_on_component_id IS NOT NULL AND depends_on_aggregator_id IS NULL AND depends_on_runner_id IS NULL AND depends_on_utility_id IS NULL) OR
        (depends_on_component_id IS NULL AND depends_on_aggregator_id IS NOT NULL AND depends_on_runner_id IS NULL AND depends_on_utility_id IS NULL) OR
        (depends_on_component_id IS NULL AND depends_on_aggregator_id IS NULL AND depends_on_runner_id IS NOT NULL AND depends_on_utility_id IS NULL) OR
        (depends_on_component_id IS NULL AND depends_on_aggregator_id IS NULL AND depends_on_runner_id IS NULL AND depends_on_utility_id IS NOT NULL)
    )
);

-- Utility dependencies
CREATE TABLE utility_dependencies (
    id INTEGER PRIMARY KEY,
    rig_id INTEGER NOT NULL,
    utility_id INTEGER NOT NULL,
    depends_on_component_id INTEGER,
    depends_on_aggregator_id INTEGER,
    depends_on_runner_id INTEGER,
    depends_on_utility_id INTEGER,
    FOREIGN KEY (rig_id) REFERENCES rig_metadata(id) ON DELETE CASCADE,
    FOREIGN KEY (utility_id) REFERENCES utilities(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_component_id) REFERENCES components(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_aggregator_id) REFERENCES aggregators(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_runner_id) REFERENCES runners(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_utility_id) REFERENCES utilities(id) ON DELETE CASCADE,
    CHECK (
        (depends_on_component_id IS NOT NULL AND depends_on_aggregator_id IS NULL AND depends_on_runner_id IS NULL AND depends_on_utility_id IS NULL) OR
        (depends_on_component_id IS NULL AND depends_on_aggregator_id IS NOT NULL AND depends_on_runner_id IS NULL AND depends_on_utility_id IS NULL) OR
        (depends_on_component_id IS NULL AND depends_on_aggregator_id IS NULL AND depends_on_runner_id IS NOT NULL AND depends_on_utility_id IS NULL) OR
        (depends_on_component_id IS NULL AND depends_on_aggregator_id IS NULL AND depends_on_runner_id IS NULL AND depends_on_utility_id IS NOT NULL)
    )
);

-- Test component relationships
CREATE TABLE test_components (
    id INTEGER PRIMARY KEY,
    rig_id INTEGER NOT NULL,
    test_id INTEGER NOT NULL,
    component_id INTEGER NOT NULL,
    FOREIGN KEY (rig_id) REFERENCES rig_metadata(id) ON DELETE CASCADE,
    FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE,
    FOREIGN KEY (component_id) REFERENCES components(id) ON DELETE CASCADE
);

-- Component source files
CREATE TABLE component_source_files (
    id INTEGER PRIMARY KEY,
    rig_id INTEGER NOT NULL,
    component_id INTEGER NOT NULL,
    source_file_path TEXT NOT NULL,
    FOREIGN KEY (rig_id) REFERENCES rig_metadata(id) ON DELETE CASCADE,
    FOREIGN KEY (component_id) REFERENCES components(id) ON DELETE CASCADE
);

-- Test source files
CREATE TABLE test_source_files (
    id INTEGER PRIMARY KEY,
    rig_id INTEGER NOT NULL,
    test_id INTEGER NOT NULL,
    source_file_path TEXT NOT NULL,
    FOREIGN KEY (rig_id) REFERENCES rig_metadata(id) ON DELETE CASCADE,
    FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE
);

-- Component external packages
CREATE TABLE component_external_packages (
    id INTEGER PRIMARY KEY,
    rig_id INTEGER NOT NULL,
    component_id INTEGER NOT NULL,
    external_package_id INTEGER NOT NULL,
    FOREIGN KEY (rig_id) REFERENCES rig_metadata(id) ON DELETE CASCADE,
    FOREIGN KEY (component_id) REFERENCES components(id) ON DELETE CASCADE,
    FOREIGN KEY (external_package_id) REFERENCES external_packages(id) ON DELETE CASCADE
);

-- Component locations relationships
CREATE TABLE component_locations_rel (
    id INTEGER PRIMARY KEY,
    rig_id INTEGER NOT NULL,
    component_id INTEGER NOT NULL,
    location_id INTEGER NOT NULL,
    FOREIGN KEY (rig_id) REFERENCES rig_metadata(id) ON DELETE CASCADE,
    FOREIGN KEY (component_id) REFERENCES components(id) ON DELETE CASCADE,
    FOREIGN KEY (location_id) REFERENCES component_locations(id) ON DELETE CASCADE
);

-- ==============================================
-- INDEXES FOR PERFORMANCE
-- ==============================================

-- Primary entity indexes
CREATE INDEX idx_components_name ON components(name);
CREATE INDEX idx_components_type ON components(type);
CREATE INDEX idx_aggregators_name ON aggregators(name);
CREATE INDEX idx_runners_name ON runners(name);
CREATE INDEX idx_utilities_name ON utilities(name);
CREATE INDEX idx_tests_name ON tests(name);

-- Relationship indexes
CREATE INDEX idx_component_deps_component ON component_dependencies(component_id);
CREATE INDEX idx_component_deps_depends ON component_dependencies(depends_on_component_id, depends_on_aggregator_id, depends_on_runner_id, depends_on_utility_id);
CREATE INDEX idx_aggregator_deps_aggregator ON aggregator_dependencies(aggregator_id);
CREATE INDEX idx_runner_deps_runner ON runner_dependencies(runner_id);
CREATE INDEX idx_utility_deps_utility ON utility_dependencies(utility_id);
CREATE INDEX idx_test_components_test ON test_components(test_id);
CREATE INDEX idx_test_components_component ON test_components(component_id);

-- Evidence and supporting data indexes
CREATE INDEX idx_evidence_rig ON evidence(rig_id);
CREATE INDEX idx_package_managers_rig ON package_managers(rig_id);
CREATE INDEX idx_external_packages_rig ON external_packages(rig_id);
CREATE INDEX idx_component_locations_rig ON component_locations(rig_id);

-- ==============================================
-- TRIGGERS FOR UPDATED_AT
-- ==============================================

CREATE TRIGGER update_rig_metadata_updated_at
    AFTER UPDATE ON rig_metadata
    FOR EACH ROW
    BEGIN
        UPDATE rig_metadata SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;
