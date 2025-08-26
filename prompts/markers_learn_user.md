INPUT:
{
  "repo_root_name": "{{REPO_NAME}}",
  "min_confidence": {{MIN_CONF}},
  "candidates": {{CANDIDATE_NAMES_JSON}}
}

INSTRUCTION:
Return a JSON array ONLY, each item:
  { "match": "...", "type": "...", "languages": ["..."]?, "weight": 0.0..1.0, "confidence": 0.0..1.0 }
