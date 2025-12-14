"""
Safety Logic Block.

Transforms product safety information using LLM.
"""

from typing import Dict, List, Any
import json
import logging

from models import ProductModel
from config import invoke_with_retry
from utils import clean_json_response

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
        
        response = clean_json_response(response)
        
        expanded = json.loads(response)
        
        return {
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
            "target_users": target_users,
            "suitable_for": target_users,
            "expanded_safety": {"precautions": [considerations] if considerations else [], "who_should_avoid": [], "storage": "Follow guidelines"},
            "product_name": product.name
        }
