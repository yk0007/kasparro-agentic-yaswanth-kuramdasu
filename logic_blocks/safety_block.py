"""
Safety Logic Block.

Pure functions for generating safety information from product data.
"""

from typing import Dict, List, Any
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ProductModel


def generate_safety_block(product: ProductModel) -> Dict[str, Any]:
    """
    Generate comprehensive safety information from product data.
    
    This block creates structured safety content including:
    - Side effects (from product data)
    - Precautions and warnings
    - Suitability information
    
    Args:
        product: Validated ProductModel containing safety-related data
        
    Returns:
        Dictionary containing:
            - side_effects: List of potential side effects
            - precautions: Safety precautions
            - suitability: Skin type suitability info
            - contraindications: Who should avoid the product
            - storage: Storage recommendations
            
    Example:
        >>> product = ProductModel(...)
        >>> result = generate_safety_block(product)
        >>> result["side_effects"]
        ["Mild tingling for sensitive skin"]
    """
    # Extract side effects
    side_effects: List[str] = _parse_side_effects(product.side_effects)
    
    # Generate precautions based on product characteristics
    precautions: List[str] = _generate_precautions(product)
    
    # Build suitability information
    suitability: Dict[str, Any] = _build_suitability(product)
    
    # Determine contraindications
    contraindications: List[str] = _get_contraindications(product)
    
    # Storage recommendations
    storage: List[str] = _get_storage_recommendations(product)
    
    return {
        "side_effects": side_effects,
        "precautions": precautions,
        "suitability": suitability,
        "contraindications": contraindications,
        "storage": storage,
        "overall_safety_rating": _calculate_safety_rating(product)
    }


def _parse_side_effects(side_effects_text: str) -> List[str]:
    """
    Parse side effects text into a list of individual effects.
    
    Args:
        side_effects_text: Raw side effects string
        
    Returns:
        List of side effect strings
    """
    if not side_effects_text:
        return []
    
    # Split by common delimiters
    effects = []
    
    # Check for comma-separated effects
    if "," in side_effects_text:
        effects = [e.strip() for e in side_effects_text.split(",")]
    elif ";" in side_effects_text:
        effects = [e.strip() for e in side_effects_text.split(";")]
    else:
        effects = [side_effects_text.strip()]
    
    return [e for e in effects if e]


def _generate_precautions(product: ProductModel) -> List[str]:
    """
    Generate precautions based on product ingredients and characteristics.
    
    Args:
        product: Product model
        
    Returns:
        List of precaution strings
    """
    precautions = []
    
    # Precautions based on ingredients
    if "Vitamin C" in product.key_ingredients:
        precautions.append("Avoid use with benzoyl peroxide as it may reduce effectiveness")
        precautions.append("Apply sunscreen during daytime use as Vitamin C may increase photosensitivity")
    
    if "Retinol" in product.key_ingredients:
        precautions.append("Start with every other day use and gradually increase frequency")
        precautions.append("Avoid use during pregnancy")
    
    if "AHA" in str(product.key_ingredients) or "Glycolic" in str(product.key_ingredients):
        precautions.append("Increases sun sensitivity - sunscreen is essential")
    
    # General precautions
    precautions.append("Perform a patch test before first use")
    precautions.append("Discontinue use if irritation occurs")
    precautions.append("For external use only")
    
    return precautions


def _build_suitability(product: ProductModel) -> Dict[str, Any]:
    """
    Build suitability information from product data.
    
    Args:
        product: Product model
        
    Returns:
        Dictionary with suitability information
    """
    # Determine who the product is suitable for
    suitable_for = product.skin_type.copy()
    
    # Determine who should use with caution
    use_with_caution = []
    if "sensitive" in product.side_effects.lower():
        use_with_caution.append("Sensitive skin (patch test first)")
    
    # Not suitable for (based on ingredients)
    not_suitable_for = []
    if "Retinol" in product.key_ingredients:
        not_suitable_for.append("Pregnant or nursing women")
    
    return {
        "suitable_for": suitable_for,
        "use_with_caution": use_with_caution,
        "not_suitable_for": not_suitable_for,
        "all_skin_types": len(product.skin_type) >= 3
    }


def _get_contraindications(product: ProductModel) -> List[str]:
    """
    Get contraindications based on product characteristics.
    
    Args:
        product: Product model
        
    Returns:
        List of contraindication strings
    """
    contraindications = []
    
    if "Retinol" in product.key_ingredients:
        contraindications.append("Pregnancy and breastfeeding")
    
    contraindications.append("Open wounds or broken skin")
    contraindications.append("Known allergy to any ingredient")
    
    return contraindications


def _get_storage_recommendations(product: ProductModel) -> List[str]:
    """
    Get storage recommendations based on ingredients.
    
    Args:
        product: Product model
        
    Returns:
        List of storage recommendation strings
    """
    storage = []
    
    if "Vitamin C" in product.key_ingredients:
        storage.append("Store in a cool, dark place")
        storage.append("Keep away from direct sunlight")
        storage.append("Refrigeration recommended for extended freshness")
    else:
        storage.append("Store at room temperature")
        storage.append("Keep away from direct sunlight")
    
    storage.append("Keep out of reach of children")
    
    return storage


def _calculate_safety_rating(product: ProductModel) -> str:
    """
    Calculate an overall safety rating based on product characteristics.
    
    Args:
        product: Product model
        
    Returns:
        Safety rating string
    """
    # Simple heuristic based on side effects and ingredients
    side_effects_lower = product.side_effects.lower()
    
    if "severe" in side_effects_lower or "serious" in side_effects_lower:
        return "Use with caution"
    elif "mild" in side_effects_lower or "slight" in side_effects_lower:
        return "Generally safe for most users"
    else:
        return "Safe for recommended use"
