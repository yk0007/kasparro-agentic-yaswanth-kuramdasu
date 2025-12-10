"""
Benefits Logic Block.

Transforms product benefits into structured content using LLM.
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


def generate_benefits_block(product: ProductModel) -> Dict[str, Any]:
    """
    Transform product benefits into structured content using LLM.
    
    Args:
        product: Validated ProductModel
        
    Returns:
        Dictionary containing structured benefits data
    """
    try:
        prompt = f"""Expand each benefit for "{product.name}" into a brief description.

Product: {product.name}
Benefits: {', '.join(product.benefits)}

Return JSON array: [{{"benefit": "X", "description": "..."}}]
Output ONLY valid JSON array."""

        response = invoke_with_retry(prompt).strip()
        
        # Clean markdown code blocks
        if "```" in response:
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        response = response.strip()
        
        detailed = json.loads(response)
        
        return {
            "primary_benefits": product.benefits.copy(),
            "detailed_benefits": detailed,
            "total_benefits": len(product.benefits)
        }
    except Exception as e:
        logger.warning(f"Benefits block LLM failed: {e}")
        return {
            "primary_benefits": product.benefits.copy(),
            "detailed_benefits": [{"benefit": b, "description": f"{product.name} provides {b}."} for b in product.benefits],
            "total_benefits": len(product.benefits)
        }
