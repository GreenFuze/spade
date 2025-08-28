"""
Dummy transport for testing SPADE without external LLM calls.
"""

import json
from typing import Any, Dict, List


def echo_transport_valid_response(messages: List[Dict[str, Any]]) -> str:
    """
    Echo transport that returns a valid JSON response for testing.

    Args:
        messages: List of messages sent to the LLM

    Returns:
        Valid JSON response string
    """
    # Extract context from the last user message
    context = None
    for msg in reversed(messages):
        if msg.get("role") == "user":
            try:
                # Try to parse the content as JSON
                content = msg.get("content", "")
                context = json.loads(content)
                break
            except json.JSONDecodeError:
                continue

    if not context:
        # Fallback response
        return json.dumps(
            {
                "inferred": {"high_level_components": [], "nodes": {}},
                "nav": {
                    "descend_into": [],
                    "descend_one_level_only": True,
                    "reasons": [],
                },
                "open_questions_ranked": [],
            }
        )

    # Extract basic info from context
    current_path = context.get("current_path", ".")
    siblings = context.get("siblings", [])

    # Create a simple response based on the context
    response = {
        "inferred": {
            "high_level_components": [
                {
                    "name": f"Component-{current_path}",
                    "role": "main component",
                    "dirs": [current_path],
                    "evidence": [{"type": "path", "value": current_path}],
                    "confidence": 0.8,
                }
            ],
            "nodes": {
                current_path: {
                    "summary": f"This is the {current_path} directory containing code and documentation.",
                    "languages": ["python", "javascript"],
                    "tags": ["backend", "api"],
                    "evidence": [
                        {"type": "marker", "value": "package.json"},
                        {"type": "name", "value": current_path},
                    ],
                    "confidence": 0.9,
                }
            },
        },
        "nav": {
            "descend_into": siblings[:2] if siblings else [],  # Limit to 2 children
            "descend_one_level_only": True,
            "reasons": ["contains code", "has documentation"],
        },
        "open_questions_ranked": [
            "What is the main purpose of this component?",
            "Are there any external dependencies?",
        ],
    }

    return json.dumps(response, indent=2)


def valid_dummy_transport(messages: List[Dict[str, Any]]) -> str:
    """
    Valid dummy transport that returns realistic responses.

    Args:
        messages: List of messages sent to the LLM

    Returns:
        Valid JSON response string
    """
    return echo_transport_valid_response(messages)


def invalid_dummy_transport(messages: List[Dict[str, Any]]) -> str:
    """
    Invalid dummy transport that returns non-JSON to test error handling.

    Args:
        messages: List of messages sent to the LLM

    Returns:
        Invalid response string
    """
    return "This is not valid JSON and should trigger error handling"


def echo_transport_markers_learning(messages: List[Dict[str, Any]]) -> str:
    """
    Dummy transport for markers learning.

    Args:
        messages: List of messages sent to the LLM

    Returns:
        Valid JSON response for markers learning
    """
    return json.dumps(
        {
            "learned_markers": [
                {
                    "match": "package.json",
                    "type": "marker",
                    "languages": ["javascript", "typescript"],
                    "weight": 0.8,
                    "confidence": 0.9,
                    "source": "llm",
                }
            ]
        }
    )


def echo_transport_languages_learning(messages: List[Dict[str, Any]]) -> str:
    """
    Dummy transport for languages learning.

    Args:
        messages: List of messages sent to the LLM

    Returns:
        Valid JSON response for languages learning
    """
    return json.dumps(
        {
            "learned_languages": [
                {
                    "ext": "js",
                    "language": "javascript",
                    "confidence": 0.95,
                    "source": "llm",
                },
                {
                    "ext": "ts",
                    "language": "typescript",
                    "confidence": 0.9,
                    "source": "llm",
                },
            ]
        }
    )
