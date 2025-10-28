"""
RIG SQLite Storage Module

This module provides functionality to save and load RIG objects to/from SQLite databases.
It handles the complete serialization and deserialization of RIG data structures.

Design: One RIG per database
- Each SQLite database contains exactly one RIG
- save_rig() replaces any existing RIG in the database
- load_rig() loads the single RIG from the database

Key Concepts:
- String IDs: Objects have string IDs like "comp-1", "evidence-1"
- Database IDs: SQLite uses integer primary keys
- During SAVE: Maps string ID → integer database ID
- During LOAD: Maps integer database ID → object, reconstructs string IDs
"""

import json
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Tuple
from contextlib import contextmanager

from core.rig import RIG
from core.schemas import (
    Component, Aggregator, Runner, TestDefinition, Evidence,
    ExternalPackage, PackageManager, RepositoryInfo,
    BuildSystemInfo, ComponentType
)


class RIGStore:
    """SQLite storage for RIG objects (one RIG per database)."""

    def __init__(self, db_path: Union[str, Path]):
        """Initialize RIG store with database path."""
        self.db_path = Path(db_path)
        self._ensure_database_exists()

    def _ensure_database_exists(self) -> None:
        """Create database and tables if they don't exist."""
        with self._get_connection() as conn:
            # Check if tables already exist
            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='rig_metadata'
            """)
            if cursor.fetchone() is None:
                # Tables don't exist, create them
                with open(Path(__file__).parent / 'rig_store_schema.sql', 'r') as f:
                    schema_sql = f.read()
                conn.executescript(schema_sql)

    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ==============================================
    # SAVE METHODS
    # ==============================================

    def save_rig(self, rig: RIG, description: str = "RIG Export") -> None:
        """
        Save RIG object to SQLite database.
        Replaces any existing RIG in the database.

        Args:
            rig: RIG object to save
            description: Description for this RIG export
        """
        with self._get_connection() as conn:
            # Clear all existing data (cascade delete will handle relationships)
            self._clear_database(conn)

            # Insert RIG metadata with id=1
            self._save_rig_metadata(conn, description)

            # Save repository info
            if rig._repository_info:
                self._save_repository_info(conn, rig._repository_info)

            # Save build system info
            if rig._build_system_info:
                self._save_build_system_info(conn, rig._build_system_info)

            # Get entity lists from RIG (using *_by_id.values())
            evidence_list = list(rig._evidence_by_id.values())
            pm_list = list(rig._package_managers_by_id.values())
            ep_list = list(rig._external_packages_by_id.values())

            # Save evidence first (referenced by nodes)
            # Returns Dict[str, int] mapping string ID → database ID
            evidence_map = self._save_evidence(conn, evidence_list)

            # Save package managers and external packages
            pm_map = self._save_package_managers(conn, pm_list)
            ep_map = self._save_external_packages(conn, ep_list, pm_map)

            # Save entities (use properties that return lists)
            component_map = self._save_components(conn, rig._components)
            aggregator_map = self._save_aggregators(conn, rig._aggregators)
            runner_map = self._save_runners(conn, rig._runners)
            test_map = self._save_tests(conn, rig._tests, component_map, runner_map)

            # Save relationships
            self._save_node_evidence(conn, rig, evidence_map, component_map, aggregator_map, runner_map, test_map)
            self._save_dependencies(conn, rig, component_map, aggregator_map, runner_map, test_map)
            self._save_runner_args_nodes(conn, rig, runner_map, component_map, aggregator_map, test_map)
            self._save_test_relationships(conn, rig._tests, test_map, component_map)
            self._save_source_files(conn, rig, component_map, test_map)
            self._save_external_package_relationships(conn, rig, component_map, ep_map)
            self._save_component_locations(conn, rig, component_map)

    def _clear_database(self, conn: sqlite3.Connection) -> None:
        """Clear all data from database tables."""
        # Delete from rig_metadata (cascades to other tables via FK constraints)
        conn.execute("DELETE FROM rig_metadata")

        # Explicitly delete from tables without FK to rig_metadata
        conn.execute("DELETE FROM repository_info")
        conn.execute("DELETE FROM build_system_info")
        conn.execute("DELETE FROM evidence")
        conn.execute("DELETE FROM package_managers")
        conn.execute("DELETE FROM external_packages")
        conn.execute("DELETE FROM components")
        conn.execute("DELETE FROM aggregators")
        conn.execute("DELETE FROM runners")
        conn.execute("DELETE FROM tests")
        conn.execute("DELETE FROM node_evidence")
        conn.execute("DELETE FROM component_dependencies")
        conn.execute("DELETE FROM aggregator_dependencies")
        conn.execute("DELETE FROM runner_dependencies")
        conn.execute("DELETE FROM runner_args_nodes")
        conn.execute("DELETE FROM test_dependencies")
        conn.execute("DELETE FROM test_components")
        conn.execute("DELETE FROM test_components_being_tested")
        conn.execute("DELETE FROM component_source_files")
        conn.execute("DELETE FROM test_source_files")
        conn.execute("DELETE FROM component_external_packages")
        conn.execute("DELETE FROM component_locations")

    def _save_rig_metadata(self, conn: sqlite3.Connection, description: str) -> None:
        """Save RIG metadata with id=1."""
        conn.execute("""
            INSERT INTO rig_metadata (id, description)
            VALUES (1, ?)
        """, (description,))

    def _save_repository_info(self, conn: sqlite3.Connection, repo: RepositoryInfo) -> None:
        """Save repository information."""
        conn.execute("""
            INSERT INTO repository_info (name, root_path, build_directory, output_directory,
                                       install_directory, configure_command, build_command, install_command, test_command)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            repo.name,
            str(repo.root_path),
            str(repo.build_directory) if repo.build_directory else None,
            str(repo.output_directory) if repo.output_directory else None,
            str(repo.install_directory) if repo.install_directory else None,
            repo.configure_command if repo.configure_command else None,
            repo.build_command if repo.build_command else None,
            repo.install_command if repo.install_command else None,
            repo.test_command if repo.test_command else None
        ))

    def _save_build_system_info(self, conn: sqlite3.Connection, build_system: BuildSystemInfo) -> None:
        """Save build system information."""
        conn.execute("""
            INSERT INTO build_system_info (name, version, build_type)
            VALUES (?, ?, ?)
        """, (build_system.name, build_system.version, build_system.build_type))

    def _save_evidence(self, conn: sqlite3.Connection, evidence_list: List[Evidence]) -> Dict[str, int]:
        """Save evidence and return mapping from string ID to database ID."""
        evidence_map = {}
        for evidence in evidence_list:
            cursor = conn.execute("""
                INSERT INTO evidence (evidence_string_id, line_json, call_stack_json)
                VALUES (?, ?, ?)
            """, (
                evidence.id,  # String ID like "evidence-1"
                json.dumps(evidence.line) if evidence.line else None,
                json.dumps(evidence.call_stack) if evidence.call_stack else None
            ))
            evidence_map[evidence.id] = cursor.lastrowid
        return evidence_map

    def _save_package_managers(self, conn: sqlite3.Connection, pm_list: List[PackageManager]) -> Dict[str, int]:
        """Save package managers and return mapping from string ID to database ID."""
        pm_map = {}
        for pm in pm_list:
            cursor = conn.execute("""
                INSERT INTO package_managers (pm_string_id, name, package_name)
                VALUES (?, ?, ?)
            """, (pm.id, pm.name, pm.package_name))
            pm_map[pm.id] = cursor.lastrowid
        return pm_map

    def _save_external_packages(self, conn: sqlite3.Connection, ep_list: List[ExternalPackage], pm_map: Dict[str, int]) -> Dict[str, int]:
        """Save external packages and return mapping from string ID to database ID."""
        ep_map = {}
        for ep in ep_list:
            pm_db_id = pm_map[ep.package_manager.id]
            cursor = conn.execute("""
                INSERT INTO external_packages (ep_string_id, name, package_manager_id)
                VALUES (?, ?, ?)
            """, (ep.id, ep.name, pm_db_id))
            ep_map[ep.id] = cursor.lastrowid
        return ep_map

    def _save_components(self, conn: sqlite3.Connection, components: List[Component]) -> Dict[str, int]:
        """Save components and return mapping from string ID to database ID."""
        component_map = {}
        for component in components:
            cursor = conn.execute("""
                INSERT INTO components (comp_string_id, name, type, relative_path, programming_language)
                VALUES (?, ?, ?, ?, ?)
            """, (
                component.id,
                component.name,
                component.type.value,
                str(component.relative_path),
                component.programming_language
            ))
            component_map[component.id] = cursor.lastrowid
        return component_map

    def _save_aggregators(self, conn: sqlite3.Connection, aggregators: List[Aggregator]) -> Dict[str, int]:
        """Save aggregators and return mapping from string ID to database ID."""
        aggregator_map = {}
        for aggregator in aggregators:
            cursor = conn.execute("""
                INSERT INTO aggregators (agg_string_id, name)
                VALUES (?, ?)
            """, (aggregator.id, aggregator.name))
            aggregator_map[aggregator.id] = cursor.lastrowid
        return aggregator_map

    def _save_runners(self, conn: sqlite3.Connection, runners: List[Runner]) -> Dict[str, int]:
        """Save runners and return mapping from string ID to database ID."""
        runner_map = {}
        for runner in runners:
            # Serialize arguments as JSON
            arguments_json = json.dumps(runner.arguments) if runner.arguments else None

            cursor = conn.execute("""
                INSERT INTO runners (runner_string_id, name, arguments_json)
                VALUES (?, ?, ?)
            """, (runner.id, runner.name, arguments_json))
            runner_map[runner.id] = cursor.lastrowid
        return runner_map

    def _save_tests(self, conn: sqlite3.Connection, tests: List[TestDefinition], component_map: Dict[str, int], runner_map: Dict[str, int]) -> Dict[str, int]:
        """Save tests and return mapping from string ID to database ID."""
        test_map = {}
        for test in tests:
            # Handle test_executable_component (can be Component or Runner)
            test_exec_db_id = None
            test_exec_type = None

            if test.test_executable_component:
                if isinstance(test.test_executable_component, Component):
                    test_exec_db_id = component_map[test.test_executable_component.id]
                    test_exec_type = 'component'
                elif isinstance(test.test_executable_component, Runner):
                    test_exec_db_id = runner_map[test.test_executable_component.id]
                    test_exec_type = 'runner'

            cursor = conn.execute("""
                INSERT INTO tests (test_string_id, name, test_executable_component_id, test_executable_type, test_framework)
                VALUES (?, ?, ?, ?, ?)
            """, (test.id, test.name, test_exec_db_id, test_exec_type, test.test_framework))
            test_map[test.id] = cursor.lastrowid
        return test_map

    def _save_node_evidence(self, conn: sqlite3.Connection, rig: RIG, evidence_map: Dict[str, int],
                           component_map: Dict[str, int], aggregator_map: Dict[str, int],
                           runner_map: Dict[str, int], test_map: Dict[str, int]) -> None:
        """Save node-evidence relationships (many-to-many)."""
        # Components
        for component in rig._components:
            component_db_id = component_map[component.id]
            for evidence in component.evidence:
                evidence_db_id = evidence_map[evidence.id]
                conn.execute("""
                    INSERT INTO node_evidence (node_type, node_id, evidence_id)
                    VALUES (?, ?, ?)
                """, ('component', component_db_id, evidence_db_id))

        # Aggregators
        for aggregator in rig._aggregators:
            aggregator_db_id = aggregator_map[aggregator.id]
            for evidence in aggregator.evidence:
                evidence_db_id = evidence_map[evidence.id]
                conn.execute("""
                    INSERT INTO node_evidence (node_type, node_id, evidence_id)
                    VALUES (?, ?, ?)
                """, ('aggregator', aggregator_db_id, evidence_db_id))

        # Runners
        for runner in rig._runners:
            runner_db_id = runner_map[runner.id]
            for evidence in runner.evidence:
                evidence_db_id = evidence_map[evidence.id]
                conn.execute("""
                    INSERT INTO node_evidence (node_type, node_id, evidence_id)
                    VALUES (?, ?, ?)
                """, ('runner', runner_db_id, evidence_db_id))

        # Tests
        for test in rig._tests:
            test_db_id = test_map[test.id]
            for evidence in test.evidence:
                evidence_db_id = evidence_map[evidence.id]
                conn.execute("""
                    INSERT INTO node_evidence (node_type, node_id, evidence_id)
                    VALUES (?, ?, ?)
                """, ('test', test_db_id, evidence_db_id))

    def _save_dependencies(self, conn: sqlite3.Connection, rig: RIG,
                          component_map: Dict[str, int], aggregator_map: Dict[str, int], runner_map: Dict[str, int], test_map: Dict[str, int]) -> None:
        """Save all dependency relationships."""
        # Component dependencies
        for component in rig._components:
            component_db_id = component_map[component.id]
            for dep in component.depends_on:
                self._save_single_dependency(conn, 'component', component_db_id, dep,
                                            component_map, aggregator_map, runner_map)

        # Aggregator dependencies
        for aggregator in rig._aggregators:
            aggregator_db_id = aggregator_map[aggregator.id]
            for dep in aggregator.depends_on:
                self._save_single_dependency(conn, 'aggregator', aggregator_db_id, dep,
                                            component_map, aggregator_map, runner_map)

        # Runner dependencies
        for runner in rig._runners:
            runner_db_id = runner_map[runner.id]
            for dep in runner.depends_on:
                self._save_single_dependency(conn, 'runner', runner_db_id, dep,
                                            component_map, aggregator_map, runner_map)

        # Test dependencies
        for test in rig._tests:
            test_db_id = test_map[test.id]
            for dep in test.depends_on:
                self._save_single_dependency(conn, 'test', test_db_id, dep,
                                            component_map, aggregator_map, runner_map)

    def _save_single_dependency(self, conn: sqlite3.Connection, node_type: str, node_db_id: int,
                               dep: Union[Component, Aggregator, Runner],
                               component_map: Dict[str, int], aggregator_map: Dict[str, int], runner_map: Dict[str, int]) -> None:
        """Save a single dependency relationship with type discriminator."""
        dep_db_id = None
        dep_type = None

        if isinstance(dep, Component):
            dep_db_id = component_map.get(dep.id)
            dep_type = 'component'
        elif isinstance(dep, Aggregator):
            dep_db_id = aggregator_map.get(dep.id)
            dep_type = 'aggregator'
        elif isinstance(dep, Runner):
            dep_db_id = runner_map.get(dep.id)
            dep_type = 'runner'

        if dep_db_id and dep_type:
            table_name = f"{node_type}_dependencies"
            conn.execute(f"""
                INSERT INTO {table_name} ({node_type}_id, depends_on_type, depends_on_id)
                VALUES (?, ?, ?)
            """, (node_db_id, dep_type, dep_db_id))

    def _save_runner_args_nodes(self, conn: sqlite3.Connection, rig: RIG, runner_map: Dict[str, int],
                                component_map: Dict[str, int], aggregator_map: Dict[str, int], test_map: Dict[str, int]) -> None:
        """Save runner args_nodes relationships."""
        for runner in rig._runners:
            runner_db_id = runner_map[runner.id]
            for args_node in runner.args_nodes:
                args_node_db_id = None
                args_node_type = None

                if isinstance(args_node, Component):
                    args_node_db_id = component_map.get(args_node.id)
                    args_node_type = 'component'
                elif isinstance(args_node, Aggregator):
                    args_node_db_id = aggregator_map.get(args_node.id)
                    args_node_type = 'aggregator'
                elif isinstance(args_node, Runner):
                    args_node_db_id = runner_map.get(args_node.id)
                    args_node_type = 'runner'
                elif isinstance(args_node, TestDefinition):
                    args_node_db_id = test_map.get(args_node.id)
                    args_node_type = 'test'

                if args_node_db_id and args_node_type:
                    conn.execute("""
                        INSERT INTO runner_args_nodes (runner_id, args_node_type, args_node_id)
                        VALUES (?, ?, ?)
                    """, (runner_db_id, args_node_type, args_node_db_id))

    def _save_test_relationships(self, conn: sqlite3.Connection, tests: List[TestDefinition],
                                 test_map: Dict[str, int], component_map: Dict[str, int]) -> None:
        """Save test-to-component relationships."""
        for test in tests:
            test_db_id = test_map[test.id]

            # Save test_components
            for component in test.test_components:
                if component.id in component_map:
                    conn.execute("""
                        INSERT INTO test_components (test_id, component_id)
                        VALUES (?, ?)
                    """, (test_db_id, component_map[component.id]))

            # Save components_being_tested
            for component in test.components_being_tested:
                if component.id in component_map:
                    conn.execute("""
                        INSERT INTO test_components_being_tested (test_id, component_id)
                        VALUES (?, ?)
                    """, (test_db_id, component_map[component.id]))

    def _save_source_files(self, conn: sqlite3.Connection, rig: RIG,
                           component_map: Dict[str, int], test_map: Dict[str, int]) -> None:
        """Save source file relationships."""
        # Component source files
        for component in rig._components:
            component_db_id = component_map[component.id]
            for source_file in component.source_files:
                conn.execute("""
                    INSERT INTO component_source_files (component_id, source_file_path)
                    VALUES (?, ?)
                """, (component_db_id, str(source_file)))

        # Test source files
        for test in rig._tests:
            test_db_id = test_map[test.id]
            for source_file in test.source_files:
                conn.execute("""
                    INSERT INTO test_source_files (test_id, source_file_path)
                    VALUES (?, ?)
                """, (test_db_id, str(source_file)))

    def _save_external_package_relationships(self, conn: sqlite3.Connection, rig: RIG,
                                            component_map: Dict[str, int], ep_map: Dict[str, int]) -> None:
        """Save component-to-external-package relationships."""
        for component in rig._components:
            component_db_id = component_map[component.id]
            for ep in component.external_packages:
                if ep.id in ep_map:
                    conn.execute("""
                        INSERT INTO component_external_packages (component_id, external_package_id)
                        VALUES (?, ?)
                    """, (component_db_id, ep_map[ep.id]))

    def _save_component_locations(self, conn: sqlite3.Connection, rig: RIG, component_map: Dict[str, int]) -> None:
        """Save component locations (simple paths)."""
        for component in rig._components:
            component_db_id = component_map[component.id]
            for location_path in component.locations:
                conn.execute("""
                    INSERT INTO component_locations (component_id, location_path)
                    VALUES (?, ?)
                """, (component_db_id, str(location_path)))

    # ==============================================
    # LOAD METHODS
    # ==============================================

    def load_rig(self) -> RIG:
        """
        Load RIG object from SQLite database.

        Returns:
            Loaded RIG object

        Raises:
            ValueError: If database contains 0 or >1 RIGs
        """
        with self._get_connection() as conn:
            # Validate exactly 1 RIG exists
            cursor = conn.execute("SELECT COUNT(*) as count FROM rig_metadata")
            count = cursor.fetchone()['count']

            if count == 0:
                raise ValueError("Database is empty - no RIG found")
            elif count > 1:
                raise ValueError(f"Database is corrupted - contains {count} RIGs, expected 1")

            # Load RIG metadata
            rig_metadata = self._load_rig_metadata(conn)
            if not rig_metadata:
                raise ValueError("RIG metadata not found")

            # Create RIG object
            rig = RIG()

            # Load repository info
            rig._repository_info = self._load_repository_info(conn)

            # Load build system info
            rig._build_system_info = self._load_build_system_info(conn)

            # Load evidence and create db_id → Evidence map
            evidence_list, evidence_db_map = self._load_evidence(conn)
            for evidence in evidence_list:
                rig._evidence_by_id[evidence.id] = evidence

            # Load package managers and external packages
            pm_list, pm_db_map = self._load_package_managers(conn)
            for pm in pm_list:
                rig._package_managers_by_id[pm.id] = pm

            ep_list, ep_db_map = self._load_external_packages(conn, pm_db_map)
            for ep in ep_list:
                rig._external_packages_by_id[ep.id] = ep

            # Load entities and create db_id → Object maps
            component_list, component_db_map = self._load_components(conn)
            for component in component_list:
                rig._components_by_id[component.id] = component

            aggregator_list, aggregator_db_map = self._load_aggregators(conn)
            for aggregator in aggregator_list:
                rig._aggregators_by_id[aggregator.id] = aggregator

            runner_list, runner_db_map = self._load_runners(conn)
            for runner in runner_list:
                rig._runners_by_id[runner.id] = runner

            test_list, test_db_map = self._load_tests(conn, component_db_map, runner_db_map)
            for test in test_list:
                rig._tests_by_id[test.id] = test

            # Load relationships using db_id maps
            self._load_node_evidence(conn, component_db_map, aggregator_db_map, runner_db_map, test_db_map, evidence_db_map)
            self._load_dependencies(conn, component_db_map, aggregator_db_map, runner_db_map, test_db_map)
            self._load_test_relationships(conn, test_db_map, component_db_map)
            self._load_source_files(conn, component_db_map, test_db_map)
            self._load_external_package_relationships(conn, component_db_map, ep_db_map)
            self._load_component_locations(conn, component_db_map)

            return rig

    def _load_rig_metadata(self, conn: sqlite3.Connection) -> Optional[Dict[str, Any]]:
        """Load RIG metadata."""
        cursor = conn.execute("SELECT * FROM rig_metadata WHERE id = 1")
        row = cursor.fetchone()
        return dict(row) if row else None

    def _load_repository_info(self, conn: sqlite3.Connection) -> Optional[RepositoryInfo]:
        """Load repository information."""
        cursor = conn.execute("SELECT * FROM repository_info")
        row = cursor.fetchone()
        if not row:
            return None

        return RepositoryInfo(
            name=row['name'],
            root_path=Path(row['root_path']),
            build_directory=Path(row['build_directory']) if row['build_directory'] else None,
            output_directory=Path(row['output_directory']) if row['output_directory'] else None,
            install_directory=Path(row['install_directory']) if row['install_directory'] else None,
            configure_command=row['configure_command'],
            build_command=row['build_command'],
            install_command=row['install_command'],
            test_command=row['test_command']
        )

    def _load_build_system_info(self, conn: sqlite3.Connection) -> Optional[BuildSystemInfo]:
        """Load build system information."""
        cursor = conn.execute("SELECT * FROM build_system_info")
        row = cursor.fetchone()
        if not row:
            return None

        return BuildSystemInfo(
            name=row['name'],
            version=row['version'],
            build_type=row['build_type']
        )

    def _load_evidence(self, conn: sqlite3.Connection) -> Tuple[List[Evidence], Dict[int, Evidence]]:
        """Load evidence and return both list and db_id → Evidence map."""
        cursor = conn.execute("SELECT * FROM evidence")
        evidence_list = []
        evidence_db_map = {}

        for row in cursor.fetchall():
            evidence = Evidence(
                id=row['evidence_string_id'],  # Use string ID column
                line=json.loads(row['line_json']) if row['line_json'] else None,
                call_stack=json.loads(row['call_stack_json']) if row['call_stack_json'] else None
            )
            evidence_list.append(evidence)
            evidence_db_map[row['id']] = evidence  # Map db ID → object

        return evidence_list, evidence_db_map

    def _load_package_managers(self, conn: sqlite3.Connection) -> Tuple[List[PackageManager], Dict[int, PackageManager]]:
        """Load package managers and return both list and db_id → PackageManager map."""
        cursor = conn.execute("SELECT * FROM package_managers")
        pm_list = []
        pm_db_map = {}

        for row in cursor.fetchall():
            pm = PackageManager(
                id=row['pm_string_id'],
                name=row['name'],
                package_name=row['package_name']
            )
            pm_list.append(pm)
            pm_db_map[row['id']] = pm

        return pm_list, pm_db_map

    def _load_external_packages(self, conn: sqlite3.Connection, pm_db_map: Dict[int, PackageManager]) -> Tuple[List[ExternalPackage], Dict[int, ExternalPackage]]:
        """Load external packages and return both list and db_id → ExternalPackage map."""
        cursor = conn.execute("SELECT * FROM external_packages")
        ep_list = []
        ep_db_map = {}

        for row in cursor.fetchall():
            pm = pm_db_map[row['package_manager_id']]
            ep = ExternalPackage(
                id=row['ep_string_id'],
                name=row['name'],
                package_manager=pm
            )
            ep_list.append(ep)
            ep_db_map[row['id']] = ep

        return ep_list, ep_db_map

    def _load_components(self, conn: sqlite3.Connection) -> Tuple[List[Component], Dict[int, Component]]:
        """Load components and return both list and db_id → Component map."""
        cursor = conn.execute("SELECT * FROM components")
        component_list = []
        component_db_map = {}

        for row in cursor.fetchall():
            component = Component(
                id=row['comp_string_id'],  # Use string ID column!
                name=row['name'],
                type=ComponentType(row['type']),
                relative_path=Path(row['relative_path']),
                programming_language=row['programming_language'],
                source_files=[],  # Loaded separately
                external_packages=[],  # Loaded separately
                locations=[],  # Loaded separately
                depends_on=[],  # Loaded separately
                evidence=[]  # Loaded separately
            )
            component_list.append(component)
            component_db_map[row['id']] = component  # Map db ID → object

        return component_list, component_db_map

    def _load_aggregators(self, conn: sqlite3.Connection) -> Tuple[List[Aggregator], Dict[int, Aggregator]]:
        """Load aggregators and return both list and db_id → Aggregator map."""
        cursor = conn.execute("SELECT * FROM aggregators")
        aggregator_list = []
        aggregator_db_map = {}

        for row in cursor.fetchall():
            aggregator = Aggregator(
                id=row['agg_string_id'],
                name=row['name'],
                depends_on=[],
                evidence=[]
            )
            aggregator_list.append(aggregator)
            aggregator_db_map[row['id']] = aggregator

        return aggregator_list, aggregator_db_map

    def _load_runners(self, conn: sqlite3.Connection) -> Tuple[List[Runner], Dict[int, Runner]]:
        """Load runners and return both list and db_id → Runner map."""
        cursor = conn.execute("SELECT * FROM runners")
        runner_list = []
        runner_db_map = {}

        for row in cursor.fetchall():
            # Deserialize arguments from JSON
            arguments = json.loads(row['arguments_json']) if row['arguments_json'] else []

            runner = Runner(
                id=row['runner_string_id'],
                name=row['name'],
                depends_on=[],
                evidence=[],
                arguments=arguments,
                args_nodes=[],
                args_nodes_ids=set()
            )
            runner_list.append(runner)
            runner_db_map[row['id']] = runner

        return runner_list, runner_db_map

    def _load_tests(self, conn: sqlite3.Connection, component_db_map: Dict[int, Component], runner_db_map: Dict[int, Runner]) -> Tuple[List[TestDefinition], Dict[int, TestDefinition]]:
        """Load tests and return both list and db_id → TestDefinition map."""
        cursor = conn.execute("SELECT * FROM tests")
        test_list = []
        test_db_map = {}

        for row in cursor.fetchall():
            # Handle test_executable_component (Component | Runner)
            test_exec = None
            if row['test_executable_component_id']:
                if row['test_executable_type'] == 'component':
                    test_exec = component_db_map.get(row['test_executable_component_id'])
                elif row['test_executable_type'] == 'runner':
                    test_exec = runner_db_map.get(row['test_executable_component_id'])

            test = TestDefinition(
                id=row['test_string_id'],
                name=row['name'],
                test_executable_component=test_exec,
                test_executable_component_id=test_exec.id if test_exec else None,
                test_components=[],  # Loaded separately
                components_being_tested=[],  # Loaded separately
                source_files=[],  # Loaded separately
                test_framework=row['test_framework'],
                depends_on=[],  # Loaded separately
                evidence=[]  # Loaded separately
            )
            test_list.append(test)
            test_db_map[row['id']] = test

        return test_list, test_db_map

    def _load_node_evidence(self, conn: sqlite3.Connection,
                           component_db_map: Dict[int, Component], aggregator_db_map: Dict[int, Aggregator],
                           runner_db_map: Dict[int, Runner], test_db_map: Dict[int, TestDefinition],
                           evidence_db_map: Dict[int, Evidence]) -> None:
        """Load node-evidence relationships."""
        cursor = conn.execute("SELECT * FROM node_evidence")

        for row in cursor.fetchall():
            evidence = evidence_db_map[row['evidence_id']]

            if row['node_type'] == 'component':
                node = component_db_map.get(row['node_id'])
                if node:
                    node.evidence.append(evidence)
                    node.evidence_ids.add(evidence.id)
            elif row['node_type'] == 'aggregator':
                node = aggregator_db_map.get(row['node_id'])
                if node:
                    node.evidence.append(evidence)
                    node.evidence_ids.add(evidence.id)
            elif row['node_type'] == 'runner':
                node = runner_db_map.get(row['node_id'])
                if node:
                    node.evidence.append(evidence)
                    node.evidence_ids.add(evidence.id)
            elif row['node_type'] == 'test':
                node = test_db_map.get(row['node_id'])
                if node:
                    node.evidence.append(evidence)
                    node.evidence_ids.add(evidence.id)

    def _load_dependencies(self, conn: sqlite3.Connection,
                          component_db_map: Dict[int, Component], aggregator_db_map: Dict[int, Aggregator],
                          runner_db_map: Dict[int, Runner], test_db_map: Dict[int, TestDefinition]) -> None:
        """Load all dependency relationships."""
        # Load component dependencies
        cursor = conn.execute("SELECT * FROM component_dependencies")
        for row in cursor.fetchall():
            component = component_db_map.get(row['component_id'])
            dep = self._get_dependency_object(row['depends_on_type'], row['depends_on_id'],
                                             component_db_map, aggregator_db_map, runner_db_map)
            if component and dep:
                component.depends_on.append(dep)
                component.depends_on_ids.add(dep.id)

        # Load aggregator dependencies
        cursor = conn.execute("SELECT * FROM aggregator_dependencies")
        for row in cursor.fetchall():
            aggregator = aggregator_db_map.get(row['aggregator_id'])
            dep = self._get_dependency_object(row['depends_on_type'], row['depends_on_id'],
                                             component_db_map, aggregator_db_map, runner_db_map)
            if aggregator and dep:
                aggregator.depends_on.append(dep)
                aggregator.depends_on_ids.add(dep.id)

        # Load runner dependencies
        cursor = conn.execute("SELECT * FROM runner_dependencies")
        for row in cursor.fetchall():
            runner = runner_db_map.get(row['runner_id'])
            dep = self._get_dependency_object(row['depends_on_type'], row['depends_on_id'],
                                             component_db_map, aggregator_db_map, runner_db_map)
            if runner and dep:
                runner.depends_on.append(dep)
                runner.depends_on_ids.add(dep.id)

        # Load runner args_nodes
        cursor = conn.execute("SELECT * FROM runner_args_nodes")
        for row in cursor.fetchall():
            runner = runner_db_map.get(row['runner_id'])
            args_node = self._get_args_node_object(row['args_node_type'], row['args_node_id'],
                                                   component_db_map, aggregator_db_map, runner_db_map, test_db_map)
            if runner and args_node:
                runner.args_nodes.append(args_node)
                runner.args_nodes_ids.add(args_node.id)

        # Load test dependencies
        cursor = conn.execute("SELECT * FROM test_dependencies")
        for row in cursor.fetchall():
            test = test_db_map.get(row['test_id'])
            dep = self._get_dependency_object(row['depends_on_type'], row['depends_on_id'],
                                             component_db_map, aggregator_db_map, runner_db_map)
            if test and dep:
                test.depends_on.append(dep)
                test.depends_on_ids.add(dep.id)

    def _get_dependency_object(self, dep_type: str, dep_db_id: int,
                               component_db_map: Dict[int, Component], aggregator_db_map: Dict[int, Aggregator],
                               runner_db_map: Dict[int, Runner]) -> Optional[Union[Component, Aggregator, Runner]]:
        """Get dependency object using type discriminator."""
        if dep_type == 'component':
            return component_db_map.get(dep_db_id)
        elif dep_type == 'aggregator':
            return aggregator_db_map.get(dep_db_id)
        elif dep_type == 'runner':
            return runner_db_map.get(dep_db_id)
        return None

    def _get_args_node_object(self, node_type: str, node_db_id: int,
                              component_db_map: Dict[int, Component], aggregator_db_map: Dict[int, Aggregator],
                              runner_db_map: Dict[int, Runner], test_db_map: Dict[int, TestDefinition]) -> Optional[Union[Component, Aggregator, Runner, TestDefinition]]:
        """Get args_node object using type discriminator (supports all node types)."""
        if node_type == 'component':
            return component_db_map.get(node_db_id)
        elif node_type == 'aggregator':
            return aggregator_db_map.get(node_db_id)
        elif node_type == 'runner':
            return runner_db_map.get(node_db_id)
        elif node_type == 'test':
            return test_db_map.get(node_db_id)
        return None

    def _load_test_relationships(self, conn: sqlite3.Connection,
                                 test_db_map: Dict[int, TestDefinition], component_db_map: Dict[int, Component]) -> None:
        """Load test-to-component relationships."""
        # Load test_components
        cursor = conn.execute("SELECT * FROM test_components")
        for row in cursor.fetchall():
            test = test_db_map.get(row['test_id'])
            component = component_db_map.get(row['component_id'])
            if test and component:
                test.test_components.append(component)
                test.test_components_ids.add(component.id)

        # Load components_being_tested
        cursor = conn.execute("SELECT * FROM test_components_being_tested")
        for row in cursor.fetchall():
            test = test_db_map.get(row['test_id'])
            component = component_db_map.get(row['component_id'])
            if test and component:
                test.components_being_tested.append(component)
                test.components_being_tested_ids.add(component.id)

    def _load_source_files(self, conn: sqlite3.Connection,
                          component_db_map: Dict[int, Component], test_db_map: Dict[int, TestDefinition]) -> None:
        """Load source file relationships."""
        # Load component source files
        cursor = conn.execute("SELECT * FROM component_source_files")
        for row in cursor.fetchall():
            component = component_db_map.get(row['component_id'])
            if component:
                component.source_files.append(Path(row['source_file_path']))

        # Load test source files
        cursor = conn.execute("SELECT * FROM test_source_files")
        for row in cursor.fetchall():
            test = test_db_map.get(row['test_id'])
            if test:
                test.source_files.append(Path(row['source_file_path']))

    def _load_external_package_relationships(self, conn: sqlite3.Connection,
                                            component_db_map: Dict[int, Component], ep_db_map: Dict[int, ExternalPackage]) -> None:
        """Load component-to-external-package relationships."""
        cursor = conn.execute("SELECT * FROM component_external_packages")
        for row in cursor.fetchall():
            component = component_db_map.get(row['component_id'])
            ep = ep_db_map.get(row['external_package_id'])
            if component and ep:
                component.external_packages.append(ep)
                component.external_packages_ids.add(ep.id)

    def _load_component_locations(self, conn: sqlite3.Connection, component_db_map: Dict[int, Component]) -> None:
        """Load component locations."""
        cursor = conn.execute("SELECT * FROM component_locations")
        for row in cursor.fetchall():
            component = component_db_map.get(row['component_id'])
            if component:
                component.locations.append(Path(row['location_path']))


# Convenience functions
def save_rig(rig: RIG, db_path: Union[str, Path], description: str = "RIG Export") -> None:
    """Save RIG to SQLite database (replaces any existing RIG)."""
    store = RIGStore(db_path)
    store.save_rig(rig, description)


def load_rig(db_path: Union[str, Path]) -> RIG:
    """Load RIG from SQLite database."""
    store = RIGStore(db_path)
    return store.load_rig()
