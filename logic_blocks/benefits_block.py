"""
Benefits Logic Block.

Pure functions for transforming product benefits into structured content.
"""

from typing import Dict, List, Any
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ProductModel


def generate_benefits_block(product: ProductModel) -> Dict[str, Any]:
    """
    Transform product benefits into structured content.
    
    This block extracts and organizes benefits data from the product
    into a format suitable for content generation.
    
    Args:
        product: Validated ProductModel containing benefits data
        
    Returns:
        Dictionary containing:
            - primary_benefits: List of main product benefits
            - detailed_benefits: Expanded benefit descriptions
            - benefit_categories: Benefits grouped by type
            
    Example:
        >>> product = ProductModel(...)
        >>> result = generate_benefits_block(product)
        >>> result["primary_benefits"]
        ["Brightening", "Fades dark spots"]
    """
    # Extract primary benefits directly from product
    primary_benefits: List[str] = product.benefits.copy()
    
    # Generate detailed benefit descriptions
    detailed_benefits: List[Dict[str, str]] = []
    for benefit in primary_benefits:
        detailed_benefits.append({
            "benefit": benefit,
            "description": _expand_benefit_description(benefit, product)
        })
    
    # Categorize benefits
    benefit_categories: Dict[str, List[str]] = _categorize_benefits(primary_benefits)
    
    return {
        "primary_benefits": primary_benefits,
        "detailed_benefits": detailed_benefits,
        "benefit_categories": benefit_categories,
        "total_benefits": len(primary_benefits)
    }


def _expand_benefit_description(benefit: str, product: ProductModel) -> str:
    """
    Expand a benefit into a detailed description using product data.
    
    Args:
        benefit: The benefit to expand
        product: Product model for context
        
    Returns:
        Expanded description string
    """
    # Map common benefits to descriptions using product context
    benefit_lower = benefit.lower()
    
    if "brightening" in benefit_lower:
        return f"The {product.concentration} in {product.name} helps brighten skin tone and enhance natural radiance."
    elif "dark spot" in benefit_lower or "fades" in benefit_lower:
        return f"{product.name} works to fade dark spots and hyperpigmentation over consistent use."
    elif "hydrat" in benefit_lower:
        return f"With Hyaluronic Acid, {product.name} provides deep hydration for plump, healthy skin."
    elif "anti-aging" in benefit_lower or "wrinkle" in benefit_lower:
        return f"{product.name} helps reduce fine lines and wrinkles with its potent antioxidant formula."
    else:
        return f"{product.name} delivers {benefit.lower()} benefits for improved skin health."


def _categorize_benefits(benefits: List[str]) -> Dict[str, List[str]]:
    """
    Categorize benefits by their type.
    
    Args:
        benefits: List of benefit strings
        
    Returns:
        Dictionary with categories as keys and benefit lists as values
    """
    categories: Dict[str, List[str]] = {
        "appearance": [],
        "skin_health": [],
        "protection": [],
        "other": []
    }
    
    for benefit in benefits:
        benefit_lower = benefit.lower()
        if any(word in benefit_lower for word in ["brightening", "glow", "radiant", "dark spot", "fades", "tone"]):
            categories["appearance"].append(benefit)
        elif any(word in benefit_lower for word in ["hydrat", "moistur", "nourish", "soft", "smooth"]):
            categories["skin_health"].append(benefit)
        elif any(word in benefit_lower for word in ["protect", "antioxidant", "uv", "barrier"]):
            categories["protection"].append(benefit)
        else:
            categories["other"].append(benefit)
    
    # Remove empty categories
    return {k: v for k, v in categories.items() if v}
