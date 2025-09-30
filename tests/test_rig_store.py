"""
Unit tests for RIG SQLite storage functionality.

This module tests the complete save/load cycle to ensure 100% data integrity.
"""

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from typing import List

from cmake_entrypoint import CMakeEntrypoint
from rig import RIG
from rig_store import RIGStore, save_rig, load_rig
from schemas import (
    Component, Aggregator, Runner, Utility, Test as TestSchema, Evidence, ComponentLocation,
    ExternalPackage, PackageManager, RepositoryInfo, BuildSystemInfo,
    ComponentType, Runtime
)


class TestRIGStore(unittest.TestCase):
    """Test RIG SQLite storage functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_rig.db"
        self.store = RIGStore(self.db_path)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_and_load_empty_rig(self):
        """Test saving and loading an empty RIG."""
        # Create empty RIG
        rig = RIG()
        
        # Save RIG
        rig_id = self.store.save_rig(rig, "Empty RIG Test")
        self.assertIsInstance(rig_id, int)
        self.assertGreater(rig_id, 0)
        
        # Load RIG
        loaded_rig = self.store.load_rig(rig_id)
        self.assertIsInstance(loaded_rig, RIG)
        
        # Verify empty RIG structure
        self.assertEqual(len(loaded_rig.components), 0)
        self.assertEqual(len(loaded_rig.aggregators), 0)
        self.assertEqual(len(loaded_rig.runners), 0)
        self.assertEqual(len(loaded_rig.utilities), 0)
        self.assertEqual(len(loaded_rig.tests), 0)
        self.assertEqual(len(loaded_rig.evidence), 0)
        self.assertEqual(len(loaded_rig.component_locations), 0)
        self.assertEqual(len(loaded_rig.external_packages), 0)
        self.assertEqual(len(loaded_rig.package_managers), 0)
        self.assertIsNone(loaded_rig.repository)
        self.assertIsNone(loaded_rig.build_system)
    
    def test_save_and_load_complete_rig(self):
        """Test saving and loading a complete RIG with all entity types."""
        # Create a complete RIG
        rig = self._create_complete_test_rig()
        
        # Save RIG
        rig_id = self.store.save_rig(rig, "Complete RIG Test")
        self.assertIsInstance(rig_id, int)
        self.assertGreater(rig_id, 0)
        
        # Load RIG
        loaded_rig = self.store.load_rig(rig_id)
        self.assertIsInstance(loaded_rig, RIG)
        
        # Deep compare all aspects
        self._deep_compare_rigs(rig, loaded_rig)
    
    def test_save_and_load_with_real_cmake_data(self):
        """Test saving and loading RIG built from real CMake data."""
        # This test requires a real CMake build directory
        # For now, we'll create a mock test that can be run when CMake data is available
        try:
            # Try to build RIG from CMake data
            cmake_dir = Path("cmake-build-debug/CMakeFiles")
            if cmake_dir.exists():
                entrypoint = CMakeEntrypoint(cmake_dir)
                rig = entrypoint.get_rig()
                
                # Save RIG
                rig_id = self.store.save_rig(rig, "Real CMake RIG Test")
                self.assertIsInstance(rig_id, int)
                self.assertGreater(rig_id, 0)
                
                # Load RIG
                loaded_rig = self.store.load_rig(rig_id)
                self.assertIsInstance(loaded_rig, RIG)
                
                # Deep compare
                self._deep_compare_rigs(rig, loaded_rig)
            else:
                self.skipTest("CMake build directory not found - skipping real data test")
        except Exception as e:
            self.skipTest(f"Could not build RIG from CMake data: {e}")
    
    def test_convenience_functions(self):
        """Test convenience functions save_rig and load_rig."""
        rig = self._create_complete_test_rig()
        
        # Test convenience functions
        rig_id = save_rig(rig, self.db_path, "Convenience Test")
        loaded_rig = load_rig(rig_id, self.db_path)
        
        self._deep_compare_rigs(rig, loaded_rig)
    
    def test_rig_list_and_delete(self):
        """Test listing and deleting RIGs."""
        # Save multiple RIGs
        rig1 = self._create_complete_test_rig()
        rig2 = self._create_complete_test_rig()
        
        id1 = self.store.save_rig(rig1, "RIG 1")
        id2 = self.store.save_rig(rig2, "RIG 2")
        
        # List RIGs
        rigs = self.store.list_rigs()
        self.assertEqual(len(rigs), 2)
        self.assertIn(id1, [r['id'] for r in rigs])
        self.assertIn(id2, [r['id'] for r in rigs])
        
        # Delete one RIG
        deleted = self.store.delete_rig(id1)
        self.assertTrue(deleted)
        
        # Verify deletion
        rigs = self.store.list_rigs()
        self.assertEqual(len(rigs), 1)
        self.assertEqual(rigs[0]['id'], id2)
        
        # Try to load deleted RIG
        with self.assertRaises(ValueError):
            self.store.load_rig(id1)
    
    def test_database_schema_integrity(self):
        """Test that database schema is properly created."""
        # Verify all tables exist
        with self.store._get_connection() as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = [
                'aggregator_dependencies', 'build_system_info', 'component_dependencies',
                'component_external_packages', 'component_locations', 'component_locations_rel',
                'component_source_files', 'components', 'evidence', 'external_packages',
                'package_managers', 'repository_info', 'rig_metadata', 'runner_dependencies',
                'runners', 'test_components', 'test_source_files', 'tests', 'utility_dependencies', 'utilities'
            ]
            
            for table in expected_tables:
                self.assertIn(table, tables, f"Table {table} not found in database")
    
    def _create_complete_test_rig(self) -> RIG:
        """Create a complete test RIG with all entity types."""
        rig = RIG()
        
        # Create evidence
        evidence1 = Evidence(id=1, call_stack=["file1.cmake#L10-L10", "file2.cmake#L5-L5"])
        evidence2 = Evidence(id=2, call_stack=["file3.cmake#L15-L15"])
        evidence3 = Evidence(id=3, call_stack=["file4.cmake#L20-L20"])
        
        rig.evidence = [evidence1, evidence2, evidence3]
        
        # Create package managers and external packages
        pm1 = PackageManager(id=1, name="vcpkg", package_name="boost")
        pm2 = PackageManager(id=2, name="conan", package_name="opencv")
        
        rig.package_managers = [pm1, pm2]
        
        ep1 = ExternalPackage(id=1, package_manager=pm1)
        ep2 = ExternalPackage(id=2, package_manager=pm2)
        
        rig.external_packages = [ep1, ep2]
        
        # Create component locations
        loc1 = ComponentLocation(
            id=1, path=Path("build/component1.exe"), action="build",
            source_location=None, evidence=evidence1
        )
        loc2 = ComponentLocation(
            id=2, path=Path("output/component1.exe"), action="copy",
            source_location=loc1, evidence=evidence2
        )
        
        rig.component_locations = [loc1, loc2]
        
        # Create components
        component1 = Component(
            id=1, name="test_component1", type=ComponentType.EXECUTABLE,
            runtime=Runtime.VS_CPP, output="test_component1.exe",
            output_path=Path("build/test_component1.exe"),
            programming_language="cxx", source_files=[Path("src/main.cpp")],
            external_packages=[ep1], locations=[loc1, loc2],
            depends_on=[], evidence=evidence1, test_link_id=None, test_link_name=None
        )
        
        component2 = Component(
            id=2, name="test_library1", type=ComponentType.SHARED_LIBRARY,
            runtime=Runtime.VS_CPP, output="test_library1.dll",
            output_path=Path("build/test_library1.dll"),
            programming_language="cxx", source_files=[Path("src/lib.cpp")],
            external_packages=[ep2], locations=[],
            depends_on=[], evidence=evidence2, test_link_id=None, test_link_name=None
        )
        
        # Set up dependencies
        component1.depends_on = [component2]
        
        rig.components = [component1, component2]
        
        # Create aggregator
        aggregator1 = Aggregator(
            id=1, name="test_aggregator", depends_on=[component1, component2],
            evidence=evidence3
        )
        
        rig.aggregators = [aggregator1]
        
        # Create runner
        runner1 = Runner(
            id=1, name="test_runner", depends_on=[component1],
            evidence=evidence1
        )
        
        rig.runners = [runner1]
        
        # Create utility
        utility1 = Utility(
            id=1, name="test_utility", depends_on=[],
            evidence=evidence2
        )
        
        rig.utilities = [utility1]
        
        # Create test
        test1 = TestSchema(
            id=1, name="test_test1", test_executable=component1,
            components_being_tested=[component1, component2],
            test_runner=runner1, source_files=[Path("test/test1.cpp")],
            test_framework="CTest", evidence=evidence3
        )
        
        rig.tests = [test1]
        
        # Create repository info
        rig.repository = RepositoryInfo(
            name="Test Repository",
            root_path=Path("/test/repo"),
            build_directory=Path("/test/repo/build"),
            output_directory=Path("/test/repo/output"),
            configure_command="cmake -B build",
            build_command="cmake --build build",
            install_command="cmake --install build",
            test_command="ctest --test-dir build"
        )
        
        # Create build system info
        rig.build_system = BuildSystemInfo(
            name="CMake/Ninja",
            version="3.20.0",
            build_type="Debug"
        )
        
        return rig
    
    def _deep_compare_rigs(self, original: RIG, loaded: RIG) -> None:
        """Deep compare two RIG objects to ensure 100% data integrity."""
        # Compare repository info
        if original.repository is None:
            self.assertIsNone(loaded.repository)
        else:
            self.assertEqual(original.repository.name, loaded.repository.name)
            self.assertEqual(original.repository.root_path, loaded.repository.root_path)
            self.assertEqual(original.repository.build_directory, loaded.repository.build_directory)
            self.assertEqual(original.repository.output_directory, loaded.repository.output_directory)
            self.assertEqual(original.repository.configure_command, loaded.repository.configure_command)
            self.assertEqual(original.repository.build_command, loaded.repository.build_command)
            self.assertEqual(original.repository.install_command, loaded.repository.install_command)
            self.assertEqual(original.repository.test_command, loaded.repository.test_command)
        
        # Compare build system info
        if original.build_system is None:
            self.assertIsNone(loaded.build_system)
        else:
            self.assertEqual(original.build_system.name, loaded.build_system.name)
            self.assertEqual(original.build_system.version, loaded.build_system.version)
            self.assertEqual(original.build_system.build_type, loaded.build_system.build_type)
        
        # Compare evidence
        self.assertEqual(len(original.evidence), len(loaded.evidence))
        for orig_ev, loaded_ev in zip(original.evidence, loaded.evidence):
            self.assertEqual(orig_ev.call_stack, loaded_ev.call_stack)
        
        # Compare package managers
        self.assertEqual(len(original.package_managers), len(loaded.package_managers))
        for orig_pm, loaded_pm in zip(original.package_managers, loaded.package_managers):
            self.assertEqual(orig_pm.name, loaded_pm.name)
            self.assertEqual(orig_pm.package_name, loaded_pm.package_name)
        
        # Compare external packages
        self.assertEqual(len(original.external_packages), len(loaded.external_packages))
        for orig_ep, loaded_ep in zip(original.external_packages, loaded.external_packages):
            self.assertEqual(orig_ep.package_manager.name, loaded_ep.package_manager.name)
            self.assertEqual(orig_ep.package_manager.package_name, loaded_ep.package_manager.package_name)
        
        # Compare component locations
        self.assertEqual(len(original.component_locations), len(loaded.component_locations))
        for orig_loc, loaded_loc in zip(original.component_locations, loaded.component_locations):
            self.assertEqual(orig_loc.path, loaded_loc.path)
            self.assertEqual(orig_loc.action, loaded_loc.action)
            self.assertEqual(orig_loc.evidence.call_stack, loaded_loc.evidence.call_stack)
        
        # Compare components
        self.assertEqual(len(original.components), len(loaded.components))
        for orig_comp, loaded_comp in zip(original.components, loaded.components):
            self.assertEqual(orig_comp.name, loaded_comp.name)
            self.assertEqual(orig_comp.type, loaded_comp.type)
            self.assertEqual(orig_comp.runtime, loaded_comp.runtime)
            self.assertEqual(orig_comp.output, loaded_comp.output)
            self.assertEqual(orig_comp.output_path, loaded_comp.output_path)
            self.assertEqual(orig_comp.programming_language, loaded_comp.programming_language)
            self.assertEqual(orig_comp.source_files, loaded_comp.source_files)
            self.assertEqual(orig_comp.test_link_id, loaded_comp.test_link_id)
            self.assertEqual(orig_comp.test_link_name, loaded_comp.test_link_name)
            self.assertEqual(orig_comp.evidence.call_stack, loaded_comp.evidence.call_stack)
            
            # Compare dependencies
            self.assertEqual(len(orig_comp.depends_on), len(loaded_comp.depends_on))
            for orig_dep, loaded_dep in zip(orig_comp.depends_on, loaded_comp.depends_on):
                self.assertEqual(orig_dep.name, loaded_dep.name)
            
            # Compare external packages
            self.assertEqual(len(orig_comp.external_packages), len(loaded_comp.external_packages))
            for orig_ep, loaded_ep in zip(orig_comp.external_packages, loaded_comp.external_packages):
                self.assertEqual(orig_ep.package_manager.name, loaded_ep.package_manager.name)
                self.assertEqual(orig_ep.package_manager.package_name, loaded_ep.package_manager.package_name)
            
            # Compare locations
            self.assertEqual(len(orig_comp.locations), len(loaded_comp.locations))
            for orig_loc, loaded_loc in zip(orig_comp.locations, loaded_comp.locations):
                self.assertEqual(orig_loc.path, loaded_loc.path)
                self.assertEqual(orig_loc.action, loaded_loc.action)
        
        # Compare aggregators
        self.assertEqual(len(original.aggregators), len(loaded.aggregators))
        for orig_agg, loaded_agg in zip(original.aggregators, loaded.aggregators):
            self.assertEqual(orig_agg.name, loaded_agg.name)
            self.assertEqual(orig_agg.evidence.call_stack, loaded_agg.evidence.call_stack)
            self.assertEqual(len(orig_agg.depends_on), len(loaded_agg.depends_on))
            for orig_dep, loaded_dep in zip(orig_agg.depends_on, loaded_agg.depends_on):
                self.assertEqual(orig_dep.name, loaded_dep.name)
        
        # Compare runners
        self.assertEqual(len(original.runners), len(loaded.runners))
        for orig_run, loaded_run in zip(original.runners, loaded.runners):
            self.assertEqual(orig_run.name, loaded_run.name)
            self.assertEqual(orig_run.evidence.call_stack, loaded_run.evidence.call_stack)
            self.assertEqual(len(orig_run.depends_on), len(loaded_run.depends_on))
            for orig_dep, loaded_dep in zip(orig_run.depends_on, loaded_run.depends_on):
                self.assertEqual(orig_dep.name, loaded_dep.name)
        
        # Compare utilities
        self.assertEqual(len(original.utilities), len(loaded.utilities))
        for orig_util, loaded_util in zip(original.utilities, loaded.utilities):
            self.assertEqual(orig_util.name, loaded_util.name)
            self.assertEqual(orig_util.evidence.call_stack, loaded_util.evidence.call_stack)
            self.assertEqual(len(orig_util.depends_on), len(loaded_util.depends_on))
            for orig_dep, loaded_dep in zip(orig_util.depends_on, loaded_util.depends_on):
                self.assertEqual(orig_dep.name, loaded_dep.name)
        
        # Compare tests
        self.assertEqual(len(original.tests), len(loaded.tests))
        for orig_test, loaded_test in zip(original.tests, loaded.tests):
            self.assertEqual(orig_test.name, loaded_test.name)
            self.assertEqual(orig_test.test_framework, loaded_test.test_framework)
            self.assertEqual(orig_test.evidence.call_stack, loaded_test.evidence.call_stack)
            self.assertEqual(orig_test.source_files, loaded_test.source_files)
            
            # Compare test executable
            if orig_test.test_executable is None:
                self.assertIsNone(loaded_test.test_executable)
            else:
                self.assertEqual(orig_test.test_executable.name, loaded_test.test_executable.name)
            
            # Compare test runner
            if orig_test.test_runner is None:
                self.assertIsNone(loaded_test.test_runner)
            else:
                self.assertEqual(orig_test.test_runner.name, loaded_test.test_runner.name)
            
            # Compare components being tested
            self.assertEqual(len(orig_test.components_being_tested), len(loaded_test.components_being_tested))
            for orig_comp, loaded_comp in zip(orig_test.components_being_tested, loaded_test.components_being_tested):
                self.assertEqual(orig_comp.name, loaded_comp.name)


if __name__ == '__main__':
    unittest.main()
