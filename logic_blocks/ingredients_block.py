"""
Ingredients/Features Logic Block.

Pure functions for transforming product features/ingredients into structured content.
Works with any product type (tech, fashion, skincare, etc.)
"""

from typing import Dict, List, Any
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ProductModel


def generate_ingredients_block(product: ProductModel) -> Dict[str, Any]:
    """
    Transform product key ingredients/features into detailed structured content.
    
    Generic implementation that works with any product type.
    The term "ingredients" is used for compatibility but represents
    key features for non-skincare products.
    
    Args:
        product: Validated ProductModel containing key_ingredients data
        
    Returns:
        Dictionary containing structured features/ingredients data
    """
    features: List[str] = product.key_ingredients.copy()
    
    # Build feature details (generic)
    feature_details: List[Dict[str, Any]] = []
    for feature in features:
        feature_details.append({
            "name": feature,
            "description": f"{feature} is a key component of {product.name}."
        })
    
    # First feature is typically the highlight
    highlight = features[0] if features else ""
    
    return {
        "active_ingredients": features,  # For compatibility
        "key_features": features,
        "ingredient_details": feature_details,
        "feature_details": feature_details,
        "ingredient_count": len(features),
        "highlight_ingredient": highlight,
        "highlight_feature": highlight,
        "concentration": product.concentration
    }
