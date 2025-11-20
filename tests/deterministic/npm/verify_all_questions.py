import json
from collections import defaultdict, deque

# Load files
with open('evaluation_questions.json', 'r') as f:
    eval_data = json.load(f)

with open('npm_ground_truth.json', 'r') as f:
    gt = json.load(f)

questions = {q['id']: q for q in eval_data['questions']}
components = gt['components']
comp_by_id = {c['id']: c for c in components}
comp_by_name = {c['name']: c for c in components}

def get_transitive_dependents(comp_id):
    """Get all components that transitively depend on comp_id"""
    dependents = set()
    
    def find_deps(target_id):
        for comp in components:
            if target_id in comp['depends_on_ids']:
                if comp['name'] not in dependents:
                    dependents.add(comp['name'])
                    find_deps(comp['id'])
    
    find_deps(comp_id)
    return sorted(list(dependents))

def calculate_max_depth():
    """Calculate maximum dependency depth"""
    def get_depth(comp_id, visited=None):
        if visited is None:
            visited = set()
        if comp_id in visited:
            return 0
        visited = visited.copy()
        visited.add(comp_id)
        
        comp = comp_by_id[comp_id]
        if not comp['depends_on_ids']:
            return 0
        
        max_dep = 0
        for dep_id in comp['depends_on_ids']:
            d = get_depth(dep_id, visited)
            max_dep = max(max_dep, d)
        
        return max_dep + 1
    
    return max(get_depth(c['id']) for c in components)

def topological_sort():
    """Perform topological sort"""
    in_degree = {c['id']: 0 for c in components}
    
    for comp in components:
        for dep_id in comp['depends_on_ids']:
            in_degree[dep_id] += 1
    
    queue = sorted([c['id'] for c in components if in_degree[c['id']] == 0])
    result = []
    
    while queue:
        current_id = queue.pop(0)
        result.append(comp_by_id[current_id]['name'])
        
        candidates = []
        for comp in components:
            if current_id in comp['depends_on_ids']:
                in_degree[comp['id']] -= 1
                if in_degree[comp['id']] == 0:
                    candidates.append(comp['id'])
        
        queue.extend(sorted(candidates))
        queue.sort()
    
    return result

def get_cross_language_types():
    """Get cross-language dependency types"""
    pairs = set()
    for comp in components:
        comp_lang = comp['programming_language']
        for dep_id in comp['depends_on_ids']:
            dep_lang = comp_by_id[dep_id]['programming_language']
            if comp_lang != dep_lang:
                pair = f"{comp_lang}-{dep_lang}"
                pairs.add(pair)
    return sorted(list(pairs))

print("="*80)
print("VERIFICATION OF ALL 30 EVALUATION QUESTIONS")
print("="*80)

failures = []
passes = []

# Q1
q = questions[1]
expected = q['expected_answer']
actual = gt['repo']['name']
status = "PASS" if expected == actual else "FAIL"
print(f"\nQ1: {q['name']}")
print(f"  Expected: {expected}")
print(f"  Actual: {actual}")
print(f"  Status: {status}")
(passes if status == "PASS" else failures).append(1)

# Q2 - workspace_count (need to check root package.json)
q = questions[2]
print(f"\nQ2: {q['name']}")
print(f"  Expected: {q['expected_answer']}")
print(f"  Status: SKIP (needs root package.json inspection)")

# Q3
q = questions[3]
expected = q['expected_answer']
core = comp_by_name['core.dist.js']
