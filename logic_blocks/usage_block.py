"""
Usage Logic Block.

Pure functions for transforming product usage instructions into structured content.
Works with any product type (tech, fashion, skincare, etc.)
"""

from typing import Dict, List, Any
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ProductModel


def generate_usage_block(product: ProductModel) -> Dict[str, Any]:
    """
    Transform product usage instructions into structured content.
    
    Generic implementation that works with any product type.
    
    Args:
        product: Validated ProductModel containing how_to_use data
        
    Returns:
        Dictionary containing structured usage data
    """
    raw_usage: str = product.how_to_use
    
    return {
        "raw_instructions": raw_usage,
        "summary": raw_usage,
        "product_name": product.name
    }
