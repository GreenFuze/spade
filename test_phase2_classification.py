#!/usr/bin/env python3
"""
Test script for Phase 2: Component Classification Agent
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add the current directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent))

from llm0_rig_generator import LLMRIGGenerator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_phase2_classification():
    """Test Phase 2: Component Classification Agent."""
    
    print("🚀 LLM-based RIG Generator - Phase 2 Testing")
    print("=" * 60)
    print("🧪 Testing Component Classification Agent")
    print("=" * 60)
    
    # Use the permanent test repository
    test_project = Path(__file__).parent / "test_repos" / "cmake_hello_world"
    
    if not test_project.exists():
        print(f"❌ Test project not found at: {test_project}")
        return False
    
    print(f"📁 Using test project at: {test_project}")
    
    # Check for required environment variables
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        return False
    
    try:
        print("🔧 Initializing LLM RIG Generator...")
        generator = LLMRIGGenerator(test_project, openai_key)
        
        print("🔍 Running Phase 1: Repository Discovery...")
        discovery_result = generator.discover_repository()
        
        if not discovery_result.success:
            print("❌ Phase 1 failed!")
            for error in discovery_result.errors:
                print(f"   Error: {error}")
            return False
        
        print("✅ Phase 1: Repository Discovery completed")
        print(f"\n🔢 Phase 1 Token Usage:")
        print(f"   Input tokens: {discovery_result.token_usage['input_tokens']}")
        print(f"   Output tokens: {discovery_result.token_usage['output_tokens']}")
        print(f"   Total tokens: {discovery_result.token_usage['total_tokens']}")
        
        print("\n🔍 Running Phase 2: Component Classification...")
        classification_result = generator.classify_components(discovery_result)
        
        if classification_result["success"]:
            print("✅ Phase 2: Component Classification completed")
            print(f"\n🔢 Phase 2 Token Usage:")
            print(f"   Input tokens: {classification_result['token_usage']['input_tokens']}")
            print(f"   Output tokens: {classification_result['token_usage']['output_tokens']}")
            print(f"   Total tokens: {classification_result['token_usage']['total_tokens']}")
            
            print(f"\n📊 Classified Components:")
            print(json.dumps(classification_result["components"], indent=2))
            
            return True
        else:
            print("❌ Phase 2 failed!")
            for error in classification_result["errors"]:
                print(f"   Error: {error}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    
    success = test_phase2_classification()
    
    # Summary
    print(f"\n📋 Test Summary:")
    print(f"   Phase 2 Component Classification: {'✅ PASS' if success else '❌ FAIL'}")
    
    if success:
        print(f"\n🎉 Test passed! Phase 2 implementation is working.")
        return 0
    else:
        print(f"\n⚠️  Test failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
