"""
Comparison Logic Blocks.

Pure functions for comparing products and generating structured comparison content.
Works with any product type (tech, fashion, skincare, etc.)
"""

from typing import Dict, List, Any
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ProductModel


def compare_ingredients_block(
    product_a: ProductModel, 
    product_b: ProductModel
) -> Dict[str, Any]:
    """
    Compare key features/ingredients between two products.
    
    Args:
        product_a: First product
        product_b: Second product
        
    Returns:
        Dictionary with comparison data
    """
    features_a = set(product_a.key_ingredients)
    features_b = set(product_b.key_ingredients)
    
    common = list(features_a & features_b)
    unique_a = list(features_a - features_b)
    unique_b = list(features_b - features_a)
    
    # Generate analysis
    parts = []
    if common:
        parts.append(f"Both products share: {', '.join(common)}.")
    if unique_a:
        parts.append(f"{product_a.name} uniquely offers: {', '.join(unique_a)}.")
    if unique_b:
        parts.append(f"{product_b.name} uniquely offers: {', '.join(unique_b)}.")
    
    analysis = " ".join(parts) if parts else "Products have different feature sets."
    
    return {
        "common": common,
        "unique_to_product_a": unique_a,
        "unique_to_product_b": unique_b,
        "total_ingredients_a": len(features_a),
        "total_ingredients_b": len(features_b),
        "analysis": analysis
    }


def compare_benefits_block(
    product_a: ProductModel, 
    product_b: ProductModel
) -> Dict[str, Any]:
    """
    Compare benefits between two products.
    
    Args:
        product_a: First product
        product_b: Second product
        
    Returns:
        Dictionary with benefits comparison data
    """
    benefits_a = set(b.lower() for b in product_a.benefits)
    benefits_b = set(b.lower() for b in product_b.benefits)
    
    common_lower = benefits_a & benefits_b
    unique_a_lower = benefits_a - benefits_b
    unique_b_lower = benefits_b - benefits_a
    
    common = [b for b in product_a.benefits if b.lower() in common_lower]
    unique_a = [b for b in product_a.benefits if b.lower() in unique_a_lower]
    unique_b = [b for b in product_b.benefits if b.lower() in unique_b_lower]
    
    # Generate analysis
    parts = []
    if common:
        parts.append(f"Both products offer: {', '.join(common)}.")
    if unique_a:
        parts.append(f"{product_a.name} additionally provides: {', '.join(unique_a)}.")
    if unique_b:
        parts.append(f"{product_b.name} additionally provides: {', '.join(unique_b)}.")
    
    analysis = " ".join(parts) if parts else "Both products target similar needs."
    
    return {
        "common": common,
        "unique_to_product_a": unique_a,
        "unique_to_product_b": unique_b,
        "advantage_product_a": unique_a,
        "advantage_product_b": unique_b,
        "total_benefits_a": len(product_a.benefits),
        "total_benefits_b": len(product_b.benefits),
        "analysis": analysis
    }


def generate_pricing_block(
    product_a: ProductModel, 
    product_b: ProductModel
) -> Dict[str, Any]:
    """
    Compare pricing between two products.
    
    Args:
        product_a: First product
        product_b: Second product
        
    Returns:
        Dictionary with pricing comparison data
    """
    price_a = product_a.price
    price_b = product_b.price
    
    # Extract numeric values
    price_a_num = _extract_price_value(price_a)
    price_b_num = _extract_price_value(price_b)
    
    difference = abs(price_a_num - price_b_num)
    
    if price_a_num == 0 and price_b_num == 0:
        cheaper = "N/A"
        value_analysis = "Pricing comparison not available."
    elif price_a_num <= price_b_num:
        cheaper = product_a.name
        value_analysis = f"{product_a.name} is more budget-friendly."
    else:
        cheaper = product_b.name
        value_analysis = f"{product_b.name} is more budget-friendly."
    
    return {
        "price_a": price_a,
        "price_b": price_b,
        "price_a_numeric": price_a_num,
        "price_b_numeric": price_b_num,
        "difference_numeric": difference,
        "cheaper_product": cheaper,
        "value_analysis": value_analysis
    }


def _extract_price_value(price: str) -> float:
    """Extract numeric value from price string."""
    import re
    numbers = re.findall(r'[\d.]+', price.replace(',', ''))
    if numbers:
        try:
            return float(numbers[0])
        except ValueError:
            return 0.0
    return 0.0
