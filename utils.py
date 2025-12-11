"""
Utility functions for Multi-Agent Content Generation System.

Provides common utilities used across agents and logic blocks.
"""

import re
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def clean_json_response(response: str) -> str:
    """
    Clean JSON response from LLM by removing markdown code blocks.
    
    This function handles common LLM response patterns where JSON is wrapped
    in markdown code fences like ```json ... ``` or ``` ... ```.
    
    Args:
        response: Raw LLM response that may contain markdown formatting
        
    Returns:
        Cleaned JSON string ready for parsing
        
    Example:
        >>> clean_json_response('```json\\n{"key": "value"}\\n```')
        '{"key": "value"}'
    """
    if not response:
        return ""
    
    cleaned = response.strip()
    
    # Remove markdown code blocks
    if "```" in cleaned:
        # Try to extract content between code fences
        pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
        match = re.search(pattern, cleaned)
        if match:
            cleaned = match.group(1).strip()
        else:
            # Fallback: remove all occurrences of ```json and ```
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()
    
    return cleaned


def parse_json_safely(response: str, default: Any = None) -> Optional[Any]:
    """
    Safely parse JSON from LLM response, handling common formatting issues.
    
    Args:
        response: Raw LLM response
        default: Default value to return on parse failure
        
    Returns:
        Parsed JSON object or default value
    """
    try:
        cleaned = clean_json_response(response)
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON: {e}")
        return default
    except Exception as e:
        logger.error(f"Unexpected error parsing JSON: {e}")
        return default


def truncate_string(s: str, max_length: int = 100) -> str:
    """
    Truncate a string to a maximum length with ellipsis.
    
    Args:
        s: String to truncate
        max_length: Maximum length including ellipsis
        
    Returns:
        Truncated string with '...' if necessary
    """
    if len(s) <= max_length:
        return s
    return s[:max_length - 3] + "..."
