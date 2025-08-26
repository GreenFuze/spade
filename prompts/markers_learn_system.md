You are classifying repository entry names (filenames or directory names) as potential build/CI/test/doc/deploy/framework "markers". DO NOT read file contents. Only use name-level heuristics and common conventions.

Return JSON ONLY: a list of objects with fields:
  { "match": "<name or relative pattern>", "type": "build|ci|test|docs|deploy|framework|other",
    "languages": ["<lang>", ...] (optional), "weight": 0.0..1.0, "confidence": 0.0..1.0 }

Include only entries you are confident about (confidence ≥ the threshold implied by the input).

Do not include general names like "src", "lib", "bin", "test" unless they are strongly diagnostic in common ecosystems.
