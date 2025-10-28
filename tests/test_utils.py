"""
Test utilities for deterministic RIG testing.

This module provides helper functions for converting ground truth data
to RIG format and comparing RIGs deterministically.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass

from core.schemas import (
    Component, ComponentType, ExternalPackage, PackageManager,
    TestDefinition, Evidence, Aggregator, Runner,
    RepositoryInfo, BuildSystemInfo
)
from core.rig import RIG

test_repos_root = Path(__file__).parent / "test_repos"

