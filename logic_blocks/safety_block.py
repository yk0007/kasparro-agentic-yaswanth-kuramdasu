"""
Safety Logic Block.

Pure functions for transforming product safety/limitations info into structured content.
Works with any product type (tech, fashion, skincare, etc.)
"""

from typing import Dict, List, Any
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ProductModel


def generate_safety_block(product: ProductModel) -> Dict[str, Any]:
    """
    Transform product safety/side effects info into structured content.
    
    Generic implementation that works with any product type.
    For non-skincare products, this represents limitations or considerations.
    
    Args:
        product: Validated ProductModel containing side_effects data
        
    Returns:
        Dictionary containing structured safety/considerations data
    """
    side_effects: str = product.side_effects
    target_users: List[str] = product.skin_type.copy()  # skin_type = target users
    
    return {
        "side_effects": side_effects,
        "considerations": side_effects,
        "limitations": side_effects,
        "target_users": target_users,
        "suitable_for": target_users,
        "product_name": product.name
    }
