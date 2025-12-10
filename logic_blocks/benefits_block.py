"""
Benefits Logic Block.

Pure functions for transforming product benefits into structured content.
Works with any product type (tech, fashion, skincare, etc.)
"""

from typing import Dict, List, Any
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ProductModel


def generate_benefits_block(product: ProductModel) -> Dict[str, Any]:
    """
    Transform product benefits into structured content.
    
    Generic implementation that works with any product type.
    
    Args:
        product: Validated ProductModel containing benefits data
        
    Returns:
        Dictionary containing structured benefits data
    """
    primary_benefits: List[str] = product.benefits.copy()
    
    # Generate detailed benefits (generic - no domain-specific content)
    detailed_benefits: List[Dict[str, str]] = []
    for benefit in primary_benefits:
        detailed_benefits.append({
            "benefit": benefit,
            "description": f"{product.name} provides {benefit.lower()}."
        })
    
    return {
        "primary_benefits": primary_benefits,
        "detailed_benefits": detailed_benefits,
        "total_benefits": len(primary_benefits)
    }
