"""
Usage Logic Block.

Transforms product usage instructions using LLM.
"""

from typing import Dict, Any
import sys
import os
import json
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ProductModel
from config import invoke_with_retry

logger = logging.getLogger(__name__)


def generate_usage_block(product: ProductModel) -> Dict[str, Any]:
    """
    Transform product usage instructions using LLM.
    
    Args:
        product: Validated ProductModel
        
    Returns:
        Dictionary containing structured usage data
    """
    raw_usage = product.how_to_use
    
    try:
        prompt = f"""Expand usage instructions for "{product.name}".

Instructions: {raw_usage}

Return JSON: {{"steps": ["step1", "step2"], "tips": ["tip1"], "frequency": "daily/weekly/etc"}}
Output ONLY valid JSON."""

        response = invoke_with_retry(prompt).strip()
        
        if "```" in response:
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        response = response.strip()
        
        expanded = json.loads(response)
        
        return {
            "raw_instructions": raw_usage,
            "summary": raw_usage,
            "expanded_instructions": expanded,
            "product_name": product.name
        }
    except Exception as e:
        logger.warning(f"Usage block LLM failed: {e}")
        return {
            "raw_instructions": raw_usage,
            "summary": raw_usage,
            "expanded_instructions": {"steps": [raw_usage], "tips": [], "frequency": "As directed"},
            "product_name": product.name
        }
