#!/usr/bin/env python3
"""
Debug path issue in V3.
"""

import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Add agentkit-gf to path
agentkit_gf_path = Path(__file__).parent / "agentkit_gf"
sys.path.insert(0, str(agentkit_gf_path))

from agentkit_gf.delegating_tools_agent import DelegatingToolsAgent
from agentkit_gf.tools.fs import FileTools
from agentkit_gf.tools.os import ProcessTools
from pydantic_ai.settings import ModelSettings

def test_paths():
    """Test path resolution."""
    test_path = Path("test_repos/cmake_hello_world")
    
    print(f"Current working directory: {Path.cwd()}")
    print(f"Test path: {test_path}")
    print(f"Test path absolute: {test_path.absolute()}")
    print(f"Test path exists: {test_path.exists()}")
    print(f"CMakeLists.txt exists: {(test_path / 'CMakeLists.txt').exists()}")
    
    # Test with absolute path
    abs_path = test_path.absolute()
    print(f"Absolute path: {abs_path}")
    print(f"Absolute path exists: {abs_path.exists()}")
    print(f"CMakeLists.txt exists: {(abs_path / 'CMakeLists.txt').exists()}")
    
    # Test FileTools
    file_tools = FileTools(root_dir=str(abs_path))
    print(f"FileTools root_dir: {file_tools.root_dir}")
    
    # Test ProcessTools
    process_tools = ProcessTools(root_cwd=str(abs_path))
    print(f"ProcessTools root_cwd: {process_tools.root_cwd}")

if __name__ == "__main__":
    test_paths()
