#!/usr/bin/env python3
"""
Debug V3 approach to identify the issue with delegate_ops tool.
"""

import sys
import asyncio
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

async def test_simple_agent():
    """Test a simple agent to see if the issue is with the setup."""
    print("Testing simple agent...")
    
    test_path = Path("test_repos/cmake_hello_world")
    
    # Create tools
    file_tools = FileTools(root_dir=str(test_path))
    process_tools = ProcessTools(root_cwd=str(test_path))
    
    # Create agent
    agent = DelegatingToolsAgent(
        model="openai:gpt-5-nano",
        tool_sources=[file_tools, process_tools],
        builtin_enums=[],
        model_settings=ModelSettings(temperature=0),
        real_time_log_user=True,
        real_time_log_agent=True
    )
    
    prompt = """
Please read the file CMakeLists.txt and tell me what build system this is.
"""
    
    try:
        response = await agent.run(prompt)
        print(f"Response: {response}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_simple_agent())
    print(f"Test {'PASSED' if success else 'FAILED'}")
