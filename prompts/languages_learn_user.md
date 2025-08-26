INPUT:
{
  "repo_root_name": "{{REPO_NAME}}",
  "candidates": {{UNKNOWN_EXTS_JSON}}
}

INSTRUCTION:
Return a JSON array ONLY, each item:
  { "ext": "...", "language": "...", "confidence": 0.0..1.0 }
