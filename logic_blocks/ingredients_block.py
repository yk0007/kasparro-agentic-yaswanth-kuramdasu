"""
Ingredients Logic Block.

Pure functions for transforming product ingredients into structured content.
"""

from typing import Dict, List, Any
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ProductModel


# Knowledge base of common skincare ingredients (derived from product data patterns)
INGREDIENT_INFO: Dict[str, Dict[str, str]] = {
    "Vitamin C": {
        "type": "Active",
        "function": "Antioxidant",
        "description": "A powerful antioxidant that brightens skin, evens tone, and protects against environmental damage.",
        "benefits": "Brightening, anti-aging, antioxidant protection"
    },
    "Hyaluronic Acid": {
        "type": "Active",
        "function": "Humectant",
        "description": "A moisture-binding molecule that holds up to 1000x its weight in water for deep hydration.",
        "benefits": "Hydration, plumping, smoothing"
    },
    "Niacinamide": {
        "type": "Active",
        "function": "Vitamin B3",
        "description": "Helps minimize pores, even skin tone, and strengthen the skin barrier.",
        "benefits": "Pore minimizing, brightening, barrier repair"
    },
    "Retinol": {
        "type": "Active",
        "function": "Vitamin A derivative",
        "description": "Promotes cell turnover for smoother, younger-looking skin.",
        "benefits": "Anti-aging, texture improvement, cell renewal"
    },
    "Salicylic Acid": {
        "type": "Active",
        "function": "BHA",
        "description": "Oil-soluble acid that penetrates pores to clear congestion and prevent breakouts.",
        "benefits": "Exfoliation, acne control, pore clearing"
    },
    "Glycolic Acid": {
        "type": "Active",
        "function": "AHA",
        "description": "Water-soluble acid that exfoliates the skin surface for improved texture.",
        "benefits": "Exfoliation, brightening, texture improvement"
    }
}


def generate_ingredients_block(product: ProductModel) -> Dict[str, Any]:
    """
    Transform product ingredients into detailed structured content.
    
    This block enriches ingredient data with descriptions and categorization
    based on the product's key ingredients.
    
    Args:
        product: Validated ProductModel containing ingredients data
        
    Returns:
        Dictionary containing:
            - active_ingredients: List of active ingredient names
            - ingredient_details: Detailed info for each ingredient
            - ingredient_count: Total number of key ingredients
            - highlight_ingredient: The primary active ingredient
            
    Example:
        >>> product = ProductModel(...)
        >>> result = generate_ingredients_block(product)
        >>> result["highlight_ingredient"]
        "Vitamin C"
    """
    # Get the key ingredients list
    ingredients: List[str] = product.key_ingredients.copy()
    
    # Build detailed ingredient information
    ingredient_details: List[Dict[str, Any]] = []
    active_ingredients: List[str] = []
    
    for ingredient in ingredients:
        detail = _get_ingredient_detail(ingredient, product)
        ingredient_details.append(detail)
        
        if detail.get("type") == "Active":
            active_ingredients.append(ingredient)
    
    # Determine the highlight/hero ingredient (usually the first or highest concentration)
    highlight: str = _get_highlight_ingredient(ingredients, product)
    
    return {
        "active_ingredients": active_ingredients if active_ingredients else ingredients,
        "ingredient_details": ingredient_details,
        "ingredient_count": len(ingredients),
        "highlight_ingredient": highlight,
        "concentration": product.concentration
    }


def _get_ingredient_detail(ingredient: str, product: ProductModel) -> Dict[str, Any]:
    """
    Get detailed information for an ingredient.
    
    Args:
        ingredient: Ingredient name
        product: Product model for context
        
    Returns:
        Dictionary with ingredient details
    """
    # Check if we have info for this ingredient
    if ingredient in INGREDIENT_INFO:
        info = INGREDIENT_INFO[ingredient].copy()
        return {
            "name": ingredient,
            "type": info["type"],
            "function": info["function"],
            "description": info["description"],
            "benefits": info["benefits"]
        }
    
    # Generate generic info for unknown ingredients
    return {
        "name": ingredient,
        "type": "Supporting",
        "function": "Skin conditioning",
        "description": f"{ingredient} is a key component of {product.name} formulation.",
        "benefits": "Overall skin health"
    }


def _get_highlight_ingredient(ingredients: List[str], product: ProductModel) -> str:
    """
    Determine the highlight/hero ingredient.
    
    The highlight is typically:
    1. Mentioned in concentration
    2. First listed active ingredient
    3. First ingredient in the list
    
    Args:
        ingredients: List of ingredients
        product: Product model for context
        
    Returns:
        The highlight ingredient name
    """
    concentration_lower = product.concentration.lower()
    
    # Check if any ingredient is mentioned in concentration
    for ingredient in ingredients:
        if ingredient.lower() in concentration_lower:
            return ingredient
    
    # Return first active ingredient if available
    for ingredient in ingredients:
        if ingredient in INGREDIENT_INFO:
            return ingredient
    
    # Default to first ingredient
    return ingredients[0] if ingredients else ""
