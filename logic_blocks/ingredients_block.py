"""
Ingredients/Features Logic Block.

Transforms product features into structured content using LLM.
"""

from typing import Dict, List, Any
import json
import logging

from models import ProductModel
from config import invoke_with_retry
from utils import clean_json_response

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
        
        response = clean_json_response(response)
        
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
