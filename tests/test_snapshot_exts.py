import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from snapshot import build_snapshot
from models import RunConfig, load_json
from conftest import create_test_files


def test_extension_rules(repo_tmp):
    """Test snapshot extension rules."""
    # Arrange
    create_test_files(repo_tmp, [
        ".env",
        "a.py",
        "noext",
        "file.backup.txt",
        "archive.tar.gz",
        "src/main.py",
        "docs/README.md"
    ])
    
    # Load config
    cfg_path = repo_tmp / ".spade" / "run.json"
    cfg = RunConfig(**json.loads(cfg_path.read_text(encoding="utf-8")))
    
    # Act
    build_snapshot(repo_tmp, cfg)
    
    # Load root dirmeta
    dirmeta_path = repo_tmp / ".spade" / "snapshot" / "." / "dirmeta.json"
    from models import DirMeta
    dirmeta = load_json(dirmeta_path, DirMeta)
    
    # Assert
    ext_histogram = dirmeta.ext_histogram or {}
    
        # Check expected extensions (only files in root directory)
    assert ext_histogram.get(".env") == 1
    assert ext_histogram.get("py") == 1  # Only a.py (src/main.py is in subdirectory)
    assert ext_histogram.get("txt") == 1  # file.backup.txt
    assert ext_histogram.get("gz") == 1   # archive.tar.gz
    # docs/README.md is in subdirectory, not counted in root dirmeta
    
    # Check that "noext" is not included
    assert "noext" not in ext_histogram
    
    # Check counts
    assert dirmeta.counts.files == 5  # Files in root directory only
    assert dirmeta.counts.dirs == 3   # .spade/, src/, and docs/ directories


def test_multi_dot_extensions(repo_tmp):
    """Test multi-dot file extensions."""
    # Arrange
    create_test_files(repo_tmp, [
        "file.backup.txt",
        "archive.tar.gz",
        "config.local.json",
        "data.2023.csv",
        "script.min.js"
    ])
    
    # Load config
    cfg_path = repo_tmp / ".spade" / "run.json"
    cfg = RunConfig(**json.loads(cfg_path.read_text(encoding="utf-8")))
    
    # Act
    build_snapshot(repo_tmp, cfg)
    
    # Load root dirmeta
    dirmeta_path = repo_tmp / ".spade" / "snapshot" / "." / "dirmeta.json"
    from models import DirMeta
    dirmeta = load_json(dirmeta_path, DirMeta)
    
    # Assert
    ext_histogram = dirmeta.ext_histogram or {}
    
    # Should extract the last extension
    assert ext_histogram.get("txt") == 1  # file.backup.txt
    assert ext_histogram.get("gz") == 1   # archive.tar.gz
    assert ext_histogram.get("json") == 1 # config.local.json
    assert ext_histogram.get("csv") == 1  # data.2023.csv
    assert ext_histogram.get("js") == 1   # script.min.js


def test_hidden_files(repo_tmp):
    """Test hidden files and dotfiles."""
    # Arrange
    create_test_files(repo_tmp, [
        ".env",
        ".gitignore",
        ".config.json",
        "normal.py",
        ".hidden_dir/file.txt"
    ])
    
    # Load config
    cfg_path = repo_tmp / ".spade" / "run.json"
    cfg = RunConfig(**json.loads(cfg_path.read_text(encoding="utf-8")))
    
    # Act
    build_snapshot(repo_tmp, cfg)
    
    # Load root dirmeta
    dirmeta_path = repo_tmp / ".spade" / "snapshot" / "." / "dirmeta.json"
    from models import DirMeta
    dirmeta = load_json(dirmeta_path, DirMeta)
    
    # Assert
    ext_histogram = dirmeta.ext_histogram or {}
    
    # Hidden files should be included (only files in root directory)
    assert ext_histogram.get(".env") == 1
    assert ext_histogram.get(".gitignore") == 1  # .gitignore (keeps the dot)
    assert ext_histogram.get("json") == 1       # .config.json
    assert ext_histogram.get("py") == 1         # normal.py
    # .hidden_dir/file.txt is in subdirectory, not counted in root dirmeta


def test_no_extension_files(repo_tmp):
    """Test files without extensions."""
    # Arrange
    create_test_files(repo_tmp, [
        "README",
        "Dockerfile",
        "Makefile",
        "LICENSE",
        "script"
    ])
    
    # Load config
    cfg_path = repo_tmp / ".spade" / "run.json"
    cfg = RunConfig(**json.loads(cfg_path.read_text(encoding="utf-8")))
    
    # Act
    build_snapshot(repo_tmp, cfg)
    
    # Load root dirmeta
    dirmeta_path = repo_tmp / ".spade" / "snapshot" / "." / "dirmeta.json"
    from models import DirMeta
    dirmeta = load_json(dirmeta_path, DirMeta)
    
    # Assert
    ext_histogram = dirmeta.ext_histogram or {}
    counts = dirmeta.counts or {}
    
    # Files without extensions should not appear in ext_histogram
    assert "README" not in ext_histogram
    assert "Dockerfile" not in ext_histogram
    assert "Makefile" not in ext_histogram
    assert "LICENSE" not in ext_histogram
    assert "script" not in ext_histogram
    
    # But they should be counted in total files
    assert dirmeta.counts.files == 5
