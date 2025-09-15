"""
RIG SQLite Storage Module

This module provides functionality to save and load RIG objects to/from SQLite databases.
It handles the complete serialization and deserialization of RIG data structures.
"""

import json
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from contextlib import contextmanager

from rig import RIG
from schemas import (
    Component, Aggregator, Runner, Utility, Test, Evidence, 
    ComponentLocation, ExternalPackage, PackageManager, RepositoryInfo, 
    BuildSystemInfo, ComponentType, Runtime
)


class RIGStore:
    """SQLite storage for RIG objects."""
    
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
                with open('rig_store_schema.sql', 'r') as f:
                    schema_sql = f.read()
                conn.executescript(schema_sql)
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def save_rig(self, rig: RIG, description: str = "RIG Export") -> int:
        """
        Save RIG object to SQLite database.
        
        Args:
            rig: RIG object to save
            description: Description for this RIG export
            
        Returns:
            RIG ID in database
        """
        with self._get_connection() as conn:
            # Start transaction
            conn.execute("BEGIN TRANSACTION")
            
            try:
                # Insert RIG metadata
                rig_id = self._save_rig_metadata(conn, description)
                
                # Save repository info
                if rig.repository:
                    self._save_repository_info(conn, rig_id, rig.repository)
                
                # Save build system info
                if rig.build_system:
                    self._save_build_system_info(conn, rig_id, rig.build_system)
                
                # Save evidence first (referenced by other entities)
                evidence_map = self._save_evidence(conn, rig_id, rig.evidence)
                
                # Save package managers and external packages
                package_manager_map = self._save_package_managers(conn, rig_id, rig.package_managers)
                external_package_map = self._save_external_packages(conn, rig_id, rig.external_packages, package_manager_map)
                
                # Save component locations
                location_map = self._save_component_locations(conn, rig_id, rig.component_locations, evidence_map)
                
                # Save entities
                component_map = self._save_components(conn, rig_id, rig.components, evidence_map, external_package_map, location_map)
                aggregator_map = self._save_aggregators(conn, rig_id, rig.aggregators, evidence_map)
                runner_map = self._save_runners(conn, rig_id, rig.runners, evidence_map)
                utility_map = self._save_utilities(conn, rig_id, rig.utilities, evidence_map)
                test_map = self._save_tests(conn, rig_id, rig.tests, evidence_map, component_map, runner_map)
                
                # Save relationships
                self._save_dependencies(conn, rig_id, rig, component_map, aggregator_map, runner_map, utility_map)
                self._save_test_relationships(conn, rig_id, rig, test_map, component_map)
                self._save_source_files(conn, rig_id, rig, component_map, test_map)
                self._save_external_package_relationships(conn, rig_id, rig, component_map, external_package_map)
                self._save_location_relationships(conn, rig_id, rig, component_map, location_map)
                
                # Commit transaction
                conn.commit()
                return rig_id
                
            except Exception:
                conn.rollback()
                raise
    
    def load_rig(self, rig_id: int) -> RIG:
        """
        Load RIG object from SQLite database.
        
        Args:
            rig_id: RIG ID to load
            
        Returns:
            Loaded RIG object
        """
        with self._get_connection() as conn:
            # Load RIG metadata
            rig_metadata = self._load_rig_metadata(conn, rig_id)
            if not rig_metadata:
                raise ValueError(f"RIG with ID {rig_id} not found")
            
            # Create RIG object
            rig = RIG()
            
            # Load repository info
            rig.repository = self._load_repository_info(conn, rig_id)
            
            # Load build system info
            rig.build_system = self._load_build_system_info(conn, rig_id)
            
            # Load evidence
            rig.evidence = self._load_evidence(conn, rig_id)
            evidence_map = {e.id: e for e in rig.evidence}
            
            # Load package managers and external packages
            rig.package_managers = self._load_package_managers(conn, rig_id)
            package_manager_map = {pm.id: pm for pm in rig.package_managers}
            
            rig.external_packages = self._load_external_packages(conn, rig_id, package_manager_map)
            external_package_map = {ep.id: ep for ep in rig.external_packages}
            
            # Load component locations
            rig.component_locations = self._load_component_locations(conn, rig_id, evidence_map)
            location_map = {cl.id: cl for cl in rig.component_locations}
            
            # Load entities
            rig.components = self._load_components(conn, rig_id, evidence_map, external_package_map, location_map)
            component_map = {c.id: c for c in rig.components}
            
            rig.aggregators = self._load_aggregators(conn, rig_id, evidence_map)
            aggregator_map = {a.id: a for a in rig.aggregators}
            
            rig.runners = self._load_runners(conn, rig_id, evidence_map)
            runner_map = {r.id: r for r in rig.runners}
            
            rig.utilities = self._load_utilities(conn, rig_id, evidence_map)
            utility_map = {u.id: u for u in rig.utilities}
            
            rig.tests = self._load_tests(conn, rig_id, evidence_map, component_map, runner_map)
            test_map = {t.id: t for t in rig.tests}
            
            # Load relationships
            self._load_dependencies(conn, rig_id, rig, component_map, aggregator_map, runner_map, utility_map)
            self._load_test_relationships(conn, rig_id, rig, test_map, component_map)
            self._load_source_files(conn, rig_id, rig, component_map, test_map)
            self._load_external_package_relationships(conn, rig_id, rig, component_map, external_package_map)
            self._load_location_relationships(conn, rig_id, rig, component_map, location_map)
            
            return rig
    
    def list_rigs(self) -> List[Dict[str, Any]]:
        """List all RIGs in the database."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, created_at, updated_at, version, description
                FROM rig_metadata
                ORDER BY created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_rig(self, rig_id: int) -> bool:
        """Delete RIG from database."""
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM rig_metadata WHERE id = ?", (rig_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # Private helper methods for saving data
    
    def _save_rig_metadata(self, conn: sqlite3.Connection, description: str) -> int:
        """Save RIG metadata and return RIG ID."""
        cursor = conn.execute("""
            INSERT INTO rig_metadata (description)
            VALUES (?)
        """, (description,))
        return cursor.lastrowid
    
    def _save_repository_info(self, conn: sqlite3.Connection, rig_id: int, repo: RepositoryInfo) -> None:
        """Save repository information."""
        conn.execute("""
            INSERT INTO repository_info (rig_id, name, root_path, build_directory, output_directory, 
                                      configure_command, build_command, install_command, test_command)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (rig_id, repo.name, str(repo.root_path), str(repo.build_directory), 
              str(repo.output_directory), repo.configure_command, repo.build_command, 
              repo.install_command, repo.test_command))
    
    def _save_build_system_info(self, conn: sqlite3.Connection, rig_id: int, build_system: BuildSystemInfo) -> None:
        """Save build system information."""
        conn.execute("""
            INSERT INTO build_system_info (rig_id, name, version, build_type)
            VALUES (?, ?, ?, ?)
        """, (rig_id, build_system.name, build_system.version, build_system.build_type))
    
    def _save_evidence(self, conn: sqlite3.Connection, rig_id: int, evidence_list: List[Evidence]) -> Dict[int, int]:
        """Save evidence and return mapping from original ID to database ID."""
        evidence_map = {}
        for evidence in evidence_list:
            cursor = conn.execute("""
                INSERT INTO evidence (rig_id, call_stack_json)
                VALUES (?, ?)
            """, (rig_id, json.dumps(evidence.call_stack)))
            evidence_map[evidence.id] = cursor.lastrowid
        return evidence_map
    
    def _save_package_managers(self, conn: sqlite3.Connection, rig_id: int, package_managers: List[PackageManager]) -> Dict[int, int]:
        """Save package managers and return mapping from original ID to database ID."""
        pm_map = {}
        for pm in package_managers:
            cursor = conn.execute("""
                INSERT INTO package_managers (rig_id, name, package_name)
                VALUES (?, ?, ?)
            """, (rig_id, pm.name, pm.package_name))
            pm_map[pm.id] = cursor.lastrowid
        return pm_map
    
    def _save_external_packages(self, conn: sqlite3.Connection, rig_id: int, external_packages: List[ExternalPackage], pm_map: Dict[int, int]) -> Dict[int, int]:
        """Save external packages and return mapping from original ID to database ID."""
        ep_map = {}
        for ep in external_packages:
            cursor = conn.execute("""
                INSERT INTO external_packages (rig_id, package_manager_id)
                VALUES (?, ?)
            """, (rig_id, pm_map[ep.package_manager.id]))
            ep_map[ep.id] = cursor.lastrowid
        return ep_map
    
    def _save_component_locations(self, conn: sqlite3.Connection, rig_id: int, locations: List[ComponentLocation], evidence_map: Dict[int, int]) -> Dict[int, int]:
        """Save component locations and return mapping from original ID to database ID."""
        location_map = {}
        for location in locations:
            source_location_id = None
            if location.source_location and location.source_location.id in location_map:
                source_location_id = location_map[location.source_location.id]
            
            cursor = conn.execute("""
                INSERT INTO component_locations (rig_id, path, action, source_location_id, evidence_id)
                VALUES (?, ?, ?, ?, ?)
            """, (rig_id, str(location.path), location.action, source_location_id, evidence_map[location.evidence.id]))
            location_map[location.id] = cursor.lastrowid
        return location_map
    
    def _save_components(self, conn: sqlite3.Connection, rig_id: int, components: List[Component], evidence_map: Dict[int, int], ep_map: Dict[int, int], location_map: Dict[int, int]) -> Dict[int, int]:
        """Save components and return mapping from original ID to database ID."""
        component_map = {}
        for component in components:
            cursor = conn.execute("""
                INSERT INTO components (rig_id, name, type, runtime, output, output_path, programming_language, 
                                      evidence_id, test_link_id, test_link_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (rig_id, component.name, component.type.value, component.runtime.value if component.runtime else None,
                  component.output, str(component.output_path), component.programming_language,
                  evidence_map[component.evidence.id], component.test_link_id, component.test_link_name))
            component_map[component.id] = cursor.lastrowid
        return component_map
    
    def _save_aggregators(self, conn: sqlite3.Connection, rig_id: int, aggregators: List[Aggregator], evidence_map: Dict[int, int]) -> Dict[int, int]:
        """Save aggregators and return mapping from original ID to database ID."""
        aggregator_map = {}
        for aggregator in aggregators:
            cursor = conn.execute("""
                INSERT INTO aggregators (rig_id, name, evidence_id)
                VALUES (?, ?, ?)
            """, (rig_id, aggregator.name, evidence_map[aggregator.evidence.id]))
            aggregator_map[aggregator.id] = cursor.lastrowid
        return aggregator_map
    
    def _save_runners(self, conn: sqlite3.Connection, rig_id: int, runners: List[Runner], evidence_map: Dict[int, int]) -> Dict[int, int]:
        """Save runners and return mapping from original ID to database ID."""
        runner_map = {}
        for runner in runners:
            cursor = conn.execute("""
                INSERT INTO runners (rig_id, name, evidence_id)
                VALUES (?, ?, ?)
            """, (rig_id, runner.name, evidence_map[runner.evidence.id]))
            runner_map[runner.id] = cursor.lastrowid
        return runner_map
    
    def _save_utilities(self, conn: sqlite3.Connection, rig_id: int, utilities: List[Utility], evidence_map: Dict[int, int]) -> Dict[int, int]:
        """Save utilities and return mapping from original ID to database ID."""
        utility_map = {}
        for utility in utilities:
            cursor = conn.execute("""
                INSERT INTO utilities (rig_id, name, evidence_id)
                VALUES (?, ?, ?)
            """, (rig_id, utility.name, evidence_map[utility.evidence.id]))
            utility_map[utility.id] = cursor.lastrowid
        return utility_map
    
    def _save_tests(self, conn: sqlite3.Connection, rig_id: int, tests: List[Test], evidence_map: Dict[int, int], component_map: Dict[int, int], runner_map: Dict[int, int]) -> Dict[int, int]:
        """Save tests and return mapping from original ID to database ID."""
        test_map = {}
        for test in tests:
            test_executable_id = None
            if test.test_executable and test.test_executable.id in component_map:
                test_executable_id = component_map[test.test_executable.id]
            
            test_runner_id = None
            if test.test_runner and test.test_runner.id in runner_map:
                test_runner_id = runner_map[test.test_runner.id]
            
            cursor = conn.execute("""
                INSERT INTO tests (rig_id, name, test_executable_id, test_runner_id, test_framework, evidence_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (rig_id, test.name, test_executable_id, test_runner_id, test.test_framework, evidence_map[test.evidence.id]))
            test_map[test.id] = cursor.lastrowid
        return test_map
    
    def _save_dependencies(self, conn: sqlite3.Connection, rig_id: int, rig: RIG, component_map: Dict[int, int], aggregator_map: Dict[int, int], runner_map: Dict[int, int], utility_map: Dict[int, int]) -> None:
        """Save all dependency relationships."""
        # Component dependencies
        for component in rig.components:
            for dep in component.depends_on:
                self._save_dependency(conn, rig_id, 'component', component.id, dep, component_map, aggregator_map, runner_map, utility_map)
        
        # Aggregator dependencies
        for aggregator in rig.aggregators:
            for dep in aggregator.depends_on:
                self._save_dependency(conn, rig_id, 'aggregator', aggregator.id, dep, component_map, aggregator_map, runner_map, utility_map)
        
        # Runner dependencies
        for runner in rig.runners:
            for dep in runner.depends_on:
                self._save_dependency(conn, rig_id, 'runner', runner.id, dep, component_map, aggregator_map, runner_map, utility_map)
        
        # Utility dependencies
        for utility in rig.utilities:
            for dep in utility.depends_on:
                self._save_dependency(conn, rig_id, 'utility', utility.id, dep, component_map, aggregator_map, runner_map, utility_map)
    
    def _save_dependency(self, conn: sqlite3.Connection, rig_id: int, entity_type: str, entity_id: int, dep, component_map: Dict[int, int], aggregator_map: Dict[int, int], runner_map: Dict[int, int], utility_map: Dict[int, int]) -> None:
        """Save a single dependency relationship."""
        table_map = {
            'component': 'component_dependencies',
            'aggregator': 'aggregator_dependencies', 
            'runner': 'runner_dependencies',
            'utility': 'utility_dependencies'
        }
        
        table = table_map[entity_type]
        
        # Determine dependency type and ID
        dep_component_id = None
        dep_aggregator_id = None
        dep_runner_id = None
        dep_utility_id = None
        
        if hasattr(dep, 'id'):
            if isinstance(dep, Component) and dep.id in component_map:
                dep_component_id = component_map[dep.id]
            elif isinstance(dep, Aggregator) and dep.id in aggregator_map:
                dep_aggregator_id = aggregator_map[dep.id]
            elif isinstance(dep, Runner) and dep.id in runner_map:
                dep_runner_id = runner_map[dep.id]
            elif isinstance(dep, Utility) and dep.id in utility_map:
                dep_utility_id = utility_map[dep.id]
        
        if dep_component_id or dep_aggregator_id or dep_runner_id or dep_utility_id:
            conn.execute(f"""
                INSERT INTO {table} (rig_id, {entity_type}_id, depends_on_component_id, depends_on_aggregator_id, 
                                   depends_on_runner_id, depends_on_utility_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (rig_id, entity_id, dep_component_id, dep_aggregator_id, dep_runner_id, dep_utility_id))
    
    def _save_test_relationships(self, conn: sqlite3.Connection, rig_id: int, rig: RIG, test_map: Dict[int, int], component_map: Dict[int, int]) -> None:
        """Save test-to-component relationships."""
        for test in rig.tests:
            for component in test.components_being_tested:
                if component.id in component_map:
                    conn.execute("""
                        INSERT INTO test_components (rig_id, test_id, component_id)
                        VALUES (?, ?, ?)
                    """, (rig_id, test_map[test.id], component_map[component.id]))
    
    def _save_source_files(self, conn: sqlite3.Connection, rig_id: int, rig: RIG, component_map: Dict[int, int], test_map: Dict[int, int]) -> None:
        """Save source file relationships."""
        # Component source files
        for component in rig.components:
            for source_file in component.source_files:
                conn.execute("""
                    INSERT INTO component_source_files (rig_id, component_id, source_file_path)
                    VALUES (?, ?, ?)
                """, (rig_id, component_map[component.id], str(source_file)))
        
        # Test source files
        for test in rig.tests:
            for source_file in test.source_files:
                conn.execute("""
                    INSERT INTO test_source_files (rig_id, test_id, source_file_path)
                    VALUES (?, ?, ?)
                """, (rig_id, test_map[test.id], str(source_file)))
    
    def _save_external_package_relationships(self, conn: sqlite3.Connection, rig_id: int, rig: RIG, component_map: Dict[int, int], ep_map: Dict[int, int]) -> None:
        """Save component-to-external-package relationships."""
        for component in rig.components:
            for ep in component.external_packages:
                if ep.id in ep_map:
                    conn.execute("""
                        INSERT INTO component_external_packages (rig_id, component_id, external_package_id)
                        VALUES (?, ?, ?)
                    """, (rig_id, component_map[component.id], ep_map[ep.id]))
    
    def _save_location_relationships(self, conn: sqlite3.Connection, rig_id: int, rig: RIG, component_map: Dict[int, int], location_map: Dict[int, int]) -> None:
        """Save component-to-location relationships."""
        for component in rig.components:
            for location in component.locations:
                if location.id in location_map:
                    conn.execute("""
                        INSERT INTO component_locations_rel (rig_id, component_id, location_id)
                        VALUES (?, ?, ?)
                    """, (rig_id, component_map[component.id], location_map[location.id]))
    
    # Private helper methods for loading data
    
    def _load_rig_metadata(self, conn: sqlite3.Connection, rig_id: int) -> Optional[Dict[str, Any]]:
        """Load RIG metadata."""
        cursor = conn.execute("SELECT * FROM rig_metadata WHERE id = ?", (rig_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def _load_repository_info(self, conn: sqlite3.Connection, rig_id: int) -> Optional[RepositoryInfo]:
        """Load repository information."""
        cursor = conn.execute("SELECT * FROM repository_info WHERE rig_id = ?", (rig_id,))
        row = cursor.fetchone()
        if not row:
            return None
        
        return RepositoryInfo(
            name=row['name'],
            root_path=Path(row['root_path']),
            build_directory=Path(row['build_directory']),
            output_directory=Path(row['output_directory']),
            configure_command=row['configure_command'],
            build_command=row['build_command'],
            install_command=row['install_command'],
            test_command=row['test_command']
        )
    
    def _load_build_system_info(self, conn: sqlite3.Connection, rig_id: int) -> Optional[BuildSystemInfo]:
        """Load build system information."""
        cursor = conn.execute("SELECT * FROM build_system_info WHERE rig_id = ?", (rig_id,))
        row = cursor.fetchone()
        if not row:
            return None
        
        return BuildSystemInfo(
            name=row['name'],
            version=row['version'],
            build_type=row['build_type']
        )
    
    def _load_evidence(self, conn: sqlite3.Connection, rig_id: int) -> List[Evidence]:
        """Load evidence."""
        cursor = conn.execute("SELECT * FROM evidence WHERE rig_id = ?", (rig_id,))
        evidence_list = []
        for row in cursor.fetchall():
            evidence = Evidence(
                id=row['id'],
                call_stack=json.loads(row['call_stack_json'])
            )
            evidence_list.append(evidence)
        return evidence_list
    
    def _load_package_managers(self, conn: sqlite3.Connection, rig_id: int) -> List[PackageManager]:
        """Load package managers."""
        cursor = conn.execute("SELECT * FROM package_managers WHERE rig_id = ?", (rig_id,))
        pm_list = []
        for row in cursor.fetchall():
            pm = PackageManager(
                id=row['id'],
                name=row['name'],
                package_name=row['package_name']
            )
            pm_list.append(pm)
        return pm_list
    
    def _load_external_packages(self, conn: sqlite3.Connection, rig_id: int, pm_map: Dict[int, PackageManager]) -> List[ExternalPackage]:
        """Load external packages."""
        cursor = conn.execute("SELECT * FROM external_packages WHERE rig_id = ?", (rig_id,))
        ep_list = []
        for row in cursor.fetchall():
            ep = ExternalPackage(
                id=row['id'],
                package_manager=pm_map[row['package_manager_id']]
            )
            ep_list.append(ep)
        return ep_list
    
    def _load_component_locations(self, conn: sqlite3.Connection, rig_id: int, evidence_map: Dict[int, Evidence]) -> List[ComponentLocation]:
        """Load component locations."""
        cursor = conn.execute("SELECT * FROM component_locations WHERE rig_id = ?", (rig_id,))
        location_list = []
        for row in cursor.fetchall():
            source_location = None
            if row['source_location_id']:
                # Find source location in already loaded locations
                for loc in location_list:
                    if loc.id == row['source_location_id']:
                        source_location = loc
                        break
            
            location = ComponentLocation(
                id=row['id'],
                path=Path(row['path']),
                action=row['action'],
                source_location=source_location,
                evidence=evidence_map[row['evidence_id']]
            )
            location_list.append(location)
        return location_list
    
    def _load_components(self, conn: sqlite3.Connection, rig_id: int, evidence_map: Dict[int, Evidence], ep_map: Dict[int, ExternalPackage], location_map: Dict[int, ComponentLocation]) -> List[Component]:
        """Load components."""
        cursor = conn.execute("SELECT * FROM components WHERE rig_id = ?", (rig_id,))
        component_list = []
        for row in cursor.fetchall():
            component = Component(
                id=row['id'],
                name=row['name'],
                type=ComponentType(row['type']),
                runtime=Runtime(row['runtime']) if row['runtime'] else None,
                output=row['output'],
                output_path=Path(row['output_path']),
                programming_language=row['programming_language'],
                source_files=[],  # Will be loaded separately
                external_packages=[],  # Will be loaded separately
                locations=[],  # Will be loaded separately
                depends_on=[],  # Will be loaded separately
                evidence=evidence_map[row['evidence_id']],
                test_link_id=row['test_link_id'],
                test_link_name=row['test_link_name']
            )
            component_list.append(component)
        return component_list
    
    def _load_aggregators(self, conn: sqlite3.Connection, rig_id: int, evidence_map: Dict[int, Evidence]) -> List[Aggregator]:
        """Load aggregators."""
        cursor = conn.execute("SELECT * FROM aggregators WHERE rig_id = ?", (rig_id,))
        aggregator_list = []
        for row in cursor.fetchall():
            aggregator = Aggregator(
                id=row['id'],
                name=row['name'],
                depends_on=[],  # Will be loaded separately
                evidence=evidence_map[row['evidence_id']]
            )
            aggregator_list.append(aggregator)
        return aggregator_list
    
    def _load_runners(self, conn: sqlite3.Connection, rig_id: int, evidence_map: Dict[int, Evidence]) -> List[Runner]:
        """Load runners."""
        cursor = conn.execute("SELECT * FROM runners WHERE rig_id = ?", (rig_id,))
        runner_list = []
        for row in cursor.fetchall():
            runner = Runner(
                id=row['id'],
                name=row['name'],
                depends_on=[],  # Will be loaded separately
                evidence=evidence_map[row['evidence_id']]
            )
            runner_list.append(runner)
        return runner_list
    
    def _load_utilities(self, conn: sqlite3.Connection, rig_id: int, evidence_map: Dict[int, Evidence]) -> List[Utility]:
        """Load utilities."""
        cursor = conn.execute("SELECT * FROM utilities WHERE rig_id = ?", (rig_id,))
        utility_list = []
        for row in cursor.fetchall():
            utility = Utility(
                id=row['id'],
                name=row['name'],
                depends_on=[],  # Will be loaded separately
                evidence=evidence_map[row['evidence_id']]
            )
            utility_list.append(utility)
        return utility_list
    
    def _load_tests(self, conn: sqlite3.Connection, rig_id: int, evidence_map: Dict[int, Evidence], component_map: Dict[int, Component], runner_map: Dict[int, Runner]) -> List[Test]:
        """Load tests."""
        cursor = conn.execute("SELECT * FROM tests WHERE rig_id = ?", (rig_id,))
        test_list = []
        for row in cursor.fetchall():
            test_executable = None
            if row['test_executable_id'] and row['test_executable_id'] in component_map:
                test_executable = component_map[row['test_executable_id']]
            
            test_runner = None
            if row['test_runner_id'] and row['test_runner_id'] in runner_map:
                test_runner = runner_map[row['test_runner_id']]
            
            test = Test(
                id=row['id'],
                name=row['name'],
                test_executable=test_executable,
                components_being_tested=[],  # Will be loaded separately
                test_runner=test_runner,
                source_files=[],  # Will be loaded separately
                test_framework=row['test_framework'],
                evidence=evidence_map[row['evidence_id']]
            )
            test_list.append(test)
        return test_list
    
    def _load_dependencies(self, conn: sqlite3.Connection, rig_id: int, rig: RIG, component_map: Dict[int, Component], aggregator_map: Dict[int, Aggregator], runner_map: Dict[int, Runner], utility_map: Dict[int, Utility]) -> None:
        """Load all dependency relationships."""
        # Load component dependencies
        cursor = conn.execute("SELECT * FROM component_dependencies WHERE rig_id = ?", (rig_id,))
        for row in cursor.fetchall():
            component = component_map[row['component_id']]
            dep = self._find_dependency_target(row, component_map, aggregator_map, runner_map, utility_map)
            if dep:
                component.depends_on.append(dep)
        
        # Load aggregator dependencies
        cursor = conn.execute("SELECT * FROM aggregator_dependencies WHERE rig_id = ?", (rig_id,))
        for row in cursor.fetchall():
            aggregator = aggregator_map[row['aggregator_id']]
            dep = self._find_dependency_target(row, component_map, aggregator_map, runner_map, utility_map)
            if dep:
                aggregator.depends_on.append(dep)
        
        # Load runner dependencies
        cursor = conn.execute("SELECT * FROM runner_dependencies WHERE rig_id = ?", (rig_id,))
        for row in cursor.fetchall():
            runner = runner_map[row['runner_id']]
            dep = self._find_dependency_target(row, component_map, aggregator_map, runner_map, utility_map)
            if dep:
                runner.depends_on.append(dep)
        
        # Load utility dependencies
        cursor = conn.execute("SELECT * FROM utility_dependencies WHERE rig_id = ?", (rig_id,))
        for row in cursor.fetchall():
            utility = utility_map[row['utility_id']]
            dep = self._find_dependency_target(row, component_map, aggregator_map, runner_map, utility_map)
            if dep:
                utility.depends_on.append(dep)
    
    def _find_dependency_target(self, row, component_map: Dict[int, Component], aggregator_map: Dict[int, Aggregator], runner_map: Dict[int, Runner], utility_map: Dict[int, Utility]):
        """Find dependency target from database row."""
        if row['depends_on_component_id'] and row['depends_on_component_id'] in component_map:
            return component_map[row['depends_on_component_id']]
        elif row['depends_on_aggregator_id'] and row['depends_on_aggregator_id'] in aggregator_map:
            return aggregator_map[row['depends_on_aggregator_id']]
        elif row['depends_on_runner_id'] and row['depends_on_runner_id'] in runner_map:
            return runner_map[row['depends_on_runner_id']]
        elif row['depends_on_utility_id'] and row['depends_on_utility_id'] in utility_map:
            return utility_map[row['depends_on_utility_id']]
        return None
    
    def _load_test_relationships(self, conn: sqlite3.Connection, rig_id: int, rig: RIG, test_map: Dict[int, Test], component_map: Dict[int, Component]) -> None:
        """Load test-to-component relationships."""
        cursor = conn.execute("SELECT * FROM test_components WHERE rig_id = ?", (rig_id,))
        for row in cursor.fetchall():
            test = test_map[row['test_id']]
            component = component_map[row['component_id']]
            test.components_being_tested.append(component)
    
    def _load_source_files(self, conn: sqlite3.Connection, rig_id: int, rig: RIG, component_map: Dict[int, Component], test_map: Dict[int, Test]) -> None:
        """Load source file relationships."""
        # Load component source files
        cursor = conn.execute("SELECT * FROM component_source_files WHERE rig_id = ?", (rig_id,))
        for row in cursor.fetchall():
            component = component_map[row['component_id']]
            component.source_files.append(Path(row['source_file_path']))
        
        # Load test source files
        cursor = conn.execute("SELECT * FROM test_source_files WHERE rig_id = ?", (rig_id,))
        for row in cursor.fetchall():
            test = test_map[row['test_id']]
            test.source_files.append(Path(row['source_file_path']))
    
    def _load_external_package_relationships(self, conn: sqlite3.Connection, rig_id: int, rig: RIG, component_map: Dict[int, Component], ep_map: Dict[int, ExternalPackage]) -> None:
        """Load component-to-external-package relationships."""
        cursor = conn.execute("SELECT * FROM component_external_packages WHERE rig_id = ?", (rig_id,))
        for row in cursor.fetchall():
            component = component_map[row['component_id']]
            ep = ep_map[row['external_package_id']]
            component.external_packages.append(ep)
    
    def _load_location_relationships(self, conn: sqlite3.Connection, rig_id: int, rig: RIG, component_map: Dict[int, Component], location_map: Dict[int, ComponentLocation]) -> None:
        """Load component-to-location relationships."""
        cursor = conn.execute("SELECT * FROM component_locations_rel WHERE rig_id = ?", (rig_id,))
        for row in cursor.fetchall():
            component = component_map[row['component_id']]
            location = location_map[row['location_id']]
            component.locations.append(location)


# Convenience functions
def save_rig(rig: RIG, db_path: Union[str, Path], description: str = "RIG Export") -> int:
    """Save RIG to SQLite database."""
    store = RIGStore(db_path)
    return store.save_rig(rig, description)


def load_rig(rig_id: int, db_path: Union[str, Path]) -> RIG:
    """Load RIG from SQLite database."""
    store = RIGStore(db_path)
    return store.load_rig(rig_id)
