"""
Test script for LLM-based RIG Generator Phase 1: Repository Discovery

This script tests the Repository Discovery Agent with a simple CMake project.
"""

import os
import sys
import logging
from pathlib import Path
import json

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from llm0_rig_generator import LLMRIGGenerator


def test_discovery_agent():
    """Test the Repository Discovery Agent."""
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    print("🧪 Testing LLM-based Repository Discovery Agent")
    print("=" * 60)
    
    # Check for OpenAI API key
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("   Please set your OpenAI API key to test the discovery agent")
        return False
    
    # Use the permanent test project
    test_project = Path(__file__).parent / "test_repos" / "cmake_hello_world"
    
    if not test_project.exists():
        print(f"❌ Test project not found at: {test_project}")
        print("   Please ensure the test_repos/cmake_hello_world directory exists")
        return False
    
    print(f"📁 Using test project at: {test_project}")
    print(f"📄 Project structure:")
    for item in test_project.rglob("*"):
        if item.is_file():
            print(f"   {item.relative_to(test_project)}")
    
    try:
        # Initialize the generator
        print(f"\n🔧 Initializing LLM RIG Generator...")
        generator = LLMRIGGenerator(test_project, openai_key)
        
        # Run discovery
        print(f"\n🔍 Running repository discovery...")
        discovery_result = generator.discover_repository()
        
        # Check results
        if discovery_result.success:
            print("✅ Discovery successful!")
            print(f"\n📊 Repository Info:")
            print(json.dumps(discovery_result.repository_info, indent=2))
            print(f"\n📋 Evidence Catalog:")
            print(json.dumps(discovery_result.evidence_catalog, indent=2))
            return True
        else:
            print("❌ Discovery failed!")
            for error in discovery_result.errors:
                print(f"   Error: {error}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during discovery: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_with_existing_repository():
    """Test with an existing repository (if available)."""
    
    # Check if we're in the spade repository
    current_dir = Path.cwd()
    if (current_dir / "rig.py").exists():
        print(f"\n🏠 Testing with current repository: {current_dir}")
        
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            print("❌ OPENAI_API_KEY environment variable not set")
            return False
        
        try:
            generator = LLMRIGGenerator(current_dir, openai_key)
            discovery_result = generator.discover_repository()
            
            if discovery_result.success:
                print("✅ Discovery successful!")
                print(f"\n📊 Repository Info:")
                print(json.dumps(discovery_result.repository_info, indent=2))
                print(f"\n🔢 Token Usage:")
                print(f"   Input tokens: {discovery_result.token_usage['input_tokens']}")
                print(f"   Output tokens: {discovery_result.token_usage['output_tokens']}")
                print(f"   Total tokens: {discovery_result.token_usage['total_tokens']}")
                return True
            else:
                print("❌ Discovery failed!")
                for error in discovery_result.errors:
                    print(f"   Error: {error}")
                return False
                
        except Exception as e:
            print(f"❌ Exception during discovery: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print(f"\n📝 No existing repository found for testing")
        return True


def main():
    """Main test function."""
    
    print("🚀 LLM-based RIG Generator - Phase 1 Testing")
    print("=" * 60)
    
    # Test: Simple CMake project (cmake_hello_world)
    success = test_discovery_agent()
    
    # Summary
    print(f"\n📋 Test Summary:")
    print(f"   CMake Hello World Project: {'✅ PASS' if success else '❌ FAIL'}")
    
    if success:
        print(f"\n🎉 Test passed! Phase 1 implementation is working.")
        return 0
    else:
        print(f"\n⚠️  Test failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
