from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from cmake_entrypoint import CMakeEntrypoint
from rig import RIG
from schemas import ComponentType
from pydantic import BaseModel, ValidationError


# =========================
# Pydantic Models for LLM Answer Validation
# =========================

class ArtifactInfo(BaseModel):
    name: str
    kind: str
    artifact: str
    output_dir: str
    depends_on: List[str] = []
    externals: List[str] = []
    defining_files: List[str] = []

class XLLRRuntime(BaseModel):
    name: str
    artifact: str
    depends_on: List[str] = []
    externals: List[str] = []
    defining_files: List[str] = []

class ExecutableInfo(BaseModel):
    name: str
    artifact: str
    output_dir: str
    defining_files: List[str] = []

class IDLPlugin(BaseModel):
    name: str
    artifact: str
    defining_files: List[str] = []

class GoCompiler(BaseModel):
    name: str
    artifact: str
    defining_files: List[str] = []

class NativeComponent(BaseModel):
    name: str
    kind: str
    artifact: str

class VMArtifact(BaseModel):
    name: str
    artifact: str
    output_dir: str
    defining_files: List[str] = []

class CDTSTest(BaseModel):
    name: str
    artifact: str
    defining_files: List[str] = []

class BoostInfo(BaseModel):
    versions: List[str] = []
    libraries: List[str] = []
    declared_in: List[str] = []

class TestToComponent(BaseModel):
    test: str
    components: List[str] = []

class GoAPITest(BaseModel):
    dependencies: List[str] = []
    externals: List[str] = []

class OpenJDKJNIBridge(BaseModel):
    depends_on: List[str] = []
    artifact: str
    defining_files: List[str] = []

class JARInfo(BaseModel):
    name: str
    artifact: str
    output_dir: str
    defining_files: List[str] = []

class GoRuntimeBinary(BaseModel):
    name: str
    artifact: str
    defining_files: List[str] = []

# Question Answer Models
class Q01Answer(BaseModel):
    artifacts: List[ArtifactInfo]
    
    def compare_answers(self, other: 'Q01Answer', calculator) -> Dict[str, Any]:
        """Compare Q01 answers with field-by-field scoring."""
        found_facts = []
        correct = 0
        incorrect = 0
        
        # Compare artifacts list
        result = calculator._compare_lists([item.model_dump() for item in self.artifacts], [item.model_dump() for item in other.artifacts], "artifacts")
        found_facts.extend(result["found_facts"])
        correct += result["correct"]
        incorrect += result["incorrect"]
        
        return {
            "found_facts": found_facts,
            "correct": correct,
            "incorrect": incorrect
        }

class Q02Answer(BaseModel):
    xllr_runtimes: List[XLLRRuntime] = []
    
    def compare_answers(self, other: 'Q02Answer', calculator) -> Dict[str, Any]:
        """Compare Q02 answers with field-by-field scoring."""
        found_facts = []
        correct = 0
        incorrect = 0
        
        # Compare xllr_runtimes list
        result = calculator._compare_lists([item.model_dump() for item in self.xllr_runtimes], [item.model_dump() for item in other.xllr_runtimes], "xllr_runtimes")
        found_facts.extend(result["found_facts"])
        correct += result["correct"]
        incorrect += result["incorrect"]
        
        return {
            "found_facts": found_facts,
            "correct": correct,
            "incorrect": incorrect
        }

class Q03Answer(BaseModel):
    executables: List[ExecutableInfo] = []
    
    def compare_answers(self, other: 'Q03Answer', calculator) -> Dict[str, Any]:
        """Compare Q03 answers with field-by-field scoring."""
        found_facts = []
        correct = 0
        incorrect = 0
        
        result = calculator._compare_lists([item.model_dump() for item in self.executables], [item.model_dump() for item in other.executables], "executables")
        found_facts.extend(result["found_facts"])
        correct += result["correct"]
        incorrect += result["incorrect"]
        
        return {
            "found_facts": found_facts,
            "correct": correct,
            "incorrect": incorrect
        }

class Q04Answer(BaseModel):
    idl_plugins: List[IDLPlugin] = []
    
    def compare_answers(self, other: 'Q04Answer', calculator) -> Dict[str, Any]:
        """Compare Q04 answers with field-by-field scoring."""
        found_facts = []
        correct = 0
        incorrect = 0
        
        result = calculator._compare_lists([item.model_dump() for item in self.idl_plugins], [item.model_dump() for item in other.idl_plugins], "idl_plugins")
        found_facts.extend(result["found_facts"])
        correct += result["correct"]
        incorrect += result["incorrect"]
        
        return {
            "found_facts": found_facts,
            "correct": correct,
            "incorrect": incorrect
        }

class Q05Answer(BaseModel):
    go_compilers: List[GoCompiler] = []
    
    def compare_answers(self, other: 'Q05Answer', calculator) -> Dict[str, Any]:
        """Compare Q05 answers with field-by-field scoring."""
        found_facts = []
        correct = 0
        incorrect = 0
        
        result = calculator._compare_lists([item.model_dump() for item in self.go_compilers], [item.model_dump() for item in other.go_compilers], "go_compilers")
        found_facts.extend(result["found_facts"])
        correct += result["correct"]
        incorrect += result["incorrect"]
        
        return {
            "found_facts": found_facts,
            "correct": correct,
            "incorrect": incorrect
        }

class Q06Answer(BaseModel):
    native: List[NativeComponent] = []
    
    def compare_answers(self, other: 'Q06Answer', calculator) -> Dict[str, Any]:
        """Compare Q06 answers with field-by-field scoring."""
        found_facts = []
        correct = 0
        incorrect = 0
        
        result = calculator._compare_lists([item.model_dump() for item in self.native], [item.model_dump() for item in other.native], "native")
        found_facts.extend(result["found_facts"])
        correct += result["correct"]
        incorrect += result["incorrect"]
        
        return {
            "found_facts": found_facts,
            "correct": correct,
            "incorrect": incorrect
        }

class Q07Answer(BaseModel):
    vm_artifacts: List[VMArtifact] = []
    
    def compare_answers(self, other: 'Q07Answer', calculator) -> Dict[str, Any]:
        """Compare Q07 answers with field-by-field scoring."""
        found_facts = []
        correct = 0
        incorrect = 0
        
        result = calculator._compare_lists([item.model_dump() for item in self.vm_artifacts], [item.model_dump() for item in other.vm_artifacts], "vm_artifacts")
        found_facts.extend(result["found_facts"])
        correct += result["correct"]
        incorrect += result["incorrect"]
        
        return {
            "found_facts": found_facts,
            "correct": correct,
            "incorrect": incorrect
        }

class Q08Answer(BaseModel):
    cdts_tests: List[CDTSTest] = []
    
    def compare_answers(self, other: 'Q08Answer', calculator) -> Dict[str, Any]:
        """Compare Q08 answers with field-by-field scoring."""
        found_facts = []
        correct = 0
        incorrect = 0
        
        result = calculator._compare_lists([item.model_dump() for item in self.cdts_tests], [item.model_dump() for item in other.cdts_tests], "cdts_tests")
        found_facts.extend(result["found_facts"])
        correct += result["correct"]
        incorrect += result["incorrect"]
        
        return {
            "found_facts": found_facts,
            "correct": correct,
            "incorrect": incorrect
        }

class Q09Answer(BaseModel):
    boost: BoostInfo
    
    def compare_answers(self, other: 'Q09Answer', calculator) -> Dict[str, Any]:
        """Compare Q09 answers with field-by-field scoring."""
        found_facts = []
        correct = 0
        incorrect = 0
        
        result = calculator._compare_objects(self.boost.model_dump(), other.boost.model_dump(), "boost")
        found_facts.extend(result["found_facts"])
        correct += result["correct"]
        incorrect += result["incorrect"]
        
        return {
            "found_facts": found_facts,
            "correct": correct,
            "incorrect": incorrect
        }

class Q10Answer(BaseModel):
    test_to_components: List[TestToComponent] = []
    
    def compare_answers(self, other: 'Q10Answer', calculator) -> Dict[str, Any]:
        """Compare Q10 answers with field-by-field scoring."""
        found_facts = []
        correct = 0
        incorrect = 0
        
        result = calculator._compare_lists([item.model_dump() for item in self.test_to_components], [item.model_dump() for item in other.test_to_components], "test_to_components")
        found_facts.extend(result["found_facts"])
        correct += result["correct"]
        incorrect += result["incorrect"]
        
        return {
            "found_facts": found_facts,
            "correct": correct,
            "incorrect": incorrect
        }

class Q11Answer(BaseModel):
    go_api_test: GoAPITest
    
    def compare_answers(self, other: 'Q11Answer', calculator) -> Dict[str, Any]:
        """Compare Q11 answers with field-by-field scoring."""
        found_facts = []
        correct = 0
        incorrect = 0
        
        result = calculator._compare_objects(self.go_api_test.model_dump(), other.go_api_test.model_dump(), "go_api_test")
        found_facts.extend(result["found_facts"])
        correct += result["correct"]
        incorrect += result["incorrect"]
        
        return {
            "found_facts": found_facts,
            "correct": correct,
            "incorrect": incorrect
        }

class Q12Answer(BaseModel):
    openjdk_jni_bridge: OpenJDKJNIBridge
    
    def compare_answers(self, other: 'Q12Answer', calculator) -> Dict[str, Any]:
        """Compare Q12 answers with field-by-field scoring."""
        found_facts = []
        correct = 0
        incorrect = 0
        
        result = calculator._compare_objects(self.openjdk_jni_bridge.model_dump(), other.openjdk_jni_bridge.model_dump(), "openjdk_jni_bridge")
        found_facts.extend(result["found_facts"])
        correct += result["correct"]
        incorrect += result["incorrect"]
        
        return {
            "found_facts": found_facts,
            "correct": correct,
            "incorrect": incorrect
        }

class Q13Answer(BaseModel):
    jars: List[JARInfo] = []
    
    def compare_answers(self, other: 'Q13Answer', calculator) -> Dict[str, Any]:
        """Compare Q13 answers with field-by-field scoring."""
        found_facts = []
        correct = 0
        incorrect = 0
        
        result = calculator._compare_lists([item.model_dump() for item in self.jars], [item.model_dump() for item in other.jars], "jars")
        found_facts.extend(result["found_facts"])
        correct += result["correct"]
        incorrect += result["incorrect"]
        
        return {
            "found_facts": found_facts,
            "correct": correct,
            "incorrect": incorrect
        }

class Q14Answer(BaseModel):
    go_runtime_binaries: List[GoRuntimeBinary] = []
    
    def compare_answers(self, other: 'Q14Answer', calculator) -> Dict[str, Any]:
        """Compare Q14 answers with field-by-field scoring."""
        found_facts = []
        correct = 0
        incorrect = 0
        
        result = calculator._compare_lists([item.model_dump() for item in self.go_runtime_binaries], [item.model_dump() for item in other.go_runtime_binaries], "go_runtime_binaries")
        found_facts.extend(result["found_facts"])
        correct += result["correct"]
        incorrect += result["incorrect"]
        
        return {
            "found_facts": found_facts,
            "correct": correct,
            "incorrect": incorrect
        }


# =========================
# Scoring and Results Models
# =========================

class FactLabel(Enum):
    CORRECT = "correct"
    INCORRECT = "incorrect"

@dataclass
class FoundFact:
    claim: str
    label: FactLabel
    raw: Any
    expected: Any = None

@dataclass
class PerQuestionScore:
    question_id: str
    found_facts: List[FoundFact]
    num_correct: int
    num_incorrect: int
    expected_fact_count: int
    score: float
    normalized_score: float
    percentage: float

@dataclass
class ScoreTotals:
    correct: int
    incorrect: int
    expected_fact_count: int
    score: float
    normalized_score: float
    percentage: float
    accuracy: float

@dataclass
class Scores:
    per_question: Dict[str, PerQuestionScore]
    totals: ScoreTotals
    skipped_questions: List[str]


# =========================
# Ground Truth Generation
# =========================

def generate_results_from_rig(rig: RIG) -> Dict[str, Any]:
    """Generate ground truth results from RIG data, formatted exactly like agent responses."""
    
    def norm_text(s: str) -> str:
        return s.replace("\\", "/").strip().lower()
    
    def basename(p: str) -> str:
        return Path(p).name.lower()
    
    results = {}

    # Build set of test executable component IDs
    test_exec_ids = {t.test_executable_component.id for t in rig._tests
                     if t.test_executable_component and isinstance(t.test_executable_component, Component)}

    # Q01: All built artifacts (excluding test executables)
    artifacts = []
    for c in rig._components:
        if c.output_path and c.id not in test_exec_ids:  # Exclude test executables
            artifact_info = {
                "name": c.name,
                "kind": c.type.value if hasattr(c.type, 'value') else str(c.type),
                "artifact": basename(str(c.output_path)),
                "output_dir": str(c.output_path.parent) if c.output_path.parent else "",
                "depends_on": [dep.name for dep in c.depends_on],
                "externals": [ext.package_manager.package_name for ext in c._external_packages if ext.package_manager and ext.package_manager.package_name],
                "defining_files": [str(f.split('#')[0]) for f in c._evidence.call_stack[:2]] if c._evidence and c._evidence.call_stack else []
            }
            artifacts.append(artifact_info)
    results["Q01"] = {"artifacts": artifacts}
    
    # Q02: XLLR runtime plugins
    xllr_runtimes = []
    for c in rig._components:
        if c.type == ComponentType.SHARED_LIBRARY and "xllr" in c.name.lower():
            xllr_info = {
                "name": c.name,
                "artifact": basename(str(c.output_path)) if c.output_path else "",
                "depends_on": [dep.name for dep in c.depends_on],
                "externals": [ext.package_manager.package_name for ext in c._external_packages if ext.package_manager and ext.package_manager.package_name],
                "defining_files": [str(f.split('#')[0]) for f in c._evidence.call_stack[:2]] if c._evidence and c._evidence.call_stack else []
            }
            xllr_runtimes.append(xllr_info)
    results["Q02"] = {"xllr_runtimes": xllr_runtimes}
    
    # Q03: CLI executables
    executables = []
    for c in rig._components:
        if c.type == ComponentType.EXECUTABLE:
            exec_info = {
                "name": c.name,
                "artifact": basename(str(c.output_path)) if c.output_path else "",
                "output_dir": str(c.output_path.parent) if c.output_path and c.output_path.parent else "",
                "defining_files": [str(f.split('#')[0]) for f in c._evidence.call_stack[:2]] if c._evidence and c._evidence.call_stack else []
            }
            executables.append(exec_info)
    results["Q03"] = {"executables": executables}
    
    # Q04: IDL plugins
    idl_plugins = []
    for c in rig._components:
        if c.type == ComponentType.SHARED_LIBRARY and "idl" in c.name.lower():
            idl_info = {
                "name": c.name,
                "artifact": basename(str(c.output_path)) if c.output_path else "",
                "defining_files": [str(f.split('#')[0]) for f in c._evidence.call_stack[:2]] if c._evidence and c._evidence.call_stack else []
            }
            idl_plugins.append(idl_info)
    results["Q04"] = {"idl_plugins": idl_plugins}
    
    # Q05: Go compilers
    go_compilers = []
    for c in rig._components:
        if c.type == ComponentType.SHARED_LIBRARY and "compiler" in c.name.lower():
            compiler_info = {
                "name": c.name,
                "artifact": basename(str(c.output_path)) if c.output_path else "",
                "defining_files": [str(f.split('#')[0]) for f in c._evidence.call_stack[:2]] if c._evidence and c._evidence.call_stack else []
            }
            go_compilers.append(compiler_info)
    results["Q05"] = {"go_compilers": go_compilers}
    
    # Q06: Native components
    native = []
    for c in rig._components:
        if c.type in [ComponentType.EXECUTABLE, ComponentType.SHARED_LIBRARY]:
            native_info = {
                "name": c.name,
                "kind": c.type.value if hasattr(c.type, 'value') else str(c.type),
                "artifact": basename(str(c.output_path)) if c.output_path else ""
            }
            native.append(native_info)
    results["Q06"] = {"native": native}
    
    # Q07: VM/JAR artifacts
    vm_artifacts = []
    for c in rig._components:
        if c.type == ComponentType.VM or (c.output_path and str(c.output_path).lower().endswith('.jar')):
            vm_info = {
                "name": c.name,
                "artifact": basename(str(c.output_path)) if c.output_path else "",
                "output_dir": str(c.output_path.parent) if c.output_path and c.output_path.parent else "",
                "defining_files": [str(f.split('#')[0]) for f in c._evidence.call_stack[:2]] if c._evidence and c._evidence.call_stack else []
            }
            vm_artifacts.append(vm_info)
    results["Q07"] = {"vm_artifacts": vm_artifacts}
    
    # Q08: CDTS tests
    cdts_tests = []
    for t in rig._tests:
        if "cdts" in t.name.lower():
            if t.test_executable and t.test_executable.output_path and t._evidence.call_stack:
                # Remove line numbers and deduplicate
                defining_files = []
                seen_files = set()
                for f in t._evidence.call_stack:
                    file_path = str(f).split('#')[0]  # Remove line numbers
                    if file_path not in seen_files:
                        defining_files.append(file_path)
                        seen_files.add(file_path)
                
                test_info = {
                    "name": t.name,
                    "artifact": basename(str(t.test_executable.output_path)),
                    "defining_files": defining_files
                }
                cdts_tests.append(test_info)
    results["Q08"] = {"cdts_tests": cdts_tests}
    
    # Q09: Boost information
    boost_libraries = set()
    boost_versions = set()
    declared_in = set()
    
    for c in rig._components:
        for ext in c._external_packages:
            if ext.package_manager and "boost" in ext.package_manager.package_name.lower():
                boost_libraries.add(ext.package_manager.package_name)
                # Add the CMake files where this component is defined
                if c._evidence and c._evidence.call_stack:
                    for f in c._evidence.call_stack:
                        file_path = str(f).split('#')[0]  # Remove line numbers
                        declared_in.add(file_path)
    
    # Extract version from library names with robust regex
    import re
    for lib in boost_libraries:
        version_match = re.search(r'(\d+)_(\d+)', lib)
        if version_match:
            major, minor = version_match.groups()
            boost_versions.add(f"{major}.{minor}")
    
    results["Q09"] = {
        "boost": {
            "versions": list(boost_versions),
            "libraries": list(boost_libraries),
            "declared_in": list(declared_in)
        }
    }
    
    # Q10: Test to components mapping
    test_to_components = []
    for t in rig._tests:
        if t._evidence.call_stack:
            components = []
            # Find components that this test depends on - precise matching only
            for c in rig._components:
                # Only match if component name exactly matches test name or is in call stack
                if c.name == t.name or (t._evidence.call_stack and c.name in t._evidence.call_stack[0]):
                    components.append(c.name)
            
            # Only include tests that have associated components
            if components:
                test_to_components.append({
                    "test": t.name,
                    "components": components
                })
    
    results["Q10"] = {"test_to_components": test_to_components}
    
    # Q11: go_api_test dependencies
    go_api_test = None
    for t in rig._tests:
        if "go_api_test" in t.name.lower() and t._evidence.call_stack:
            dependencies = []
            externals = []
            # Find dependencies - precise matching only
            for c in rig._components:
                if c.name == t.name or (t._evidence.call_stack and c.name in t._evidence.call_stack[0]):
                    dependencies.append(c.name)
            
            # Extract externals from the test's associated components
            for c in rig._components:
                if c.name in dependencies:
                    for ext in c._external_packages:
                        if ext.package_manager and ext.package_manager.package_name:
                            externals.append(ext.package_manager.package_name)
            
            go_api_test = {
                "dependencies": dependencies,
                "externals": externals
            }
            break
    
    if not go_api_test:
        go_api_test = {"dependencies": [], "externals": []}
    results["Q11"] = {"go_api_test": go_api_test}
    
    # Q12: xllr.openjdk.jni.bridge
    jni_bridge = None
    for c in rig._components:
        if "xllr.openjdk.jni.bridge" in c.name.lower() and c.output_path and c.source_files:
            jni_bridge = {
                "depends_on": [dep.name for dep in c.depends_on],
                "artifact": basename(str(c.output_path)),
                "defining_files": [str(f.split('#')[0]) for f in c._evidence.call_stack[:2]] if c._evidence and c._evidence.call_stack else []
            }
            break
    
    if not jni_bridge:
        jni_bridge = {"depends_on": [], "artifact": "", "defining_files": []}
    results["Q12"] = {"openjdk_jni_bridge": jni_bridge}
    
    # Q13: JAR files
    jars = []
    for c in rig._components:
        if c.output_path and str(c.output_path).lower().endswith('.jar'):
            jar_info = {
                "name": c.name,
                "artifact": basename(str(c.output_path)),
                "output_dir": str(c.output_path.parent) if c.output_path.parent else "",
                "defining_files": [str(f.split('#')[0]) for f in c._evidence.call_stack[:2]] if c._evidence and c._evidence.call_stack else []
            }
            jars.append(jar_info)
    results["Q13"] = {"jars": jars}
    
    # Q14: Go runtime binaries
    go_runtime_binaries = []
    for c in rig._components:
        # Check if it's a Go binary by language or by name containing "go"
        is_go_binary = (
            (hasattr(c, 'language') and c.language == 'go') or
            "go" in c.name.lower()
        )
        if c.type == ComponentType.SHARED_LIBRARY and is_go_binary:
            go_info = {
                "name": c.name,
                "artifact": basename(str(c.output_path)) if c.output_path else "",
                "defining_files": [str(f.split('#')[0]) for f in c._evidence.call_stack[:2]] if c._evidence and c._evidence.call_stack else []
            }
            go_runtime_binaries.append(go_info)
    results["Q14"] = {"go_runtime_binaries": go_runtime_binaries}
    
    return results


# =========================
# Aliases
# =========================

class Aliases:
    def __init__(self):
        # Pre-create all alias sets
        self.alias_sets = {
            "artifacts.externals": [
                # Boost filesystem aliases
                {
                    "boost::filesystem", 
                    "boost_filesystem", 
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_filesystem-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_filesystem-vc143-mt-gd-x64-1_87.lib"
                },
                # Boost program_options aliases
                {
                    "boost::program_options", 
                    "boost_program_options", 
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_program_options-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_program_options-vc143-mt-gd-x64-1_87.lib"
                },
                # Boost system aliases
                {
                    "boost::system", 
                    "boost_system", 
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_system-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_system-vc143-mt-gd-x64-1_87.lib"
                },
                # Boost container aliases
                {
                    "boost::container", 
                    "boost_container", 
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_container-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_container-vc143-mt-gd-x64-1_87.lib"
                },
                # Boost thread aliases
                {
                    "boost::thread", 
                    "boost_thread", 
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_thread-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_thread-vc143-mt-gd-x64-1_87.lib"
                },
                # Boost chrono aliases
                {
                    "boost::chrono", 
                    "boost_chrono", 
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_chrono-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_chrono-vc143-mt-gd-x64-1_87.lib"
                },
                # Boost date_time aliases
                {
                    "boost::date_time", 
                    "boost_date_time", 
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_date_time-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_date_time-vc143-mt-gd-x64-1_87.lib"
                },
                # Boost atomic aliases
                {
                    "boost::atomic", 
                    "boost_atomic", 
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_atomic-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_atomic-vc143-mt-gd-x64-1_87.lib"
                },
                # Windows system libraries
                {"kernel32", "kernel32.lib"},
                {"user32", "user32.lib"},
                {"gdi32", "gdi32.lib"},
                {"winspool", "winspool.lib"},
                {"shell32", "shell32.lib"},
                {"ole32", "ole32.lib"},
                {"oleaut32", "oleaut32.lib"},
                {"uuid", "uuid.lib"},
                {"comdlg32", "comdlg32.lib"},
                {"advapi32", "advapi32.lib"},
                {"synchronization", "synchronization.lib"},
                # JNI
                {"jni", "jni.lib", "jni.h"},
            ],
            # Apply same aliases to all externals fields
            "xllr_runtimes.externals": [
                # Boost filesystem aliases
                {
                    "boost::filesystem", 
                    "boost_filesystem", 
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_filesystem-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_filesystem-vc143-mt-gd-x64-1_87.lib"
                },
                # Boost program_options aliases
                {
                    "boost::program_options", 
                    "boost_program_options", 
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_program_options-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_program_options-vc143-mt-gd-x64-1_87.lib"
                },
                # Boost system aliases
                {
                    "boost::system", 
                    "boost_system", 
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_system-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_system-vc143-mt-gd-x64-1_87.lib"
                },
                # Boost container aliases
                {
                    "boost::container", 
                    "boost_container", 
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_container-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_container-vc143-mt-gd-x64-1_87.lib"
                },
                # Boost thread aliases
                {
                    "boost::thread", 
                    "boost_thread", 
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_thread-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_thread-vc143-mt-gd-x64-1_87.lib"
                },
                # Boost chrono aliases
                {
                    "boost::chrono", 
                    "boost_chrono", 
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_chrono-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_chrono-vc143-mt-gd-x64-1_87.lib"
                },
                # Boost date_time aliases
                {
                    "boost::date_time", 
                    "boost_date_time", 
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_date_time-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_date_time-vc143-mt-gd-x64-1_87.lib"
                },
                # Boost atomic aliases
                {
                    "boost::atomic", 
                    "boost_atomic", 
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_atomic-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_atomic-vc143-mt-gd-x64-1_87.lib"
                },
                # Windows system libraries
                {"kernel32", "kernel32.lib"},
                {"user32", "user32.lib"},
                {"gdi32", "gdi32.lib"},
                {"winspool", "winspool.lib"},
                {"shell32", "shell32.lib"},
                {"ole32", "ole32.lib"},
                {"oleaut32", "oleaut32.lib"},
                {"uuid", "uuid.lib"},
                {"comdlg32", "comdlg32.lib"},
                {"advapi32", "advapi32.lib"},
                {"synchronization", "synchronization.lib"},
                # JNI
                {"jni", "jni.lib", "jni.h"},
            ],
            "boost.libraries": [
                # Boost filesystem aliases
                {
                    "boost::filesystem", 
                    "boost_filesystem", 
                    "filesystem",
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_filesystem-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_filesystem-vc143-mt-gd-x64-1_87.lib"
                },
                # Boost program_options aliases
                {
                    "boost::program_options", 
                    "boost_program_options", 
                    "program_options",
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_program_options-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_program_options-vc143-mt-gd-x64-1_87.lib"
                },
                # Boost system aliases
                {
                    "boost::system", 
                    "boost_system", 
                    "system",
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_system-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_system-vc143-mt-gd-x64-1_87.lib"
                },
                # Boost container aliases
                {
                    "boost::container", 
                    "boost_container", 
                    "container",
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_container-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_container-vc143-mt-gd-x64-1_87.lib"
                },
                # Boost thread aliases
                {
                    "boost::thread", 
                    "boost_thread", 
                    "thread",
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_thread-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_thread-vc143-mt-gd-x64-1_87.lib"
                },
                # Boost chrono aliases
                {
                    "boost::chrono", 
                    "boost_chrono", 
                    "chrono",
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_chrono-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_chrono-vc143-mt-gd-x64-1_87.lib"
                },
                # Boost date_time aliases
                {
                    "boost::date_time", 
                    "boost_date_time", 
                    "date_time",
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_date_time-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_date_time-vc143-mt-gd-x64-1_87.lib"
                },
                # Boost atomic aliases
                {
                    "boost::atomic", 
                    "boost_atomic", 
                    "atomic",
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_atomic-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_atomic-vc143-mt-gd-x64-1_87.lib"
                },
            ],
            "boost.versions": [
                # Boost version aliases
                {
                    "1.87",
                    "1.87.0"
                }
            ],
            "go_api_test.externals": [
                # Boost filesystem aliases
                {
                    "boost::filesystem", 
                    "boost_filesystem", 
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_filesystem-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_filesystem-vc143-mt-gd-x64-1_87.lib"
                },
                # Boost program_options aliases
                {
                    "boost::program_options", 
                    "boost_program_options", 
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_program_options-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_program_options-vc143-mt-gd-x64-1_87.lib"
                },
                # Boost system aliases
                {
                    "boost::system", 
                    "boost_system", 
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_system-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_system-vc143-mt-gd-x64-1_87.lib"
                },
                # Boost container aliases
                {
                    "boost::container", 
                    "boost_container", 
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_container-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_container-vc143-mt-gd-x64-1_87.lib"
                },
                # Boost thread aliases
                {
                    "boost::thread", 
                    "boost_thread", 
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_thread-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_thread-vc143-mt-gd-x64-1_87.lib"
                },
                # Boost chrono aliases
                {
                    "boost::chrono", 
                    "boost_chrono", 
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_chrono-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_chrono-vc143-mt-gd-x64-1_87.lib"
                },
                # Boost date_time aliases
                {
                    "boost::date_time", 
                    "boost_date_time", 
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_date_time-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_date_time-vc143-mt-gd-x64-1_87.lib"
                },
                # Boost atomic aliases
                {
                    "boost::atomic", 
                    "boost_atomic", 
                    "c:\\src\\vcpkg\\installed\\x64-windows\\debug\\lib\\boost_atomic-vc143-mt-gd-x64-1_87.lib",
                    "c:/src/vcpkg/installed/x64-windows/debug/lib/boost_atomic-vc143-mt-gd-x64-1_87.lib"
                },
                # Windows system libraries
                {"kernel32", "kernel32.lib"},
                {"user32", "user32.lib"},
                {"gdi32", "gdi32.lib"},
                {"winspool", "winspool.lib"},
                {"shell32", "shell32.lib"},
                {"ole32", "ole32.lib"},
                {"oleaut32", "oleaut32.lib"},
                {"uuid", "uuid.lib"},
                {"comdlg32", "comdlg32.lib"},
                {"advapi32", "advapi32.lib"},
                {"synchronization", "synchronization.lib"},
                # JNI
                {"jni", "jni.lib", "jni.h"},
            ]
        }
    
    def is_aliases(self, field_name: str, value1: str, value2: str) -> bool:
        """Check if two values are aliases of each other in the given field."""
        if field_name not in self.alias_sets:
            return False
        
        # Normalize values for comparison
        norm_value1 = value1.lower().replace("\\", "/").strip()
        norm_value2 = value2.lower().replace("\\", "/").strip()
        
        # Check each alias set
        for alias_set in self.alias_sets[field_name]:
            # Normalize all values in the set
            norm_set = {v.lower().replace("\\", "/").strip() for v in alias_set}
            
            # If both values are in the same alias set, they are aliases
            if norm_value1 in norm_set and norm_value2 in norm_set:
                return True
        
        return False

# =========================
# Score Calculator
# =========================

class ScoreCalculator:
    def __init__(self, ground_truth_file: str):
        with open(ground_truth_file, 'r', encoding='utf-8') as f:
            self.ground_truth = json.load(f)
        
        # Initialize aliases
        self.aliases = Aliases()
    
    def calculate(self, agent_json: str) -> Scores:
        try:
            agent_data = json.loads(agent_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid agent JSON: {e}")
        
        per_question = {}
        skipped_questions = []
        
        # Initialize totals
        correct = 0
        incorrect = 0
        score = 0.0
        expected_fact_count = 0
        
        # Process each question
        for qid in [f"Q{n:02d}" for n in range(1, 15)]:
            if qid not in agent_data:
                skipped_questions.append(qid)
                continue
                
            question_score = self._score_question(qid, agent_data[qid], self.ground_truth.get(qid, {}))
            per_question[qid] = question_score
            
            correct += question_score.num_correct
            incorrect += question_score.num_incorrect
            score += question_score.score
            expected_fact_count += question_score.expected_fact_count
        
        # Calculate derived values
        total_facts = correct + incorrect
        accuracy = correct / max(1, total_facts) * 100 if total_facts > 0 else 0
        percentage = (correct / max(1, expected_fact_count)) * 100 if expected_fact_count > 0 else 0
        normalized_score = percentage / 10.0
        
        totals = ScoreTotals(
            correct=correct,
            incorrect=incorrect,
            expected_fact_count=expected_fact_count,
            score=score,
            normalized_score=normalized_score,
            percentage=percentage,
            accuracy=accuracy
        )
        
        return Scores(per_question=per_question, totals=totals, skipped_questions=skipped_questions)
    
    def _score_question(self, qid: str, agent_data: Dict[str, Any], ground_truth: Dict[str, Any]) -> PerQuestionScore:
        """Score a single question by comparing agent data with ground truth."""
        
        found_facts = []
        correct = 0
        incorrect = 0
        
        # Get the appropriate validator for this question
        validator = self._get_validator(qid)
        assert validator is not None, f"validator is None for {qid}"
        
        try:
            # Parse agent data with Pydantic
            agent_answer = validator(**agent_data)
            ground_truth_answer = validator(**ground_truth)
            
            # Compare the answers using the question-specific method
            comparison_result = agent_answer.compare_answers(ground_truth_answer, self)
            
            found_facts = comparison_result["found_facts"]
            correct = comparison_result["correct"]
            incorrect = comparison_result["incorrect"]
            
        except ValidationError as e:
            # Invalid JSON structure - count as incorrect
            found_facts.append(FoundFact(
                claim=f"Invalid JSON structure: {str(e)}",
                label=FactLabel.INCORRECT,
                raw=agent_data
            ))
            incorrect = 1
        
        expected_fact_count = correct + incorrect
        score = correct
        percentage = (correct / max(1, expected_fact_count)) * 100 if expected_fact_count > 0 else 0
        normalized_score = percentage / 10.0
        
        return PerQuestionScore(
            question_id=qid,
            found_facts=found_facts,
            num_correct=correct,
            num_incorrect=incorrect,
            expected_fact_count=expected_fact_count,
            score=score,
            normalized_score=normalized_score,
            percentage=percentage
        )
    
    def _get_validator(self, qid: str):
        """Get the appropriate Pydantic validator for a question."""
        validators = {
            "Q01": Q01Answer,
            "Q02": Q02Answer,
            "Q03": Q03Answer,
            "Q04": Q04Answer,
            "Q05": Q05Answer,
            "Q06": Q06Answer,
            "Q07": Q07Answer,
            "Q08": Q08Answer,
            "Q09": Q09Answer,
            "Q10": Q10Answer,
            "Q11": Q11Answer,
            "Q12": Q12Answer,
            "Q13": Q13Answer,
            "Q14": Q14Answer,
        }
        return validators.get(qid)
    
    
    def _compare_lists(self, agent_list: List, expected_list: List, field_name: str) -> Dict[str, Any]:
        """Compare lists using element-by-element search with 100% accuracy - no fallbacks."""
        found_facts = []
        correct = 0
        incorrect = 0
        
        # Input validation
        assert isinstance(agent_list, list), f"Agent list must be a list, got {type(agent_list)}"
        assert isinstance(expected_list, list), f"Expected list must be a list, got {type(expected_list)}"
        
        # Special case: string lists (like externals)
        # Check if ALL elements in both lists are strings
        if (agent_list and expected_list and 
            all(isinstance(item, str) for item in agent_list) and 
            all(isinstance(item, str) for item in expected_list)):
            return self._compare_string_lists(agent_list, expected_list, field_name)
        
        # Create lookup maps for expected items by core identifier
        expected_by_id = {}
        for item in expected_list:
            core_id = self._get_core_identifier(item)
            assert core_id not in expected_by_id, f"Duplicate core identifier {core_id} in expected list"
            expected_by_id[core_id] = item
        
        # Track which expected items we've found
        found_expected_ids = set()
        
        # Check each agent item
        for agent_item in agent_list:
            core_id = self._get_core_identifier(agent_item)
            
            if core_id in expected_by_id:
                # Found a match - compare individual fields
                expected_item = expected_by_id[core_id]
                found_expected_ids.add(core_id)
                
                # Compare each field separately with partial credit
                field_comparison = self._compare_individual_fields(agent_item, expected_item, field_name)
                found_facts.extend(field_comparison["found_facts"])
                correct += field_comparison["correct"]
                incorrect += field_comparison["incorrect"]
            else:
                # Not in expected - this is a hallucination
                incorrect += 1
                found_facts.append(FoundFact(
                    claim=f"{field_name}: {core_id}",
                    label=FactLabel.INCORRECT,
                    raw=agent_item,
                    expected="Not found in ground truth"
                ))
        
        # Check for missing items
        for core_id, expected_item in expected_by_id.items():
            if core_id not in found_expected_ids:
                incorrect += 1
                found_facts.append(FoundFact(
                    claim=f"{field_name}: {core_id}",
                    label=FactLabel.INCORRECT,
                    raw=expected_item,
                    expected=expected_item
                ))
        
        return {
            "found_facts": found_facts,
            "correct": correct,
            "incorrect": incorrect
        }
    
    def _compare_objects(self, agent_obj: Dict, expected_obj: Dict, field_name: str) -> Dict[str, Any]:
        """Compare two nested objects."""
        found_facts = []
        correct = 0
        incorrect = 0
        
        # Compare each field in the nested object
        for sub_field, expected_value in expected_obj.items():
            agent_value = agent_obj.get(sub_field)
            
            if isinstance(expected_value, list):
                # List comparison within nested object
                sub_field_name = f"{field_name}.{sub_field}"
                result = self._compare_lists(agent_value or [], expected_value or [], sub_field_name)
                found_facts.extend(result["found_facts"])
                correct += result["correct"]
                incorrect += result["incorrect"]
            else:
                # Normalized value comparison - no fallbacks
                agent_normalized = self._normalize_string(str(agent_value)) if agent_value is not None else ""
                expected_normalized = self._normalize_string(str(expected_value)) if expected_value is not None else ""
                
                if agent_normalized == expected_normalized:
                    correct += 1
                    found_facts.append(FoundFact(
                        claim=f"{field_name}.{sub_field}: {agent_value}",
                        label=FactLabel.CORRECT,
                        raw=agent_value
                    ))
                else:
                    incorrect += 1
                    found_facts.append(FoundFact(
                        claim=f"{field_name}.{sub_field}: {agent_value}",
                        label=FactLabel.INCORRECT,
                        raw=agent_value,
                        expected=expected_value
                    ))
        
        return {
            "found_facts": found_facts,
            "correct": correct,
            "incorrect": incorrect
        }
    
    def _normalize_string(self, s) -> str:
        """Normalize string for comparison (lowercase, path separators) - no fallbacks."""
        if s is None:
            return ""
        
        if s == "":
            return ""
        
        s_str = str(s)
        return s_str.lower().replace("\\", "/").strip()
    
    
    def _compare_string_lists(self, agent_list: List[str], expected_list: List[str], field_name: str) -> Dict[str, Any]:
        """Compare lists of strings with alias support."""
        found_facts = []
        correct = 0
        incorrect = 0
        
        # Track which expected items we've found
        found_expected = set()
        
        # Special handling for defining_files: agent gets credit for any correct item, no penalty for missing items
        if field_name.endswith(".defining_files") and len(expected_list) >= 2:
            # Check each agent item against the full expected list
            for agent_item in agent_list:
                found_match = False
                matched_expected = None
                
                # Check against all expected items (not just last two)
                for expected_item in expected_list:
                    exact_match = agent_item == expected_item
                    alias_match = self.aliases.is_aliases(field_name, agent_item, expected_item)
                    if exact_match or alias_match:
                        found_expected.add(expected_item)
                        found_match = True
                        matched_expected = expected_item
                        break
                
                if found_match:
                    correct += 1
                    found_facts.append(FoundFact(
                        claim=f"{field_name}: {agent_item}",
                        label=FactLabel.CORRECT,
                        raw=agent_item
                    ))
                else:
                    incorrect += 1
                    found_facts.append(FoundFact(
                        claim=f"{field_name}: {agent_item}",
                        label=FactLabel.INCORRECT,
                        raw=agent_item,
                        expected="Not found in ground truth"
                    ))
            
            # For defining_files, we don't check for missing items since agent only needs to provide any of the last two
            return {
                "found_facts": found_facts,
                "correct": correct,
                "incorrect": incorrect
            }
        
        # Regular comparison for other fields
        # Check each agent item
        for agent_item in agent_list:
            found_match = False
            matched_expected = None
            
            # Check if agent item matches any expected item (including aliases)
            for expected_item in expected_list:
                exact_match = agent_item == expected_item
                alias_match = self.aliases.is_aliases(field_name, agent_item, expected_item)
                if exact_match or alias_match:
                    found_expected.add(expected_item)
                    found_match = True
                    matched_expected = expected_item
                    break
            
            if found_match:
                correct += 1
                found_facts.append(FoundFact(
                    claim=f"{field_name}: {agent_item}",
                    label=FactLabel.CORRECT,
                    raw=agent_item
                ))
            else:
                incorrect += 1
                found_facts.append(FoundFact(
                    claim=f"{field_name}: {agent_item}",
                    label=FactLabel.INCORRECT,
                    raw=agent_item,
                    expected="Not found in ground truth"
                ))
        
        # Check for missing items (these are also incorrect)
        for expected_item in expected_list:
            if expected_item not in found_expected:
                incorrect += 1
                found_facts.append(FoundFact(
                    claim=f"{field_name}: MISSING {expected_item}",
                    label=FactLabel.INCORRECT,
                    raw=expected_item,
                    expected=expected_item
                ))
        
        return {
            "found_facts": found_facts,
            "correct": correct,
            "incorrect": incorrect
        }
    
    def _get_core_identifier(self, item) -> str:
        """Get core identifier for matching - no fallbacks."""
        if not isinstance(item, dict):
            # For non-dict items, use the string representation as identifier
            return self._normalize_string(str(item))
        
        # Handle different data structures
        if 'name' in item and 'artifact' in item:
            # Standard component structure (name + artifact + kind)
            name = self._normalize_string(item['name'])
            artifact = self._normalize_string(item['artifact'])
            kind = self._normalize_string(item.get('kind', ''))
            core_id = f"{name}|{artifact}|{kind}"
        elif 'test' in item and 'components' in item:
            # Test-to-component structure (test + components)
            test = self._normalize_string(item['test'])
            components = sorted([self._normalize_string(c) for c in item['components']])
            core_id = f"{test}|{','.join(components)}"
        else:
            # Fallback to all key-value pairs
            keys = sorted(item.keys())
            values = [self._normalize_string(str(item[k])) for k in keys]
            core_id = "|".join([f"{k}:{v}" for k, v in zip(keys, values)])
        
        return core_id
    
    def _compare_individual_fields(self, agent_item, expected_item, field_name: str) -> Dict[str, Any]:
        """Compare individual fields with partial credit - no fallbacks."""
        found_facts = []
        correct = 0
        incorrect = 0
        
        # Handle non-dict items
        if not isinstance(agent_item, dict) or not isinstance(expected_item, dict):
            agent_normalized = self._normalize_string(str(agent_item))
            expected_normalized = self._normalize_string(str(expected_item))
            
            if agent_normalized == expected_normalized:
                correct += 1
                found_facts.append(FoundFact(
                    claim=f"{field_name}: {agent_item}",
                    label=FactLabel.CORRECT,
                    raw=agent_item
                ))
            else:
                incorrect += 1
                found_facts.append(FoundFact(
                    claim=f"{field_name}: {agent_item}",
                    label=FactLabel.INCORRECT,
                    raw=agent_item,
                    expected=expected_item
                ))
            
            return {
                "found_facts": found_facts,
                "correct": correct,
                "incorrect": incorrect
            }
        
        # Get all possible fields from both items
        all_fields = set(agent_item.keys()) | set(expected_item.keys())
        
        for field in sorted(all_fields):
            agent_value = agent_item.get(field, [])
            expected_value = expected_item.get(field, [])
            
            # Handle list fields (like defining_files, externals, etc.)
            if isinstance(agent_value, list) and isinstance(expected_value, list):
                result = self._compare_lists(agent_value, expected_value, f"{field_name}.{field}")
                found_facts.extend(result["found_facts"])
                correct += result["correct"]
                incorrect += result["incorrect"]
            else:
                # Normalized value comparison
                agent_normalized = self._normalize_string(str(agent_value)) if agent_value is not None else ""
                expected_normalized = self._normalize_string(str(expected_value)) if expected_value is not None else ""
                
                if agent_normalized == expected_normalized:
                    correct += 1
                    found_facts.append(FoundFact(
                        claim=f"{field_name}.{field}: {agent_value}",
                        label=FactLabel.CORRECT,
                        raw=agent_value
                    ))
                else:
                    incorrect += 1
                    found_facts.append(FoundFact(
                        claim=f"{field_name}.{field}: {agent_value}",
                        label=FactLabel.INCORRECT,
                        raw=agent_value,
                        expected=expected_value
                    ))
        
        return {
            "found_facts": found_facts,
            "correct": correct,
            "incorrect": incorrect
        }


# =========================
# Score Comparer
# =========================

def score_comparer(scores1: Scores, scores2: Scores, name1: str, name2: str) -> None:
    """Compare two Scores objects and write a detailed report to markdown file."""
    
    # Create markdown content
    markdown_content = []
    
    # Header
    markdown_content.append("# Score Comparison Report")
    markdown_content.append("")
    markdown_content.append(f"**Comparing:** {name1} vs {name2}")
    markdown_content.append("")
    markdown_content.append("---")
    markdown_content.append("")
    
    # Overall performance comparison
    markdown_content.append("## Overall Performance Comparison")
    markdown_content.append("")
    markdown_content.append("| Metric | " + name1 + " | " + name2 + " | Difference |")
    markdown_content.append("|--------|" + "-" * (len(name1) + 2) + "|" + "-" * (len(name2) + 2) + "|------------|")
    
    percentage_diff = scores2.totals.percentage - scores1.totals.percentage
    accuracy_diff = scores2.totals.accuracy - scores1.totals.accuracy
    correct_diff = scores2.totals.correct - scores1.totals.correct
    
    # Color coding for differences
    def color_diff(diff, reverse=False):
        if diff > 0:
            return f"<span style='color: green'>+{diff:.1f}</span>" if not reverse else f"<span style='color: red'>+{diff:.1f}</span>"
        elif diff < 0:
            return f"<span style='color: red'>{diff:.1f}</span>" if not reverse else f"<span style='color: green'>{diff:.1f}</span>"
        else:
            return "0.0"
    
    markdown_content.append(f"| Percentage | {scores1.totals.percentage:.1f}% | {scores2.totals.percentage:.1f}% | {color_diff(percentage_diff)} |")
    markdown_content.append(f"| Normalized Score (0-10) | {scores1.totals.normalized_score:.2f} | {scores2.totals.normalized_score:.2f} | {color_diff(scores2.totals.normalized_score - scores1.totals.normalized_score)} |")
    markdown_content.append(f"| Raw Score | {scores1.totals.score:.2f} | {scores2.totals.score:.2f} | {color_diff(scores2.totals.score - scores1.totals.score)} |")
    markdown_content.append("")
    
    # Detailed counts comparison
    markdown_content.append("## Detailed Counts Comparison")
    markdown_content.append("")
    markdown_content.append("| Count Type | " + name1 + " | " + name2 + " | Difference |")
    markdown_content.append("|------------|" + "-" * (len(name1) + 2) + "|" + "-" * (len(name2) + 2) + "|------------|")
    markdown_content.append(f"| Correct | {scores1.totals.correct} | {scores2.totals.correct} | {color_diff(correct_diff)} |")
    markdown_content.append(f"| Incorrect | {scores1.totals.incorrect} | {scores2.totals.incorrect} | {color_diff(scores2.totals.incorrect - scores1.totals.incorrect, reverse=True)} |")
    markdown_content.append(f"| Expected Count | {scores1.totals.expected_fact_count} | {scores2.totals.expected_fact_count} | {color_diff(scores2.totals.expected_fact_count - scores1.totals.expected_fact_count)} |")
    markdown_content.append(f"| Accuracy | {scores1.totals.accuracy:.1f}% | {scores2.totals.accuracy:.1f}% | {color_diff(accuracy_diff)} |")
    markdown_content.append("")
    
    # Per-question comparison
    markdown_content.append("## Per-Question Comparison")
    markdown_content.append("")
    markdown_content.append("| Question | Metric | " + name1 + " | " + name2 + " | Expected from RIG | Difference |")
    markdown_content.append("|----------|--------|" + "-" * (len(name1) + 2) + "|" + "-" * (len(name2) + 2) + "|-------------------|------------|")
    
    all_questions = set(scores1.per_question.keys()) | set(scores2.per_question.keys())
    for qid in sorted(all_questions):
        q1 = scores1.per_question.get(qid)
        q2 = scores2.per_question.get(qid)
        
        if q1 and q2:
            q_diff = q2.percentage - q1.percentage
            markdown_content.append(f"| {qid} | Percentage | {q1.percentage:.1f}% | {q2.percentage:.1f}% | 100.0% | {color_diff(q_diff)} |")
            markdown_content.append(f"| {qid} | Correct | {q1.num_correct} | {q2.num_correct} | {q1.expected_fact_count} | {color_diff(q2.num_correct - q1.num_correct)} |")
            markdown_content.append(f"| {qid} | Incorrect | {q1.num_incorrect} | {q2.num_incorrect} | 0 | {color_diff(q2.num_incorrect - q1.num_incorrect, reverse=True)} |")
        elif q1:
            markdown_content.append(f"| {qid} | Percentage | {q1.percentage:.1f}% | N/A | 100.0% | N/A |")
        elif q2:
            markdown_content.append(f"| {qid} | Percentage | N/A | {q2.percentage:.1f}% | 100.0% | N/A |")
    
    markdown_content.append("")
    
    # Impact analysis
    markdown_content.append("## Impact Analysis")
    markdown_content.append("")
    
    if percentage_diff > 0:
        markdown_content.append(f"✅ **{name2} outperforms {name1} by {percentage_diff:.1f} percentage points**")
    elif percentage_diff < 0:
        markdown_content.append(f"❌ **{name1} outperforms {name2} by {abs(percentage_diff):.1f} percentage points**")
    else:
        markdown_content.append(f"🤝 **{name1} and {name2} have the same percentage**")
    
    if accuracy_diff > 0:
        markdown_content.append(f"✅ **{name2} has {accuracy_diff:.1f}% higher accuracy than {name1}**")
    elif accuracy_diff < 0:
        markdown_content.append(f"❌ **{name1} has {abs(accuracy_diff):.1f}% higher accuracy than {name2}**")
    else:
        markdown_content.append(f"🤝 **{name1} and {name2} have the same accuracy**")
    
    if correct_diff > 0:
        markdown_content.append(f"✅ **{name2} has {correct_diff} more correct facts than {name1}**")
    elif correct_diff < 0:
        markdown_content.append(f"❌ **{name1} has {abs(correct_diff)} more correct facts than {name2}**")
    else:
        markdown_content.append(f"🤝 **{name1} and {name2} have the same number of correct facts**")
    
    if scores1.totals.incorrect == scores2.totals.incorrect:
        markdown_content.append(f"🤝 **{name1} and {name2} have the same number of incorrect facts**")
    else:
        incorrect_diff = scores2.totals.incorrect - scores1.totals.incorrect
        if incorrect_diff > 0:
            markdown_content.append(f"❌ **{name2} has {incorrect_diff} more incorrect facts than {name1}**")
        else:
            markdown_content.append(f"✅ **{name1} has {abs(incorrect_diff)} more incorrect facts than {name2}**")
    
    markdown_content.append("")
    
    # Best performing questions
    markdown_content.append("## Best Performing Questions")
    markdown_content.append("")
    question_diffs = []
    for qid in all_questions:
        q1 = scores1.per_question.get(qid)
        q2 = scores2.per_question.get(qid)
        if q1 and q2:
            diff = q2.percentage - q1.percentage
            question_diffs.append((qid, diff))
    
    question_diffs.sort(key=lambda x: x[1], reverse=True)
    for qid, diff in question_diffs[:3]:
        if diff > 0:
            markdown_content.append(f"✅ **{qid}**: {name2} +{diff:.1f}% vs {name1}")
        elif diff < 0:
            markdown_content.append(f"❌ **{qid}**: {name1} +{abs(diff):.1f}% vs {name2}")
    
    markdown_content.append("")
    
    # Final verdict
    markdown_content.append("## Final Verdict")
    markdown_content.append("")
    if percentage_diff > 5:
        markdown_content.append(f"🏆 **WINNER: {name2}**")
        markdown_content.append(f"   {name2} is **SIGNIFICANTLY BETTER** than {name1}")
        markdown_content.append(f"   Performance difference: **{percentage_diff:.1f} percentage points**")
        markdown_content.append(f"   **Recommendation:** Use {name2} for superior results")
    elif percentage_diff < -5:
        markdown_content.append(f"🏆 **WINNER: {name1}**")
        markdown_content.append(f"   {name1} is **SIGNIFICANTLY BETTER** than {name2}")
        markdown_content.append(f"   Performance difference: **{abs(percentage_diff):.1f} percentage points**")
        markdown_content.append(f"   **Recommendation:** Use {name1} for superior results")
    else:
        markdown_content.append(f"🤝 **TIE: {name1} and {name2}**")
        markdown_content.append(f"   Performance difference: **{abs(percentage_diff):.1f} percentage points**")
        markdown_content.append(f"   **Recommendation:** Both perform similarly")
    
    markdown_content.append("")
    markdown_content.append("### Key Insights")
    markdown_content.append(f"- **Accuracy difference:** {accuracy_diff:+.1f}% ({name2} vs {name1})")
    markdown_content.append(f"- **Correct facts difference:** {correct_diff:+d} ({name2} vs {name1})")
    if question_diffs:
        best_q = question_diffs[0]
        markdown_content.append(f"- **{name2} excels most at:** {best_q[0]} ({best_q[1]:+.1f}%)")
    
    markdown_content.append("")
    
    # Detailed incorrect facts
    markdown_content.append("## Detailed Incorrect Facts")
    markdown_content.append("")
    
    for qid in sorted(all_questions):
        q1 = scores1.per_question.get(qid)
        q2 = scores2.per_question.get(qid)
        
        if not q1 and not q2:
            continue
            
        markdown_content.append(f"### {qid}")
        markdown_content.append("")
        
        # Show hallucinations for both
        if q1 and q1.num_incorrect > 0:
            markdown_content.append(f"**{name1} Incorrect Facts ({q1.num_incorrect}):**")
            markdown_content.append("")
            for i, fact in enumerate(q1.found_facts, 1):
                if fact.label == FactLabel.INCORRECT:
                    if fact.expected is not None:
                        markdown_content.append(f"{i}. `{fact.claim}` → <span style='color: red'>**{fact.label.value}** (expected: `{fact.expected}`)</span>")
                    else:
                        markdown_content.append(f"{i}. `{fact.claim}` → <span style='color: red'>**{fact.label.value}**</span>")
            markdown_content.append("")
        
        if q2 and q2.num_incorrect > 0:
            markdown_content.append(f"**{name2} Incorrect Facts ({q2.num_incorrect}):**")
            markdown_content.append("")
            for i, fact in enumerate(q2.found_facts, 1):
                if fact.label == FactLabel.INCORRECT:
                    if fact.expected is not None:
                        markdown_content.append(f"{i}. `{fact.claim}` → <span style='color: red'>**{fact.label.value}** (expected: `{fact.expected}`)</span>")
                    else:
                        markdown_content.append(f"{i}. `{fact.claim}` → <span style='color: red'>**{fact.label.value}**</span>")
            markdown_content.append("")
        
        if (q1 and q1.num_incorrect == 0) and (q2 and q2.num_incorrect == 0):
            markdown_content.append(f"✅ No incorrect facts found for either {name1} or {name2}")
            markdown_content.append("")
    
    # Missing facts analysis
    markdown_content.append("## Missing Facts Analysis")
    markdown_content.append("*What each response needs for perfect score*")
    markdown_content.append("")
    
    for qid in sorted(all_questions):
        q1 = scores1.per_question.get(qid)
        q2 = scores2.per_question.get(qid)
        
        if not q1 and not q2:
            continue
            
        markdown_content.append(f"### {qid}")
        markdown_content.append("")
        
        if q1:
            expected = q1.expected_fact_count
            actual = q1.num_correct
            missing = q1.num_incorrect
            markdown_content.append(f"**Expected:** {expected} correct, 0 incorrect")
            markdown_content.append(f"**Actual in \"{name1}\":** {actual} correct, {q1.num_incorrect} incorrect")
            markdown_content.append("")
            
            if missing > 0:
                markdown_content.append(f"**Missing items in \"{name1}\" ({missing}):**")
                markdown_content.append("")
                for i, fact in enumerate(q1.found_facts, 1):
                    if fact.label == FactLabel.INCORRECT:
                        markdown_content.append(f"{i}. `{fact.claim}`")
                markdown_content.append("")
            else:
                markdown_content.append(f"✅ **No missing items in \"{name1}\" - perfect score!**")
                markdown_content.append("")
        
        if q2:
            expected = q2.expected_fact_count
            actual = q2.num_correct
            missing = q2.num_incorrect
            markdown_content.append(f"**Expected:** {expected} correct, 0 incorrect")
            markdown_content.append(f"**Actual in \"{name2}\":** {actual} correct, {q2.num_incorrect} incorrect")
            markdown_content.append("")
            
            if missing > 0:
                markdown_content.append(f"**Missing items in \"{name2}\" ({missing}):**")
                markdown_content.append("")
                for i, fact in enumerate(q2.found_facts, 1):
                    if fact.label == FactLabel.INCORRECT:
                        markdown_content.append(f"{i}. `{fact.claim}`")
                markdown_content.append("")
            else:
                markdown_content.append(f"✅ **No missing items in \"{name2}\" - perfect score!**")
                markdown_content.append("")
    
    # Write to file
    with open('comparison_results.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(markdown_content))
    
    print("Comparison report written to comparison_results.md")
    print(f"Overall: {name1} {scores1.totals.percentage:.1f}% vs {name2} {scores2.totals.percentage:.1f}% - {percentage_diff:+.1f}% difference")


# =========================
# Main Function
# =========================

def main():
    # Generate ground truth from RIG
    metaffi_config_dir = Path("C:/src/github.com/MetaFFI/cmake-build-debug")
    entrypoint = CMakeEntrypoint(metaffi_config_dir)
    rig = entrypoint.rig
    
    print("Generating ground truth from RIG...")
    ground_truth = generate_results_from_rig(rig)
    
    # Save ground truth
    with open('results_from_rig.json', 'w', encoding='utf-8') as f:
        json.dump(ground_truth, f, indent=2)
    print("Ground truth saved to results_from_rig.json")
    
    # Load agent responses
    with open('results_cursor_without_rig.json', 'r', encoding='utf-8') as f:
        results_without_rig = f.read()
    
    with open('results_cursor_with_rig.json', 'r', encoding='utf-8') as f:
        results_with_rig = f.read()
    
    # Calculate scores
    print("Calculating scores...")
    scorer = ScoreCalculator('results_from_rig.json')
    
    scores_without_rig = scorer.calculate(results_without_rig)
    scores_with_rig = scorer.calculate(results_with_rig)
    
    # Compare scores
    print("Generating comparison report...")
    score_comparer(scores_without_rig, scores_with_rig, "WITHOUT RIG", "WITH RIG")


if __name__ == "__main__":
    main()
