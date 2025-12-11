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
        
        Pass-through the product data built by ProductPageAgent.
        
        Args:
            data: Dictionary of content data (built by agent)
            blocks: Dictionary of logic block outputs
            
        Returns:
            Rendered product page content dictionary
        """
        product_data = data.get("product", {})
        
        # Pass-through the agent-built structure
        return {
            "page_type": self.template_type,
            "product": {
                "name": product_data.get("name", ""),
                "tagline": product_data.get("tagline", ""),
                "headline": product_data.get("headline", ""),
                "description": product_data.get("description", ""),
                "product_type": product_data.get("product_type", ""),
                "key_features": product_data.get("key_features", []),
                "ingredients": product_data.get("ingredients", {}),
                "benefits": product_data.get("benefits", {}),
                "how_to_use": product_data.get("how_to_use", {}),
                "suitable_for": product_data.get("suitable_for", []),
                "safety_information": product_data.get("safety_information", {}),
                "price": product_data.get("price", {})
            }
        }
    
    def _generate_tagline(self, product: Dict[str, Any]) -> str:
        """Generate a tagline from product data."""
        benefits = product.get("benefits", [])
        if benefits:
            return f"Experience {benefits[0].lower()} like never before"
        return "Discover the difference"
    
    def _generate_headline(self, product: Dict[str, Any]) -> str:
        """Generate a headline from product data."""
        name = product.get("name", "Product")
        concentration = product.get("product_type", "")
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
        concentration = product.get("product_type", "")
        benefits = product.get("benefits", [])
        target_users = product.get("target_users", product.get("target_users", []))
        
        parts = [f"{name}"]
        if concentration:
            parts.append(f"features {concentration}")
        if benefits:
            parts.append(f"to deliver {' and '.join(b.lower() for b in benefits)}")
        if target_users:
            parts.append(f"Perfect for {' and '.join(target_users).lower()}.")
        
        return ". ".join(parts)
    
    def _extract_key_features(self, product: Dict[str, Any]) -> List[str]:
        """Extract key features from product data."""
        features = []
        
        if product.get("product_type"):
            features.append(product["product_type"])
        
        if product.get("key_features"):
            for ing in product["key_features"]:
                features.append(f"Includes {ing}")
        
        if product.get("benefits"):
            for benefit in product["benefits"]:
                features.append(benefit)
        
        return features
    
    def _extract_currency(self, price: str) -> str:
        """
        Extract currency code from price string.
        
        Uses a mapping of currency symbols to ISO codes for better 
        internationalization support.
        
        Args:
            price: Price string potentially containing currency symbol
            
        Returns:
            ISO currency code (default: currency detected or 'USD')
        """
        import re
        
        # Currency symbol to ISO code mapping (extensible)
        CURRENCY_MAP = {
            "₹": "INR",
            "$": "USD", 
            "€": "EUR",
            "£": "GBP",
            "¥": "JPY",
            "₩": "KRW",
            "฿": "THB",
            "₽": "RUB",
            "R": "ZAR",  # South African Rand
            "kr": "SEK",  # Swedish Krona
        }
        
        # Try to match currency symbols
        for symbol, code in CURRENCY_MAP.items():
            if symbol in price:
                return code
        
        # Try regex for currency codes like USD, INR, EUR
        iso_match = re.search(r'\b(USD|INR|EUR|GBP|JPY|CAD|AUD)\b', price.upper())
        if iso_match:
            return iso_match.group(1)
        
        # Default to USD if no currency detected
        return "USD"
