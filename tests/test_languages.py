#!/usr/bin/env python3
"""
Test script for SPADE language mapping functionality
Validates that extension→language mapping and aggregation works correctly
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from languages import SEED_EXT2LANG, load_learned, active_map, aggregate_languages
from workspace import Workspace


def test_seed_mapping():
    """Test that seed mapping is properly defined."""
    print("Testing seed mapping...")
    
    # Check that we have a reasonable number of mappings
    if len(SEED_EXT2LANG) < 20:
        print(f"✗ Too few seed mappings: {len(SEED_EXT2LANG)}")
        return False
    
    # Check some common mappings
    expected_mappings = {
        "py": "python",
        "js": "javascript",
        "ts": "typescript",
        "cpp": "c++",
        "java": "java",
        "go": "go",
        "rs": "rust"
    }
    
    for ext, expected_lang in expected_mappings.items():
        if SEED_EXT2LANG.get(ext) != expected_lang:
            print(f"✗ Expected {ext} → {expected_lang}, got {SEED_EXT2LANG.get(ext)}")
            return False
    
    print(f"✓ {len(SEED_EXT2LANG)} seed mappings loaded correctly")
    return True


def test_active_map():
    """Test active_map function with different configurations."""
    print("\nTesting active_map...")
    
    repo_root = Path("fakeapp")
    config = Workspace.load_config(repo_root)
    
    # Test with learned languages disabled
    config.use_learned_languages = False
    mapping = active_map(config, repo_root)
    
    if len(mapping) == len(SEED_EXT2LANG):
        print("✓ Active map returns seed-only when learned languages disabled")
    else:
        print(f"✗ Expected {len(SEED_EXT2LANG)} mappings, got {len(mapping)}")
        return False
    
    # Test with learned languages enabled (but no file exists)
    config.use_learned_languages = True
    mapping = active_map(config, repo_root)
    
    if len(mapping) == len(SEED_EXT2LANG):
        print("✓ Active map returns seed-only when learned file doesn't exist")
    else:
        print(f"✗ Expected {len(SEED_EXT2LANG)} mappings, got {len(mapping)}")
        return False
    
    return True


def test_learned_mapping():
    """Test learned mapping functionality."""
    print("\nTesting learned mapping...")
    
    repo_root = Path("fakeapp")
    
    # Test loading when file doesn't exist
    learned = load_learned(repo_root)
    if learned == {}:
        print("✓ Empty learned mapping when file doesn't exist")
    else:
        print(f"✗ Expected empty dict, got: {learned}")
        return False
    
    # Create a test learned mapping file
    learned_mappings = [
        {"ext": "custom", "language": "custom_lang"},
        {"ext": "special", "language": "special_lang"},
        {"ext": ".env", "language": "environment"}  # Test dotfile mapping
    ]
    
    learned_path = repo_root / ".spade" / "languages.learned.json"
    learned_path.parent.mkdir(exist_ok=True)
    with open(learned_path, 'w') as f:
        json.dump(learned_mappings, f)
    
    # Test loading the file
    loaded = load_learned(repo_root)
    expected = {"custom": "custom_lang", "special": "special_lang", "env": "environment"}
    
    if loaded == expected:
        print("✓ Learned mapping loaded correctly")
    else:
        print(f"✗ Expected {expected}, got {loaded}")
        return False
    
    # Test active_map with learned languages enabled
    config = Workspace.load_config(repo_root)
    config.use_learned_languages = True
    mapping = active_map(config, repo_root)
    
    # Check that learned mappings are included
    for ext, lang in expected.items():
        if mapping.get(ext) != lang:
            print(f"✗ Expected {ext} → {lang}, got {mapping.get(ext)}")
            return False
    
    print("✓ Active map includes learned mappings when enabled")
    
    # Clean up
    learned_path.unlink()
    
    return True


def test_aggregate_languages():
    """Test language aggregation functionality."""
    print("\nTesting aggregate_languages...")
    
    # Test case from acceptance criteria
    ext_histogram = {"py": 10, "ts": 3, "md": 7, ".env": 2}
    ext2lang = {"py": "python", "ts": "typescript"}  # Only include the mappings that should be used
    
    result = aggregate_languages(ext_histogram, ext2lang)
    expected = [("python", 10), ("typescript", 3)]
    
    if result == expected:
        print("✓ Language aggregation works correctly")
    else:
        print(f"✗ Expected {expected}, got {result}")
        return False
    
    # Test with more complex case
    ext_histogram2 = {"py": 5, "js": 3, "ts": 8, "cpp": 2, "h": 1, ".gitignore": 1}
    ext2lang2 = {"py": "python", "js": "javascript", "ts": "typescript", "cpp": "c++", "h": "c"}
    
    result2 = aggregate_languages(ext_histogram2, ext2lang2)
    expected2 = [("typescript", 8), ("python", 5), ("javascript", 3), ("c++", 2), ("c", 1)]
    
    if result2 == expected2:
        print("✓ Complex language aggregation works correctly")
    else:
        print(f"✗ Expected {expected2}, got {result2}")
        return False
    
    # Test with empty histogram
    result3 = aggregate_languages({}, ext2lang)
    if result3 == []:
        print("✓ Empty histogram handled correctly")
    else:
        print(f"✗ Expected empty list, got {result3}")
        return False
    
    # Test with unknown extensions
    ext_histogram4 = {"py": 3, "unknown": 5, "ts": 2}
    result4 = aggregate_languages(ext_histogram4, ext2lang)
    expected4 = [("python", 3), ("typescript", 2)]
    
    if result4 == expected4:
        print("✓ Unknown extensions ignored correctly")
    else:
        print(f"✗ Expected {expected4}, got {result4}")
        return False
    
    return True


def test_edge_cases():
    """Test edge cases and error handling."""
    print("\nTesting edge cases...")
    
    # Test with invalid count types
    ext_histogram = {"py": "invalid", "ts": 3}
    ext2lang = {"py": "python", "ts": "typescript"}
    
    result = aggregate_languages(ext_histogram, ext2lang)
    expected = [("typescript", 3)]
    
    if result == expected:
        print("✓ Invalid count types handled correctly")
    else:
        print(f"✗ Expected {expected}, got {result}")
        return False
    
    # Test with zero and negative counts
    ext_histogram2 = {"py": 0, "ts": -1, "js": 3}
    ext2lang2 = {"py": "python", "ts": "typescript", "js": "javascript"}
    
    result2 = aggregate_languages(ext_histogram2, ext2lang2)
    expected2 = [("javascript", 3)]
    
    if result2 == expected2:
        print("✓ Zero and negative counts handled correctly")
    else:
        print(f"✗ Expected {expected2}, got {result2}")
        return False
    
    # Test with dotfile that has explicit mapping
    ext_histogram3 = {".env": 5, "py": 3}
    ext2lang3 = {".env": "environment", "py": "python"}
    
    result3 = aggregate_languages(ext_histogram3, ext2lang3)
    expected3 = [("environment", 5), ("python", 3)]
    
    if result3 == expected3:
        print("✓ Dotfile with explicit mapping handled correctly")
    else:
        print(f"✗ Expected {expected3}, got {result3}")
        return False
    
    return True


def main():
    """Run all tests."""
    print("SPADE Language Mapping Test Suite")
    print("=" * 50)
    
    try:
        success1 = test_seed_mapping()
        success2 = test_active_map()
        success3 = test_learned_mapping()
        success4 = test_aggregate_languages()
        success5 = test_edge_cases()
        
        if success1 and success2 and success3 and success4 and success5:
            print("\n" + "=" * 50)
            print("✓ All tests passed! Language mapping working correctly.")
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
