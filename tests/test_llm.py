#!/usr/bin/env python3
"""
Test script for SPADE LLM client functionality
Validates that LLM client works correctly with prompts and transport
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from llm import LLMClient, pretty_json
from prompts import load_system, load_user
from dev.dummy_transport import (
    echo_transport_always_invalid,
    echo_transport_valid_response,
    echo_transport_malformed_json
)


def test_prompt_loading():
    """Test prompt loading functionality."""
    print("Testing prompt loading...")
    
    try:
        # Test system prompt loading
        sys_prompt = load_system("phase0_scaffold")
        if "SPADE Phase-0" in sys_prompt and "MISSION" in sys_prompt:
            print("✓ System prompt loaded successfully")
        else:
            print("✗ System prompt content incorrect")
            return False
        
        # Test user prompt loading
        user_prompt = load_user("phase0_scaffold")
        if "{{PHASE0_CONTEXT_JSON}}" in user_prompt:
            print("✓ User prompt loaded successfully")
        else:
            print("✗ User prompt content incorrect")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Prompt loading failed: {e}")
        return False


def test_pretty_json():
    """Test pretty JSON formatting."""
    print("\nTesting pretty JSON formatting...")
    
    test_obj = {
        "repo_root_name": "test-repo",
        "current": {
            "path": ".",
            "depth": 0,
            "counts": {"files": 10, "dirs": 5}
        },
        "siblings": ["src", "docs", "tests"]
    }
    
    formatted = pretty_json(test_obj)
    
    # Check that it's valid JSON
    try:
        parsed = json.loads(formatted)
        if parsed == test_obj:
            print("✓ Pretty JSON formatting works correctly")
            return True
        else:
            print("✗ Pretty JSON formatting changed content")
            return False
    except Exception as e:
        print(f"✗ Pretty JSON formatting produced invalid JSON: {e}")
        return False


def test_context_injection():
    """Test context injection into user prompt."""
    print("\nTesting context injection...")
    
    try:
        user_template = load_user("phase0_scaffold")
        context = {
            "repo_root_name": "test-repo",
            "current": {"path": ".", "depth": 0},
            "siblings": ["src"]
        }
        
        # Test that placeholder is replaced
        if "{{PHASE0_CONTEXT_JSON}}" not in user_template:
            print("✗ User template missing placeholder")
            return False
        
        injected = user_template.replace("{{PHASE0_CONTEXT_JSON}}", pretty_json(context))
        
        if "{{PHASE0_CONTEXT_JSON}}" in injected:
            print("✗ Placeholder not replaced")
            return False
        
        if "test-repo" in injected and "src" in injected:
            print("✓ Context injection works correctly")
            return True
        else:
            print("✗ Context not properly injected")
            return False
            
    except Exception as e:
        print(f"✗ Context injection failed: {e}")
        return False


def test_valid_response():
    """Test LLM client with valid response."""
    print("\nTesting LLM client with valid response...")
    
    client = LLMClient(echo_transport_valid_response)
    context = {
        "repo_root_name": "test-repo",
        "current": {"path": ".", "depth": 0},
        "siblings": ["src"]
    }
    
    response, raw = client.call_phase0(context)
    
    if response is not None:
        print("✓ Valid response parsed successfully")
        
        # Check that response has expected structure
        if (hasattr(response, 'inferred') and 
            hasattr(response, 'nav') and 
            hasattr(response, 'open_questions_ranked')):
            print("✓ Response has correct structure")
            return True
        else:
            print("✗ Response missing expected attributes")
            return False
    else:
        print("✗ Valid response not parsed")
        return False


def test_invalid_response():
    """Test LLM client with invalid response."""
    print("\nTesting LLM client with invalid response...")
    
    client = LLMClient(echo_transport_always_invalid)
    context = {
        "repo_root_name": "test-repo",
        "current": {"path": ".", "depth": 0},
        "siblings": ["src"]
    }
    
    response, raw = client.call_phase0(context)
    
    if response is None:
        print("✓ Invalid response correctly handled")
        return True
    else:
        print("✗ Invalid response incorrectly parsed")
        return False


def test_repair_attempt():
    """Test LLM client repair attempt with malformed JSON."""
    print("\nTesting LLM client repair attempt...")
    
    client = LLMClient(echo_transport_malformed_json)
    context = {
        "repo_root_name": "test-repo",
        "current": {"path": ".", "depth": 0},
        "siblings": ["src"]
    }
    
    response, raw = client.call_phase0(context)
    
    # The malformed transport should trigger a repair attempt
    # Since our dummy transport doesn't actually repair, we expect None
    if response is None:
        print("✓ Repair attempt handled correctly")
        return True
    else:
        print("✗ Repair attempt incorrectly succeeded")
        return False


def test_transport_error():
    """Test LLM client with transport error."""
    print("\nTesting LLM client with transport error...")
    
    def failing_transport(messages):
        raise Exception("Transport failed")
    
    client = LLMClient(failing_transport)
    context = {
        "repo_root_name": "test-repo",
        "current": {"path": ".", "depth": 0},
        "siblings": ["src"]
    }
    
    response, raw = client.call_phase0(context)
    
    if response is None and raw == "":
        print("✓ Transport error handled correctly")
        return True
    else:
        print("✗ Transport error not handled correctly")
        return False


def test_acceptance_criteria():
    """Test the exact acceptance criteria."""
    print("\nTesting acceptance criteria...")
    
    # Test 1: Can instantiate LLMClient with dummy transport
    try:
        client = LLMClient(echo_transport_valid_response)
        print("✓ LLMClient instantiation works")
    except Exception as e:
        print(f"✗ LLMClient instantiation failed: {e}")
        return False
    
    # Test 2: Valid schema JSON returns (LLMResponse, raw)
    context = {"repo_root_name": "test", "current": {"path": "."}, "siblings": []}
    response, raw = client.call_phase0(context)
    
    if response is not None and isinstance(raw, str):
        print("✓ Valid schema JSON returns (LLMResponse, raw)")
    else:
        print("✗ Valid schema JSON not handled correctly")
        return False
    
    # Test 3: Invalid response shows repair attempt and returns (None, raw2)
    client_invalid = LLMClient(echo_transport_always_invalid)
    response2, raw2 = client_invalid.call_phase0(context)
    
    if response2 is None and isinstance(raw2, str):
        print("✓ Invalid response shows repair attempt and returns (None, raw2)")
    else:
        print("✗ Invalid response not handled correctly")
        return False
    
    print("✓ All acceptance criteria met")
    return True


def main():
    """Run all tests."""
    print("SPADE LLM Client Test Suite")
    print("=" * 50)
    
    try:
        success1 = test_prompt_loading()
        success2 = test_pretty_json()
        success3 = test_context_injection()
        success4 = test_valid_response()
        success5 = test_invalid_response()
        success6 = test_repair_attempt()
        success7 = test_transport_error()
        success8 = test_acceptance_criteria()
        
        if success1 and success2 and success3 and success4 and success5 and success6 and success7 and success8:
            print("\n" + "=" * 50)
            print("✓ All tests passed! LLM client working correctly.")
        else:
            print("\n" + "=" * 50)
            print("✗ Some tests failed.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
