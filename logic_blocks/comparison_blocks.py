"""
Comparison Logic Blocks.

Functions for comparing products using LLM.
"""

from typing import Dict, List, Any
import re
import logging


from models import ProductModel
from config import invoke_with_retry

logger = logging.getLogger(__name__)


def compare_ingredients_block(product_a: ProductModel, product_b: ProductModel) -> Dict[str, Any]:
    """Compare key features between two products."""
    features_a = set(product_a.key_features)
    features_b = set(product_b.key_features)
    
    common = list(features_a & features_b)
    unique_a = list(features_a - features_b)
    unique_b = list(features_b - features_a)
    
    try:
        prompt = f"""Compare features of "{product_a.name}" vs "{product_b.name}".
{product_a.name}: {', '.join(product_a.key_features)}
{product_b.name}: {', '.join(product_b.key_features)}
Write a brief 2-sentence comparison. Output ONLY the text."""

        analysis = invoke_with_retry(prompt).strip()
    except Exception as e:
        logger.warning(f"Comparison analysis failed: {e}")
        analysis = f"Both products offer distinct features for their target users."
    
    return {
        "common": common,
        "unique_to_product_a": unique_a,
        "unique_to_product_b": unique_b,
        "total_ingredients_a": len(features_a),
        "total_ingredients_b": len(features_b),
        "analysis": analysis
    }


def compare_benefits_block(product_a: ProductModel, product_b: ProductModel) -> Dict[str, Any]:
    """Compare benefits between two products."""
    benefits_a = set(b.lower() for b in product_a.benefits)
    benefits_b = set(b.lower() for b in product_b.benefits)
    
    common_lower = benefits_a & benefits_b
    unique_a = [b for b in product_a.benefits if b.lower() not in common_lower]
    unique_b = [b for b in product_b.benefits if b.lower() not in common_lower]
    common = [b for b in product_a.benefits if b.lower() in common_lower]
    
    try:
        prompt = f"""Compare benefits of "{product_a.name}" vs "{product_b.name}".
{product_a.name}: {', '.join(product_a.benefits)}
{product_b.name}: {', '.join(product_b.benefits)}
Write a brief 2-sentence comparison. Output ONLY the text."""

        analysis = invoke_with_retry(prompt).strip()
    except Exception as e:
        logger.warning(f"Benefits comparison failed: {e}")
        analysis = f"Both products target similar needs with different approaches."
    
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


def generate_pricing_block(product_a: ProductModel, product_b: ProductModel) -> Dict[str, Any]:
    """Compare pricing between two products using NormalizedPrice (no LLM call)."""
    from models import NormalizedPrice
    
    # B1: Use NormalizedPrice for robust price parsing
    price_a_norm = NormalizedPrice.from_string(product_a.price)
    price_b_norm = NormalizedPrice.from_string(product_b.price)
    
    price_a_num = float(price_a_norm.amount) if price_a_norm.amount else 0.0
    price_b_num = float(price_b_norm.amount) if price_b_norm.amount else 0.0
    
    difference = abs(price_a_num - price_b_num)
    
    if price_a_num <= price_b_num:
        cheaper = product_a.name
        analysis = f"{product_a.name} is more budget-friendly."
    else:
        cheaper = product_b.name
        analysis = f"{product_b.name} is more budget-friendly."
    
    return {
        # Comment 1: Backward-compatible price fields
        # Normalized objects for newer consumers
        "price_a": price_a_norm.model_dump(),
        "price_b": price_b_norm.model_dump(),
        # Raw strings for legacy consumers
        "price_a_raw": price_a_norm.original,
        "price_b_raw": price_b_norm.original,
        # Numeric fields for comparison logic
        "price_a_numeric": price_a_num,
        "price_b_numeric": price_b_num,
        "difference_numeric": difference,
        "cheaper_product": cheaper,
        "value_analysis": analysis
    }
