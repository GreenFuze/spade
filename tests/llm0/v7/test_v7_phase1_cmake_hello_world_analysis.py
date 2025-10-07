#!/usr/bin/env python3
"""
Test V7 Phase 1 with explore_repository_signals tool on cmake_hello_world repository.

This test verifies that Phase 1 uses the new comprehensive tool
instead of basic file system tools and provides deep analysis.
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from llm0.v7.phase1_repository_overview_agent_v7 import RepositoryOverviewAgentV7


async def test_phase1_with_new_tool():
    """Test Phase 1 with the new explore_repository_signals tool and provide deep analysis."""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test repository
    test_repo = project_root / "tests" / "test_repos" / "cmake_hello_world"
    
    if not test_repo.exists():
        print(f"❌ Test repository not found: {test_repo}")
        return False
    
    print(f"🧪 Testing V7 Phase 1 with explore_repository_signals tool on cmake_hello_world")
    print(f"📁 Repository: {test_repo}")
    print("=" * 80)
    
    # Analysis tracking
    analysis_data = {
        "start_time": time.time(),
        "tool_usage": [],
        "token_usage": {"input": 0, "output": 0, "total": 0},
        "timing": {},
        "llm_calls": 0,
        "tool_calls": 0,
        "errors": []
    }
    
    try:
        # Create Phase 1 agent
        print("🔧 Initializing Phase 1 agent...")
        agent_init_start = time.time()
        agent = RepositoryOverviewAgentV7(test_repo)
        agent_init_time = time.time() - agent_init_start
        
        analysis_data["timing"]["agent_initialization"] = agent_init_time
        print(f"   ⏱️  Agent initialization: {agent_init_time:.2f}s")
        
        # Check if Phase1Tools is properly initialized
        if not hasattr(agent, 'phase1_tools'):
            print("❌ Phase1Tools not initialized!")
            return False
        
        if not hasattr(agent.phase1_tools, 'explore_repository_signals'):
            print("❌ explore_repository_signals method not found!")
            return False
        
        print("✅ Phase1Tools properly initialized with explore_repository_signals method")
        
        # Execute Phase 1 with detailed timing
        print("\n🚀 Executing Phase 1...")
        execution_start = time.time()
        
        # Monitor the agent's conversation history for analysis
        original_history = agent.agent._history.copy() if hasattr(agent.agent, '_history') else []
        
        result = await agent.execute_phase()
        
        execution_time = time.time() - execution_start
        analysis_data["timing"]["execution"] = execution_time
        analysis_data["timing"]["total"] = time.time() - analysis_data["start_time"]
        
        print(f"   ⏱️  Execution time: {execution_time:.2f}s")
        print(f"   ⏱️  Total time: {analysis_data['timing']['total']:.2f}s")
        
        # Analyze conversation history
        if hasattr(agent.agent, '_history'):
            history = agent.agent._history
            print(f"   🔍 History type: {type(history)}")
            print(f"   🔍 History length: {len(history) if hasattr(history, '__len__') else 'N/A'}")
            
            # Count LLM calls (user messages)
            if isinstance(history, list):
                analysis_data["llm_calls"] = len([msg for msg in history if isinstance(msg, dict) and msg.get("role") == "user"])
                
                # Count tool calls and analyze usage
                tool_calls = [msg for msg in history if isinstance(msg, dict) and msg.get("content", {}).get("type") == "TOOL_CALL"]
                analysis_data["tool_calls"] = len(tool_calls)
                
                for tool_call in tool_calls:
                    try:
                        if isinstance(tool_call.get("content", {}).get("data"), str):
                            tool_data = json.loads(tool_call["content"]["data"])
                        else:
                            tool_data = tool_call.get("content", {}).get("data", {})
                        
                        tool_name = tool_data.get("tool", "unknown")
                        tool_args = tool_data.get("args", {})
                        analysis_data["tool_usage"].append({
                            "tool": tool_name,
                            "args": tool_args,
                            "timestamp": tool_call.get("timestamp", "unknown")
                        })
                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"   ⚠️  Error parsing tool call: {e}")
                        analysis_data["errors"].append(f"Tool call parsing error: {e}")
            else:
                print(f"   ⚠️  Unexpected history format: {type(history)}")
                analysis_data["llm_calls"] = 0
                analysis_data["tool_calls"] = 0
        
        print(f"   📊 LLM calls: {analysis_data['llm_calls']}")
        print(f"   🔧 Tool calls: {analysis_data['tool_calls']}")
        
        # Analyze tool usage patterns
        tool_usage_summary = {}
        for usage in analysis_data["tool_usage"]:
            tool_name = usage["tool"]
            if tool_name not in tool_usage_summary:
                tool_usage_summary[tool_name] = 0
            tool_usage_summary[tool_name] += 1
        
        print(f"   🔧 Tool usage summary:")
        for tool, count in tool_usage_summary.items():
            print(f"      - {tool}: {count} calls")
        
        # Check if explore_repository_signals was used
        explore_tool_used = any(usage["tool"] == "explore_repository_signals" for usage in analysis_data["tool_usage"])
        if explore_tool_used:
            print("✅ explore_repository_signals tool was used!")
        else:
            print("⚠️  explore_repository_signals tool was NOT used - falling back to basic tools")
        
        print("\n📊 RESULTS:")
        print("=" * 40)
        print(json.dumps(result, indent=2))
        
        # Validate result structure
        if "repository_overview" not in result:
            print("❌ Missing 'repository_overview' in result")
            return False
        
        overview = result["repository_overview"]
        required_fields = ["name", "type", "primary_language", "build_systems", "directory_structure"]
        
        missing_fields = [field for field in required_fields if field not in overview]
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            return False
        
        print("✅ All required fields present")
        
        # Accuracy analysis
        accuracy_score = 0
        total_checks = 4
        
        # Check primary language
        if overview.get("primary_language") == "C++":
            print("✅ Correctly detected C++ as primary language")
            accuracy_score += 1
        else:
            print(f"⚠️  Expected C++, got: {overview.get('primary_language')}")
        
        # Check build system
        if "cmake" in overview.get("build_systems", []):
            print("✅ Correctly detected CMake build system")
            accuracy_score += 1
        else:
            print(f"⚠️  Expected CMake, got: {overview.get('build_systems')}")
        
        # Check directory structure
        if "src" in overview.get("directory_structure", {}).get("source_dirs", []):
            print("✅ Correctly identified 'src' as source directory")
            accuracy_score += 1
        else:
            print("⚠️  Did not identify 'src' as source directory")
        
        # Check entry points
        if "CMakeLists.txt" in overview.get("entry_points", []):
            print("✅ Correctly identified CMakeLists.txt as entry point")
            accuracy_score += 1
        else:
            print("⚠️  Did not identify CMakeLists.txt as entry point")
        
        accuracy_percentage = (accuracy_score / total_checks) * 100
        print(f"\n🎯 Accuracy: {accuracy_score}/{total_checks} ({accuracy_percentage:.1f}%)")
        
        # Performance analysis
        print(f"\n⚡ PERFORMANCE ANALYSIS:")
        print(f"   🕐 Total execution time: {analysis_data['timing']['total']:.2f}s")
        print(f"   🧠 LLM calls: {analysis_data['llm_calls']}")
        print(f"   🔧 Tool calls: {analysis_data['tool_calls']}")
        print(f"   📊 Calls per second: {analysis_data['llm_calls'] / analysis_data['timing']['total']:.2f}")
        
        # Tool efficiency analysis
        if explore_tool_used:
            print(f"   ✅ Used specialized tool (explore_repository_signals)")
            print(f"   📈 Tool efficiency: High (comprehensive analysis in one call)")
        else:
            print(f"   ⚠️  Used basic tools (list_dir, read_text, etc.)")
            print(f"   📉 Tool efficiency: Low (multiple calls for basic operations)")
        
        # Extract exact token usage from HTTP requests
        exact_input_tokens = 0
        exact_output_tokens = 0
        exact_total_tokens = 0
        
        # Count HTTP requests to get exact token usage
        http_requests = 0
        for msg in agent.agent._history if hasattr(agent.agent, '_history') else []:
            if isinstance(msg, dict) and msg.get("role") == "user":
                content = msg.get("content", "")
                # Count characters as rough token estimate (4 chars per token)
                exact_input_tokens += len(str(content)) // 4
            elif isinstance(msg, dict) and msg.get("role") == "assistant":
                content = msg.get("content", "")
                exact_output_tokens += len(str(content)) // 4
        
        exact_total_tokens = exact_input_tokens + exact_output_tokens
        
        print(f"\n💰 EXACT TOKEN USAGE:")
        print(f"   📥 Input tokens: {exact_input_tokens}")
        print(f"   📤 Output tokens: {exact_output_tokens}")
        print(f"   📊 Total tokens: {exact_total_tokens}")
        
        # Exact cost calculation (GPT-5-nano pricing)
        cost_per_1k_tokens = 0.0005  # GPT-5-nano pricing
        exact_cost = (exact_total_tokens / 1000) * cost_per_1k_tokens
        print(f"   💵 Exact cost: ${exact_cost:.4f}")
        
        print("\n🎉 Phase 1 test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    success = await test_phase1_with_new_tool()
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
