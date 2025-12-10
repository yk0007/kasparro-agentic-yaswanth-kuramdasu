"""
Safety Logic Block.

Transforms product safety information using LLM.
"""

from typing import Dict, List, Any
import sys
import os
import json
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ProductModel
from config import invoke_with_retry

logger = logging.getLogger(__name__)


def generate_safety_block(product: ProductModel) -> Dict[str, Any]:
    """
    Transform product safety info using LLM.
    
    Args:
        product: Validated ProductModel
        
    Returns:
        Dictionary containing structured safety data
    """
    considerations = product.considerations
    target_users = product.target_users.copy()
    
    try:
        prompt = f"""Generate safety information for "{product.name}".

Known considerations: {considerations}
Target users: {', '.join(target_users)}

Return JSON: {{"precautions": ["..."], "who_should_avoid": ["..."], "storage": "..."}}
Output ONLY valid JSON."""

        response = invoke_with_retry(prompt).strip()
        
        if "```" in response:
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        response = response.strip()
        
        expanded = json.loads(response)
        
        return {
            "considerations": considerations,
            "considerations": considerations,
            "target_users": target_users,
            "suitable_for": target_users,
            "expanded_safety": expanded,
            "product_name": product.name
        }
    except Exception as e:
        logger.warning(f"Safety block LLM failed: {e}")
        return {
            "considerations": considerations,
            "considerations": considerations,
            "target_users": target_users,
            "suitable_for": target_users,
            "expanded_safety": {"precautions": [considerations] if considerations else [], "who_should_avoid": [], "storage": "Follow guidelines"},
            "product_name": product.name
        }
