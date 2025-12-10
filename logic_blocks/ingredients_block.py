"""
Ingredients/Features Logic Block.

Transforms product features into structured content using LLM.
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


def generate_ingredients_block(product: ProductModel) -> Dict[str, Any]:
    """
    Transform product features into structured content using LLM.
    
    Args:
        product: Validated ProductModel
        
    Returns:
        Dictionary containing structured features data
    """
    features = product.key_features.copy()
    
    try:
        prompt = f"""Describe each key feature for "{product.name}".

Product: {product.name}
Features: {', '.join(features)}

Return JSON array: [{{"name": "X", "description": "..."}}]
Output ONLY valid JSON array."""

        response = invoke_with_retry(prompt).strip()
        
        if "```" in response:
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        response = response.strip()
        
        details = json.loads(response)
        
        return {
            "key_features": features,
            "active_ingredients": features,
            "ingredient_details": details,
            "feature_details": details,
            "ingredient_count": len(features),
            "highlight_feature": features[0] if features else "",
            "highlight_ingredient": features[0] if features else "",
            "product_type": product.product_type
        }
    except Exception as e:
        logger.warning(f"Ingredients block LLM failed: {e}")
        return {
            "key_features": features,
            "active_ingredients": features,
            "ingredient_details": [{"name": f, "description": f"{f} is a key component."} for f in features],
            "feature_details": [{"name": f, "description": f"{f} is a key component."} for f in features],
            "ingredient_count": len(features),
            "highlight_feature": features[0] if features else "",
            "highlight_ingredient": features[0] if features else "",
            "product_type": product.product_type
        }
