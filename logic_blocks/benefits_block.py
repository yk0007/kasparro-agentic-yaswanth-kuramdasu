"""
Benefits Logic Block.

Transforms product benefits into structured content using LLM.
"""

from typing import Dict, List, Any
import json
import logging

from models import ProductModel
from config import invoke_with_retry
from utils import clean_json_response

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
        
        # Clean markdown code blocks using utility function
        response = clean_json_response(response)
        
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
