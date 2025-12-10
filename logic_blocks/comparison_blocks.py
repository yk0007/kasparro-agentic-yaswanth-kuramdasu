"""
Comparison Logic Blocks.

Pure functions for comparing products and generating structured comparison content.
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
    Compare ingredients between two products.
    
    Analyzes common ingredients, unique ingredients to each product,
    and provides an overall comparison analysis.
    
    Args:
        product_a: First product (typically the input product)
        product_b: Second product (typically fictional competitor)
        
    Returns:
        Dictionary containing:
            - common: Ingredients in both products
            - unique_to_product_a: Ingredients only in product A
            - unique_to_product_b: Ingredients only in product B
            - analysis: Text analysis of the comparison
            
    Example:
        >>> result = compare_ingredients_block(product_a, product_b)
        >>> result["common"]
        ["Vitamin C"]
    """
    ingredients_a = set(product_a.key_ingredients)
    ingredients_b = set(product_b.key_ingredients)
    
    common = list(ingredients_a & ingredients_b)
    unique_a = list(ingredients_a - ingredients_b)
    unique_b = list(ingredients_b - ingredients_a)
    
    # Generate analysis text
    analysis = _generate_ingredients_analysis(
        common, unique_a, unique_b, product_a, product_b
    )
    
    return {
        "common": common,
        "unique_to_product_a": unique_a,
        "unique_to_product_b": unique_b,
        "total_ingredients_a": len(ingredients_a),
        "total_ingredients_b": len(ingredients_b),
        "overlap_percentage": _calculate_overlap(ingredients_a, ingredients_b),
        "analysis": analysis
    }


def compare_benefits_block(
    product_a: ProductModel, 
    product_b: ProductModel
) -> Dict[str, Any]:
    """
    Compare benefits between two products.
    
    Analyzes common benefits, unique benefits to each product,
    and provides an overall comparison.
    
    Args:
        product_a: First product
        product_b: Second product
        
    Returns:
        Dictionary containing:
            - common: Benefits in both products
            - unique_to_product_a: Benefits only in product A
            - unique_to_product_b: Benefits only in product B
            - advantage_product_a: Product A's key advantages
            - advantage_product_b: Product B's key advantages
            - analysis: Text analysis
    """
    benefits_a = set(b.lower() for b in product_a.benefits)
    benefits_b = set(b.lower() for b in product_b.benefits)
    
    # Find common and unique (case-insensitive comparison)
    common_lower = benefits_a & benefits_b
    unique_a_lower = benefits_a - benefits_b
    unique_b_lower = benefits_b - benefits_a
    
    # Map back to original casing
    common = [b for b in product_a.benefits if b.lower() in common_lower]
    unique_a = [b for b in product_a.benefits if b.lower() in unique_a_lower]
    unique_b = [b for b in product_b.benefits if b.lower() in unique_b_lower]
    
    # Determine advantages
    advantage_a = _determine_advantages(product_a, unique_a)
    advantage_b = _determine_advantages(product_b, unique_b)
    
    analysis = _generate_benefits_analysis(
        product_a, product_b, common, unique_a, unique_b
    )
    
    return {
        "common": common,
        "unique_to_product_a": unique_a,
        "unique_to_product_b": unique_b,
        "advantage_product_a": advantage_a,
        "advantage_product_b": advantage_b,
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
    
    Analyzes price difference and provides value analysis.
    
    Args:
        product_a: First product
        product_b: Second product
        
    Returns:
        Dictionary containing:
            - price_a: Product A price
            - price_b: Product B price
            - difference: Price difference
            - cheaper_product: Which product is cheaper
            - value_analysis: Analysis of value proposition
    """
    price_a = product_a.price
    price_b = product_b.price
    
    # Extract numeric values
    price_a_num = _extract_price_value(price_a)
    price_b_num = _extract_price_value(price_b)
    
    difference = abs(price_a_num - price_b_num)
    currency = "₹" if "₹" in price_a else "$"
    
    cheaper = product_a.name if price_a_num < price_b_num else product_b.name
    more_expensive = product_b.name if price_a_num < price_b_num else product_a.name
    
    value_analysis = _generate_value_analysis(
        product_a, product_b, price_a_num, price_b_num
    )
    
    return {
        "price_a": price_a,
        "price_b": price_b,
        "price_a_numeric": price_a_num,
        "price_b_numeric": price_b_num,
        "difference": f"{currency}{difference}",
        "difference_numeric": difference,
        "cheaper_product": cheaper,
        "more_expensive_product": more_expensive,
        "percentage_difference": _calculate_percentage_diff(price_a_num, price_b_num),
        "value_analysis": value_analysis
    }


def _extract_price_value(price: str) -> float:
    """Extract numeric value from price string."""
    # Remove currency symbols and whitespace
    cleaned = price.replace("₹", "").replace("$", "").replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def _calculate_overlap(set_a: set, set_b: set) -> float:
    """Calculate percentage overlap between two sets."""
    if not set_a or not set_b:
        return 0.0
    union = len(set_a | set_b)
    intersection = len(set_a & set_b)
    return round((intersection / union) * 100, 1) if union > 0 else 0.0


def _calculate_percentage_diff(price_a: float, price_b: float) -> str:
    """Calculate percentage price difference."""
    if price_a == 0 or price_b == 0:
        return "N/A"
    
    diff = abs(price_a - price_b)
    base = min(price_a, price_b)
    percentage = (diff / base) * 100
    
    return f"{round(percentage, 1)}%"


def _generate_ingredients_analysis(
    common: List[str],
    unique_a: List[str],
    unique_b: List[str],
    product_a: ProductModel,
    product_b: ProductModel
) -> str:
    """Generate text analysis of ingredient comparison."""
    parts = []
    
    if common:
        parts.append(f"Both products share {len(common)} key ingredient(s): {', '.join(common)}.")
    
    if unique_a:
        parts.append(f"{product_a.name} uniquely features: {', '.join(unique_a)}.")
    
    if unique_b:
        parts.append(f"{product_b.name} uniquely features: {', '.join(unique_b)}.")
    
    if not common:
        parts.append("The products have distinct formulations with no overlapping key ingredients.")
    
    return " ".join(parts)


def _generate_benefits_analysis(
    product_a: ProductModel,
    product_b: ProductModel,
    common: List[str],
    unique_a: List[str],
    unique_b: List[str]
) -> str:
    """Generate text analysis of benefits comparison."""
    parts = []
    
    if common:
        parts.append(f"Both serums offer {', '.join(common).lower()} benefits.")
    
    if unique_a:
        parts.append(f"{product_a.name} additionally provides {', '.join(unique_a).lower()}.")
    
    if unique_b:
        parts.append(f"{product_b.name} additionally offers {', '.join(unique_b).lower()}.")
    
    return " ".join(parts) if parts else "Both products target similar skin concerns."


def _determine_advantages(product: ProductModel, unique_benefits: List[str]) -> List[str]:
    """Determine key advantages based on unique benefits."""
    advantages = []
    
    for benefit in unique_benefits:
        benefit_lower = benefit.lower()
        if "anti" in benefit_lower and "aging" in benefit_lower:
            advantages.append("Anti-aging focus")
        elif "hydrat" in benefit_lower:
            advantages.append("Enhanced hydration")
        elif "bright" in benefit_lower:
            advantages.append("Brightening power")
        else:
            advantages.append(benefit)
    
    return advantages


def _generate_value_analysis(
    product_a: ProductModel,
    product_b: ProductModel,
    price_a: float,
    price_b: float
) -> str:
    """Generate value analysis text."""
    if price_a == price_b:
        return "Both products are priced equally. Choice should be based on specific skin needs and ingredient preferences."
    
    cheaper = product_a if price_a < price_b else product_b
    expensive = product_b if price_a < price_b else product_a
    diff = abs(price_a - price_b)
    
    return (
        f"{cheaper.name} offers a more budget-friendly option at a ₹{diff} savings. "
        f"{expensive.name} is positioned as a premium alternative with "
        f"{len(expensive.key_ingredients)} key ingredients."
    )
