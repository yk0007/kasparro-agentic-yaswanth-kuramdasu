"""
Usage Logic Block.

Pure functions for transforming product usage instructions into structured content.
"""

from typing import Dict, List, Any
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ProductModel


def generate_usage_block(product: ProductModel) -> Dict[str, Any]:
    """
    Transform product usage instructions into structured content.
    
    This block parses the usage instructions and extracts:
    - Step-by-step application guide
    - Recommended frequency
    - Best time to use
    - Usage tips
    
    Args:
        product: Validated ProductModel containing usage data
        
    Returns:
        Dictionary containing:
            - steps: List of application steps
            - frequency: How often to use
            - best_time: Optimal time of day
            - tips: Additional usage tips
            - warnings: Any usage warnings
            
    Example:
        >>> product = ProductModel(...)
        >>> result = generate_usage_block(product)
        >>> result["frequency"]
        "Daily"
    """
    # Parse the usage instructions
    usage_text = product.how_to_use
    
    # Extract steps from usage text
    steps: List[Dict[str, str]] = _parse_usage_steps(usage_text, product)
    
    # Determine frequency
    frequency: str = _extract_frequency(usage_text)
    
    # Determine best time
    best_time: str = _extract_best_time(usage_text)
    
    # Generate tips based on product type
    tips: List[str] = _generate_usage_tips(product)
    
    # Extract any warnings
    warnings: List[str] = _generate_warnings(product)
    
    return {
        "steps": steps,
        "frequency": frequency,
        "best_time": best_time,
        "tips": tips,
        "warnings": warnings,
        "raw_instructions": usage_text
    }


def _parse_usage_steps(usage_text: str, product: ProductModel) -> List[Dict[str, str]]:
    """
    Parse usage text into structured steps.
    
    Args:
        usage_text: Raw usage instructions
        product: Product model for context
        
    Returns:
        List of step dictionaries
    """
    steps = []
    
    # Check if instructions mention drops
    if "drop" in usage_text.lower():
        steps.append({
            "step_number": 1,
            "action": "Cleanse",
            "description": "Start with a clean, dry face"
        })
        steps.append({
            "step_number": 2,
            "action": "Apply",
            "description": usage_text
        })
        steps.append({
            "step_number": 3,
            "action": "Wait",
            "description": "Allow the serum to absorb for 1-2 minutes"
        })
        
        # Check for follow-up products
        if "sunscreen" in usage_text.lower():
            steps.append({
                "step_number": 4,
                "action": "Protect",
                "description": "Follow with sunscreen for daytime use"
            })
    else:
        # Generic steps
        steps.append({
            "step_number": 1,
            "action": "Prepare",
            "description": "Cleanse and dry your face"
        })
        steps.append({
            "step_number": 2,
            "action": "Apply",
            "description": usage_text
        })
    
    return steps


def _extract_frequency(usage_text: str) -> str:
    """Extract usage frequency from instructions."""
    usage_lower = usage_text.lower()
    
    if "twice" in usage_lower or "2x" in usage_lower:
        return "Twice daily"
    elif "morning" in usage_lower and "night" in usage_lower:
        return "Twice daily (AM & PM)"
    elif "morning" in usage_lower:
        return "Once daily (Morning)"
    elif "night" in usage_lower or "evening" in usage_lower:
        return "Once daily (Evening)"
    elif "daily" in usage_lower:
        return "Daily"
    else:
        return "As directed"


def _extract_best_time(usage_text: str) -> str:
    """Extract best time to use from instructions."""
    usage_lower = usage_text.lower()
    
    if "morning" in usage_lower:
        return "Morning"
    elif "night" in usage_lower or "evening" in usage_lower:
        return "Evening"
    elif "before bed" in usage_lower:
        return "Before bed"
    else:
        return "Morning or Evening"


def _generate_usage_tips(product: ProductModel) -> List[str]:
    """Generate usage tips based on product characteristics."""
    tips = []
    
    # Tips based on ingredients
    if "Vitamin C" in product.key_ingredients:
        tips.append("Store in a cool, dark place to maintain potency")
        tips.append("Can be layered under other serums and moisturizers")
    
    if "Hyaluronic Acid" in product.key_ingredients:
        tips.append("Apply to slightly damp skin for best absorption")
    
    # Tips based on skin type
    if "Oily" in product.skin_type:
        tips.append("May be used alone as a light hydrator for oily skin")
    
    if "Sensitive" in product.skin_type or "sensitive" in product.side_effects.lower():
        tips.append("Patch test recommended before first use")
    
    # General tips
    tips.append("Consistency is key for best results")
    
    return tips


def _generate_warnings(product: ProductModel) -> List[str]:
    """Generate warnings based on product characteristics."""
    warnings = []
    
    if product.side_effects:
        warnings.append(product.side_effects)
    
    if "Vitamin C" in product.key_ingredients:
        warnings.append("May increase sun sensitivity; always use sunscreen")
    
    return warnings
