#!/usr/bin/env python3

from cmake_entrypoint import CMakeEntrypoint
from pathlib import Path
import json

# Create entrypoint without parsing CMake to avoid the full processing
entrypoint = CMakeEntrypoint(Path('C:/src/github.com/MetaFFI/cmake-build-debug/CMakeFiles'), parse_cmake=False)

# Manually create CMakeProject to access raw data
from cmake_file_api import CMakeProject
proj = CMakeProject(build_path=entrypoint.cmake_config_dir, source_path=entrypoint.repo_root, api_version=1)

# Get codemodel
codemodel = proj.get_codemodel()

print('Looking for metaffi.compiler.go target in CMake File API...')

for config in codemodel.configurations:
    for project in config.projects:
        for target in project.targets:
            if target.name == 'metaffi.compiler.go':
                print(f'Found target: {target.name}')
                print(f'Target type: {getattr(target, "type", "unknown")}')
                
                # Get the detailed target info
                detailed_target = proj.get_target(target.id)
                print(f'Detailed target type: {getattr(detailed_target, "type", "unknown")}')
                
                # Check for commands
                if hasattr(detailed_target, 'commands'):
                    print(f'Commands: {detailed_target.commands}')
                if hasattr(detailed_target, 'command'):
                    print(f'Command: {detailed_target.command}')
                    
                # Print all attributes
                attrs = [attr for attr in dir(detailed_target) if not attr.startswith('_')]
                print(f'Available attributes: {attrs}')
                
                # Check for any string attributes that might contain 'go'
                for attr in attrs:
                    try:
                        value = getattr(detailed_target, attr)
                        if isinstance(value, str) and 'go' in value.lower():
                            print(f'{attr}: {value}')
                        elif isinstance(value, list):
                            for item in value:
                                if isinstance(item, str) and 'go' in item.lower():
                                    print(f'{attr}: {item}')
                    except:
                        pass
                break
