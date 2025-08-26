import sys
import pytest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ignore import load_specs, should_skip, explain_skip
from conftest import write_ignore, create_test_files, create_symlink_if_supported


def test_ignore_patterns(repo_tmp):
    """Test basic ignore patterns and allow override."""
    # Arrange
    write_ignore(
        repo_tmp, 
        ignore_lines=["node_modules", "*.cache", ".git", "build"], 
        allow_lines=["build/keepme"]
    )
    
    create_test_files(repo_tmp, [
        "node_modules/package.json",
        "build/output.js",
        "build/keepme/important.js",
        "src/main.py",
        ".git/config",
        "cache.tmp"
    ])
    
    # Act
    ignore_spec, allow_spec, ignore_lines, allow_lines = load_specs(repo_tmp)
    
    # Assert
    assert should_skip("node_modules", repo_tmp, ignore_spec, allow_spec, True) == True
    assert should_skip("build", repo_tmp, ignore_spec, allow_spec, True) == True
    assert should_skip("build/keepme", repo_tmp, ignore_spec, allow_spec, True) == False
    assert should_skip("src", repo_tmp, ignore_spec, allow_spec, True) == False
    assert should_skip(".git", repo_tmp, ignore_spec, allow_spec, True) == True
    
    # Test explain_skip shows exact pattern
    node_modules_skip = explain_skip("node_modules", repo_tmp, ignore_spec, allow_spec, ignore_lines, allow_lines, True)
    assert "matched .spadeignore: 'node_modules'" in node_modules_skip
    
    build_keepme_skip = explain_skip("build/keepme", repo_tmp, ignore_spec, allow_spec, ignore_lines, allow_lines, True)
    assert build_keepme_skip is None  # Not skipped


def test_symlink_policy(repo_tmp):
    """Test symlink policy when skip_symlinks=True."""
    # Arrange
    create_test_files(repo_tmp, ["target_dir/file.txt"])
    
    # Try to create symlink
    symlink_created = create_symlink_if_supported(repo_tmp, "target_dir", "symlink_dir")
    
    if symlink_created:
        # Act
        ignore_spec, allow_spec, ignore_lines, allow_lines = load_specs(repo_tmp)
        
        # Assert
        assert should_skip("symlink_dir", repo_tmp, ignore_spec, allow_spec, True) == True
        symlink_skip = explain_skip("symlink_dir", repo_tmp, ignore_spec, allow_spec, ignore_lines, allow_lines, True)
        assert "symlink target" in symlink_skip
    else:
        # Skip test if symlinks not supported
        pytest.skip("Symlinks not supported on this platform")


def test_allow_override(repo_tmp):
    """Test that allow patterns override ignore patterns."""
    # Arrange
    write_ignore(
        repo_tmp,
        ignore_lines=["*.log", "temp"],
        allow_lines=["important.log", "temp/keep"]
    )
    
    create_test_files(repo_tmp, [
        "app.log",
        "important.log",
        "temp/file.txt",
        "temp/keep/file.txt"
    ])
    
    # Act
    ignore_spec, allow_spec, ignore_lines, allow_lines = load_specs(repo_tmp)
    
    # Assert
    assert should_skip("app.log", repo_tmp, ignore_spec, allow_spec, True) == True
    assert should_skip("important.log", repo_tmp, ignore_spec, allow_spec, True) == False
    assert should_skip("temp", repo_tmp, ignore_spec, allow_spec, True) == True
    assert should_skip("temp/keep", repo_tmp, ignore_spec, allow_spec, True) == False


def test_no_ignore_files(repo_tmp):
    """Test behavior when no ignore files exist."""
    # Act
    ignore_spec, allow_spec, ignore_lines, allow_lines = load_specs(repo_tmp)
    
    # Assert
    assert should_skip("any_file.txt", repo_tmp, ignore_spec, allow_spec, True) == False
    assert explain_skip("any_file.txt", repo_tmp, ignore_spec, allow_spec, ignore_lines, allow_lines, True) is None


def test_complex_patterns(repo_tmp):
    """Test complex ignore patterns."""
    # Arrange
    write_ignore(repo_tmp, ignore_lines=[
        "*.pyc",
        "**/__pycache__",
        "dist",
        "*.egg-info",
        "coverage.xml",
        "*.tmp"
    ])
    
    create_test_files(repo_tmp, [
        "src/__pycache__/module.pyc",
        "dist/build.tar.gz",
        "package.egg-info/metadata.json",
        "coverage.xml",
        "temp.tmp",
        "src/main.py"
    ])
    
    # Act
    ignore_spec, allow_spec, ignore_lines, allow_lines = load_specs(repo_tmp)
    
    # Assert
    assert should_skip("src/__pycache__", repo_tmp, ignore_spec, allow_spec, True) == True
    assert should_skip("dist", repo_tmp, ignore_spec, allow_spec, True) == True
    assert should_skip("package.egg-info", repo_tmp, ignore_spec, allow_spec, True) == True
    assert should_skip("coverage.xml", repo_tmp, ignore_spec, allow_spec, True) == True
    assert should_skip("temp.tmp", repo_tmp, ignore_spec, allow_spec, True) == True
    assert should_skip("src/main.py", repo_tmp, ignore_spec, allow_spec, True) == False
