import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.rig import RIG


def verify_non_optimized_vs_optimized(non_optimized_json: str, optimized_json: str) -> bool:
    """Validate that optimized JSON preserves semantics and reduces size.

    Fast-fail policy: raise on structural mismatches; return True on success.
    Accept fallback (optimizer may return original when no gain).
    """
    base = json.loads(non_optimized_json)
    opt = json.loads(optimized_json)

    # Fallback path: optimized equals base dict
    if not isinstance(opt, dict) or 'data' not in opt or 'lookups' not in opt:
        assert base == opt, "Fallback optimized JSON differs from base"
        return True

    lookups = opt['lookups']
    data = opt['data']

    paths = lookups.get('paths', [])
    strings = lookups.get('strings', [])
    key_map = lookups.get('keys', {})  # alias -> original

    def expand_scalar(x):
        if isinstance(x, str) and x.startswith('$') and len(x) > 2:
            tag, idx = x[1], x[2:]
            if idx.isdigit():
                i = int(idx)
                if tag == 'p':
                    assert 0 <= i < len(paths), 'Path index out of range'
                    return paths[i]
                if tag == 's':
                    assert 0 <= i < len(strings), 'String index out of range'
                    return strings[i]
        return x

    def restore(node):
        if isinstance(node, dict):
            out = {}
            for k, v in node.items():
                ok = key_map.get(k, k)
                out[ok] = restore(v)
            return out
        if isinstance(node, list):
            return [restore(v) for v in node]
        return expand_scalar(node)

    restored = restore(data)

    # Semantic equality
    assert restored == base, 'Restored optimized JSON does not match base JSON'

    # Size advantage
    assert len(optimized_json) <= len(non_optimized_json), 'Optimized JSON is larger than base JSON'
    return True


class MyTestCase(unittest.TestCase):
    def test_something(self):
        # load RIG from metaffi_ground_truth.sqlite3 (same dir as this test)
        original_rig = RIG.load(Path(__file__).parent / 'metaffi_ground_truth.sqlite3')
        non_optimized_json = original_rig.generate_prompts_json_data(False)
        optimized_json = original_rig.generate_prompts_json_data(True)
        self.assertTrue(verify_non_optimized_vs_optimized(non_optimized_json, optimized_json))


if __name__ == '__main__':
    unittest.main()
