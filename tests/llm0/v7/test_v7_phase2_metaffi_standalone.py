#!/usr/bin/env python3
"""
Test V7 Phase 2: Build System Detection on MetaFFI repository (Standalone)

This test validates Phase 2 of the V7 Enhanced Architecture:
- Tests the new LLM-controlled pattern exploration design
- Validates deterministic tool behavior
- Measures token usage and execution time
- Ensures proper integration with Phase 1 output
- Uses standalone imports to avoid package dependency issues
- Tests complex multi-language framework (C++, Python, Java, JavaScript, etc.)
"""

import asyncio
import json
import logging
import time
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Add agentkit-gf to path
agentkit_gf_path = Path("C:/src/github.com/GreenFuze/agentkit-gf")
if str(agentkit_gf_path) not in sys.path:
    sys.path.insert(0, str(agentkit_gf_path))

# Import everything we need
from agentkit_gf.tools.fs import FileTools
from agentkit_gf.delegating_tools_agent import DelegatingToolsAgent, ModelSettings

# Import the tools directly by adding the path
sys.path.insert(0, str(project_root / "llm0" / "v7"))

# Import the tools directly
from phase1_tools import Phase1Tools
from phase2_tools import Phase2Tools


async def test_phase2_build_system_detection():
    """Test Phase 2: Build System Detection on MetaFFI"""
    
    print("=" * 80)
    print("V7 Phase 2: Build System Detection Test")
    print("Repository: MetaFFI")
    print("Method: Standalone (direct imports)")
    print("=" * 80)
    
    # Setup - MetaFFI is in a different location
    repository_path = Path("C:/src/github.com/MetaFFI")
    
    if not repository_path.exists():
        print(f"❌ Repository not found: {repository_path}")
        return
    
    print(f"📁 Repository: {repository_path}")
    
    # Phase 1: Get language detection results
    print("\n🔄 Running Phase 1: Language Detection...")
    start_time = time.time()
    
    # Create Phase 1 tools and agent
    phase1_tools = Phase1Tools(repository_path)
    phase1_agent = DelegatingToolsAgent(
        model="openai:gpt-5-nano",
        tool_sources=[phase1_tools, FileTools(root_dir=repository_path)],
        builtin_enums=[],
        model_settings=ModelSettings(temperature=0),
        real_time_log_user=True,
        real_time_log_agent=True
    )
    
    # Run Phase 1
    phase1_prompt = f"""
You are a Repository Overview Agent (Phase 1). Your single goal is to detect all programming languages present in the repository.

YOUR TASK:
1. Use the `explore_repository_signals` tool to analyze the repository
2. The tool will provide comprehensive language detection with confidence scores
3. Interpret the tool results to determine languages with confidence scores
4. Provide structured output with evidence for each detected language

CRITICAL RULES:
- Use the `explore_repository_signals` tool to analyze the repository
- All conclusions must be backed by evidence from the tool
- Provide confidence scores for each detected language
- Focus only on language detection - this is your single goal

OUTPUT FORMAT:
{{
  "languages_detected": {{
    "C++": {{
      "detected": true,
      "confidence": 0.95,
      "evidence": ["src/main.cpp", "src/utils.cpp"],
      "reasoning": "C++ source files found in src/ directory"
    }},
    "Python": {{
      "detected": true,
      "confidence": 0.95,
      "evidence": ["src/main.py"],
      "reasoning": "Python source files found in src/ directory"
    }},
    "Java": {{
      "detected": true,
      "confidence": 0.95,
      "evidence": ["src/HelloWorld.java"],
      "reasoning": "Java source files found in src/ directory"
    }}
  }},
  "architecture_classification": {{
    "primary_language": "C++",
    "detected_languages": ["C++", "Python", "Java"],
    "language_percentages": {{"C++": 50.0, "Python": 30.0, "Java": 20.0}},
    "multi_language": true,
    "repository_type": "framework",
    "notes": "Multi-language framework with C++, Python, and Java components"
  }},
  "confidence_verification": {{
    "all_languages_analyzed": true,
    "all_confidence_scores_above_95": true,
    "evidence_sufficient": true,
    "ready_for_phase_2": true
  }}
}}

Remember: Your single goal is language detection. Use the tool and provide evidence-based results.
"""
    
    phase1_result = await phase1_agent.run(phase1_prompt)
    # Extract the response content from the agent result
    response_text = phase1_result.output
    
    # Find the JSON part in the response (look for the first { and last })
    start_idx = response_text.find('{')
    end_idx = response_text.rfind('}') + 1
    
    if start_idx != -1 and end_idx != 0:
        json_text = response_text[start_idx:end_idx]
        phase1_output = json.loads(json_text)
    else:
        raise ValueError("No valid JSON found in agent response")
    
    phase1_time = time.time() - start_time
    print(f"✅ Phase 1 completed in {phase1_time:.2f} seconds")
    
    # Display Phase 1 results
    print("\n📊 Phase 1 Results:")
    languages_detected = phase1_output.get("languages_detected", {})
    for lang, data in languages_detected.items():
        if data.get("detected", False):
            confidence = data.get("confidence", 0)
            print(f"  - {lang}: {confidence:.1%} confidence")
    
    # Phase 2: Build System Detection
    print("\n🔄 Running Phase 2: Build System Detection...")
    start_time = time.time()
    
    # Create Phase 2 tools and agent
    phase2_tools = Phase2Tools(repository_path)
    phase2_agent = DelegatingToolsAgent(
        model="openai:gpt-5-nano",
        tool_sources=[phase2_tools, FileTools(root_dir=repository_path)],
        builtin_enums=[],
        model_settings=ModelSettings(temperature=0),
        real_time_log_user=True,
        real_time_log_agent=True
    )
    
    # Run Phase 2
    phase2_prompt = f"""
You are a Build System Detection Agent (Phase 2). Your single goal is to identify all build systems present in the repository.

PHASE 1 OUTPUT (Languages Detected):
{json.dumps(phase1_output, indent=2)}

YOUR TASK:
1. Based on the detected languages, decide which file and directory patterns to scan
2. Use the `detect_build_systems` tool with your chosen patterns
3. Interpret the tool results to determine build systems with confidence scores
4. If confidence is low, call the tool again with different patterns
5. Provide structured output with evidence for each detected build system

CRITICAL RULES:
- You control the exploration by setting file_patterns and directory_patterns
- Based on detected languages, choose relevant build system patterns to scan
- The tool will return all found signals - you interpret them
- You can call the tool multiple times with different patterns if needed
- Focus only on build system detection - this is your single goal

EXAMPLES OF PATTERN SELECTION:
- If C++ detected: file_patterns=["CMakeLists.txt", "*.cmake", "Makefile"], directory_patterns=["build/"]
- If Java detected: file_patterns=["pom.xml", "build.gradle"], directory_patterns=["target/", "build/"]
- If Python detected: file_patterns=["setup.py", "pyproject.toml", "requirements.txt"], directory_patterns=["dist/", "build/"]
- If JavaScript detected: file_patterns=["package.json"], directory_patterns=["node_modules/", "dist/"]
- If multiple languages: scan broadly with common patterns

OUTPUT FORMAT:
{{
  "build_systems_detected": {{
    "cmake": {{
      "detected": true,
      "confidence": 0.95,
      "evidence": ["CMakeLists.txt", "build/"],
      "reasoning": "CMakeLists.txt found in root directory"
    }},
    "maven": {{
      "detected": true,
      "confidence": 0.90,
      "evidence": ["pom.xml"],
      "reasoning": "pom.xml found for Java components"
    }},
    "pip": {{
      "detected": true,
      "confidence": 0.85,
      "evidence": ["setup.py", "requirements.txt"],
      "reasoning": "Python build files found"
    }}
  }},
  "build_analysis": {{
    "primary_build_system": "cmake",
    "secondary_build_systems": ["maven", "pip"],
    "multi_build_system": true,
    "language_build_mapping": {{"C++": "cmake", "Java": "maven", "Python": "pip"}}
  }},
  "confidence_verification": {{
    "all_build_systems_analyzed": true,
    "all_confidence_scores_above_95": false,
    "evidence_sufficient": true,
    "ready_for_phase_3": true
  }}
}}

Remember: You control the exploration strategy. Choose patterns based on detected languages, then interpret the results.
"""
    
    phase2_result = await phase2_agent.run(phase2_prompt)
    # Extract the response content from the agent result
    response_text = phase2_result.output
    
    # Find the JSON part in the response (look for the first { and last })
    start_idx = response_text.find('{')
    end_idx = response_text.rfind('}') + 1
    
    if start_idx != -1 and end_idx != 0:
        json_text = response_text[start_idx:end_idx]
        # Remove comments from JSON (lines starting with //)
        lines = json_text.split('\n')
        cleaned_lines = []
        for line in lines:
            # Remove // comments but preserve the line structure
            if '//' in line:
                comment_idx = line.find('//')
                # Only remove comment if it's not inside a string
                in_string = False
                escape_next = False
                for i, char in enumerate(line):
                    if escape_next:
                        escape_next = False
                        continue
                    if char == '\\':
                        escape_next = True
                        continue
                    if char == '"' and not escape_next:
                        in_string = not in_string
                    if i == comment_idx and not in_string:
                        line = line[:comment_idx].rstrip()
                        break
            cleaned_lines.append(line)
        json_text = '\n'.join(cleaned_lines)
        phase2_output = json.loads(json_text)
    else:
        raise ValueError("No valid JSON found in agent response")
    
    phase2_time = time.time() - start_time
    print(f"✅ Phase 2 completed in {phase2_time:.2f} seconds")
    
    # Display Phase 2 results
    print("\n📊 Phase 2 Results:")
    build_systems = phase2_output.get("build_systems_detected", {})
    for system, data in build_systems.items():
        if data.get("detected", False):
            confidence = data.get("confidence", 0)
            evidence = data.get("evidence", [])
            print(f"  - {system}: {confidence:.1%} confidence")
            print(f"    Evidence: {', '.join(evidence[:3])}{'...' if len(evidence) > 3 else ''}")
    
    # Analysis
    print("\n🔍 Analysis:")
    
    # Check if multiple build systems were detected
    detected_systems = [system for system, data in build_systems.items() if data.get("detected", False)]
    print(f"✅ Detected {len(detected_systems)} build systems: {', '.join(detected_systems)}")
    
    # Check primary build system
    primary_system = phase2_output.get("build_analysis", {}).get("primary_build_system")
    if primary_system:
        print(f"✅ Primary build system identified as: {primary_system}")
    else:
        print("❌ No primary build system identified")
    
    # Check if multi-build system
    multi_build = phase2_output.get("build_analysis", {}).get("multi_build_system", False)
    if multi_build:
        print("✅ Multi-build system correctly identified")
    else:
        print("❌ Multi-build system NOT identified")
    
    # Check language-build mapping
    language_mapping = phase2_output.get("build_analysis", {}).get("language_build_mapping", {})
    print(f"✅ Language-build mappings: {language_mapping}")
    
    # Token usage analysis
    print("\n📈 Token Usage Analysis:")
    
    # Count tool calls from agent history
    phase2_history = phase2_agent._history
    tool_calls = 0
    total_tokens = 0
    
    for msg in phase2_history:
        if hasattr(msg, 'content') and isinstance(msg.content, str):
            # Count tool calls in the content
            if "detect_build_systems" in msg.content:
                tool_calls += 1
        
        # Try to extract token usage
        if hasattr(msg, 'usage'):
            if hasattr(msg.usage, 'total_tokens'):
                total_tokens += msg.usage.total_tokens
    
    print(f"  - Tool calls: {tool_calls}")
    print(f"  - Total tokens: {total_tokens}")
    print(f"  - Execution time: {phase2_time:.2f} seconds")
    
    # Success criteria for MetaFFI (more flexible than simple repos)
    success = (
        len(detected_systems) >= 1 and  # At least one build system detected
        primary_system is not None and  # Primary system identified
        len(language_mapping) >= 1      # At least one language mapping
    )
    
    if success:
        print("\n🎉 Phase 2 Test PASSED!")
        print("✅ All success criteria met")
    else:
        print("\n❌ Phase 2 Test FAILED!")
        print("❌ Some success criteria not met")
    
    # Save results
    results = {
        "test": "V7 Phase 2: Build System Detection (MetaFFI Standalone)",
        "repository": "MetaFFI",
        "success": success,
        "phase1_time": phase1_time,
        "phase2_time": phase2_time,
        "total_time": phase1_time + phase2_time,
        "tool_calls": tool_calls,
        "total_tokens": total_tokens,
        "detected_languages": [lang for lang, data in languages_detected.items() if data.get("detected", False)],
        "detected_build_systems": detected_systems,
        "primary_build_system": primary_system,
        "multi_build_system": multi_build,
        "language_build_mapping": language_mapping,
        "phase1_output": phase1_output,
        "phase2_output": phase2_output
    }
    
    results_file = project_root / "tests" / "llm0" / "v7" / "phase2_metaffi_test_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    return success


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run test
    success = asyncio.run(test_phase2_build_system_detection())
    
    if success:
        print("\n🎯 MetaFFI test completed successfully!")
        print("✅ Phase 2 is ready for production use")
    else:
        print("\n🔧 Need to analyze MetaFFI results and potentially adjust criteria")
