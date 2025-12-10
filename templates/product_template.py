"""
Product Page Template for Content Generation.

Defines the structure and validation for product page content.
"""

from typing import Dict, List, Any
from templates.base_template import BaseTemplate


class ProductTemplate(BaseTemplate):
    """
    Template for product page content.
    
    Creates a comprehensive product page with all product information
    organized for display: features, benefits, ingredients, usage, and safety.
    """
    
    template_type: str = "product"
    required_fields: List[str] = ["product"]
    optional_fields: List[str] = ["tagline", "headline"]
    required_blocks: List[str] = [
        "benefits_block", 
        "usage_block", 
        "ingredients_block", 
        "safety_block"
    ]
    
    def _validate_specific(self, data: Dict[str, Any]) -> None:
        """
        Validate product page-specific requirements.
        
        - Validates product structure
        - Checks for required product fields
        
        Args:
            data: Dictionary of content data
        """
        if "product" not in data:
            return  # Already caught by required fields check
        
        product = data["product"]
        
        if not isinstance(product, dict):
            self._errors.append("product must be a dictionary")
            return
        
        # Check required product fields
        required_product_fields = ["name", "benefits", "ingredients"]
        for field in required_product_fields:
            if field not in product:
                self._warnings.append(f"product is missing recommended field: {field}")
    
    def _render_structure(
        self, 
        data: Dict[str, Any], 
        blocks: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build the product page output structure.
        
        Combines raw product data with enriched logic block outputs.
        
        Args:
            data: Dictionary of content data
            blocks: Dictionary of logic block outputs
            
        Returns:
            Rendered product page content dictionary
        """
        product_data = data["product"]
        
        # Build comprehensive product structure
        product = {
            "name": product_data.get("name", ""),
            "tagline": data.get("tagline", self._generate_tagline(product_data)),
            "headline": data.get("headline", self._generate_headline(product_data)),
            "description": self._generate_description(product_data, blocks),
            
            # From product data
            "key_features": self._extract_key_features(product_data),
            
            # From ingredients block
            "ingredients": blocks.get("ingredients_block", {
                "active": product_data.get("key_ingredients", []),
                "details": {}
            }),
            
            # From benefits block  
            "benefits": blocks.get("benefits_block", {
                "primary": product_data.get("benefits", []),
                "detailed": []
            }),
            
            # From usage block
            "how_to_use": blocks.get("usage_block", {
                "steps": [],
                "frequency": "",
                "best_time": ""
            }),
            
            # Skin type suitability
            "suitable_for": product_data.get("skin_type", []),
            
            # From safety block
            "safety_information": blocks.get("safety_block", {
                "side_effects": product_data.get("side_effects", ""),
                "precautions": []
            }),
            
            # Pricing
            "price": {
                "amount": product_data.get("price", ""),
                "currency": self._extract_currency(product_data.get("price", ""))
            }
        }
        
        return {
            "page_type": self.template_type,
            "product": product
        }
    
    def _generate_tagline(self, product: Dict[str, Any]) -> str:
        """Generate a tagline from product data."""
        benefits = product.get("benefits", [])
        if benefits:
            return f"Unlock {benefits[0].lower()} with every drop"
        return "Transform your skin care routine"
    
    def _generate_headline(self, product: Dict[str, Any]) -> str:
        """Generate a headline from product data."""
        name = product.get("name", "Product")
        concentration = product.get("concentration", "")
        if concentration:
            return f"{name} - {concentration} Power"
        return name
    
    def _generate_description(
        self, 
        product: Dict[str, Any], 
        blocks: Dict[str, Any]
    ) -> str:
        """Generate product description from data and blocks."""
        name = product.get("name", "This product")
        concentration = product.get("concentration", "")
        benefits = product.get("benefits", [])
        skin_types = product.get("skin_type", [])
        
        parts = [f"{name}"]
        if concentration:
            parts.append(f"features {concentration}")
        if benefits:
            parts.append(f"to deliver {' and '.join(b.lower() for b in benefits)}")
        if skin_types:
            parts.append(f"Perfect for {' and '.join(skin_types).lower()} skin types.")
        
        return ". ".join(parts)
    
    def _extract_key_features(self, product: Dict[str, Any]) -> List[str]:
        """Extract key features from product data."""
        features = []
        
        if product.get("concentration"):
            features.append(product["concentration"])
        
        if product.get("key_ingredients"):
            for ing in product["key_ingredients"]:
                features.append(f"Contains {ing}")
        
        if product.get("benefits"):
            for benefit in product["benefits"]:
                features.append(benefit)
        
        return features
    
    def _extract_currency(self, price: str) -> str:
        """Extract currency from price string."""
        if "₹" in price:
            return "INR"
        elif "$" in price:
            return "USD"
        elif "€" in price:
            return "EUR"
        return "INR"
