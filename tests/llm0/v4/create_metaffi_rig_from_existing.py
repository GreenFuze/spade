#!/usr/bin/env python3
"""
Create HTML graph for MetaFFI using existing phase results
"""

import sys
import json
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from core.rig import RIG
from core.schemas import RepositoryInfo, BuildSystemInfo, Component, ComponentType, Runtime, Evidence, ComponentLocation


def create_metaffi_rig_from_phase1():
    """Create RIG from existing Phase 1 results and generate HTML graph."""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("create_metaffi_rig_from_phase1")
    
    try:
        # Load existing Phase 1 results
        phase1_file = project_root / "phase1_output.json"
        if not phase1_file.exists():
            logger.error(f"Phase 1 results not found: {phase1_file}")
            return False
        
        logger.info("Loading existing Phase 1 results...")
        with open(phase1_file, 'r') as f:
            phase1_data = json.load(f)
        
        # Create RIG
        rig = RIG()
        
        # Set repository info from Phase 1
        repo_overview = phase1_data.get("repository_overview", {})
        rig._repository_info = RepositoryInfo(
            name=repo_overview.get("name", "MetaFFI"),
            root_path="C:/src/github.com/MetaFFI",
            build_directory=repo_overview.get("directory_structure", {}).get("build_dirs", ["build"])[0] if repo_overview.get("directory_structure", {}).get("build_dirs") else "build",
            output_directory="output",
            configure_command="cmake .",
            build_command="cmake --build .",
            install_command="cmake --install .",
            test_command="ctest"
        )
        
        # Set build system info
        build_systems = repo_overview.get("build_systems", [])
        if build_systems:
            rig._build_system_info = BuildSystemInfo(
                name=build_systems[0].title(),  # "cmake" -> "CMake"
                version="3.10+",
                build_type="Debug"
            )
        
        # Create basic components from directory structure
        source_dirs = repo_overview.get("directory_structure", {}).get("source_dirs", [])
        for i, source_dir in enumerate(source_dirs):
            component = Component(
                name=source_dir,
                type=ComponentType.LIBRARY if "plugin" in source_dir.lower() else ComponentType.EXECUTABLE,
                programming_language="C++",
                runtime=Runtime.VS_CPP,
                source_files=[f"{source_dir}/**/*.cpp", f"{source_dir}/**/*.h"],
                output_path=f"build/{source_dir}",
                evidence=[
                    Evidence(
                        file="Repository Overview",
                        lines="N/A",
                        content=f"Directory structure analysis identified {source_dir}",
                        reason="Phase 1 repository overview analysis"
                    )
                ],
                dependencies=[],
                test_relationship=None
            )
            rig._components.append(component)
            
            # Add evidence
            rig._evidence.append(component.evidence[0])
            
            # Add component location
            location = ComponentLocation(
                component_name=component.name,
                file_path=source_dir,
                line_start=1,
                line_end=1
            )
            rig._component_locations.append(location)
        
        logger.info("✅ RIG created from Phase 1 results!")
        logger.info(f"Repository: {rig._repository_info.name}")
        logger.info(f"Components: {len(rig._components)}")
        logger.info(f"Evidence: {len(rig._evidence)}")
        
        # Generate HTML graph
        logger.info("Generating HTML graph visualization...")
        rig.show_graph(validate_before_show=False)  # Skip validation since we're using partial data
        
        # Get the generated filename
        html_filename = f"rig_{rig._repository_info.name}_graph.html"
        
        logger.info(f"✅ HTML graph created: {html_filename}")
        logger.info(f"Open {html_filename} in your browser to view the RIG graph")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create RIG HTML graph: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    print("Creating RIG HTML graph for MetaFFI from existing Phase 1 results...")
    
    success = create_metaffi_rig_from_phase1()
    
    if success:
        print("\n[OK] RIG HTML graph created successfully!")
        print("Open the HTML file in your browser to view the interactive graph.")
    else:
        print("\n[ERROR] RIG HTML graph creation failed.")
        print("Check the logs above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
