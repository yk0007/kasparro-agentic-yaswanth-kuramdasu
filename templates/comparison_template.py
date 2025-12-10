"""
Comparison Page Template for Content Generation.

Defines the structure and validation for comparison page content
between Product A (input) and Product B (fictional).
"""

from typing import Dict, List, Any
from templates.base_template import BaseTemplate


class ComparisonTemplate(BaseTemplate):
    """
    Template for comparison page content.
    
    Compares Product A (the input product) with Product B (a fictional 
    competitor generated using Gemini with grounding).
    """
    
    template_type: str = "comparison"
    required_fields: List[str] = ["products", "comparison"]
    optional_fields: List[str] = ["recommendation", "summary"]
    required_blocks: List[str] = [
        "compare_ingredients_block",
        "compare_benefits_block",
        "pricing_block"
    ]
    
    def _validate_specific(self, data: Dict[str, Any]) -> None:
        """
        Validate comparison page-specific requirements.
        
        - Validates both products exist
        - Validates comparison structure
        - Ensures Product B is properly structured
        
        Args:
            data: Dictionary of content data
        """
        if "products" in data:
            products = data["products"]
            
            if not isinstance(products, dict):
                self._errors.append("products must be a dictionary")
                return
            
            # Check both products exist
            if "product_a" not in products:
                self._errors.append("products must contain 'product_a'")
            if "product_b" not in products:
                self._errors.append("products must contain 'product_b'")
            
            # Validate Product B structure (fictional product)
            if "product_b" in products:
                product_b = products["product_b"]
                required_b_fields = ["name", "concentration", "key_ingredients", "benefits", "price"]
                for field in required_b_fields:
                    if field not in product_b or not product_b.get(field):
                        self._errors.append(
                            f"Product B must have '{field}' field (fictional but structured)"
                        )
        
        if "comparison" in data:
            comparison = data["comparison"]
            
            if not isinstance(comparison, dict):
                self._errors.append("comparison must be a dictionary")
                return
            
            # Check comparison has required sections
            recommended_sections = ["ingredients", "benefits", "price"]
            for section in recommended_sections:
                if section not in comparison:
                    self._warnings.append(
                        f"comparison is missing recommended section: {section}"
                    )
    
    def _render_structure(
        self, 
        data: Dict[str, Any], 
        blocks: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build the comparison page output structure.
        
        Combines product data with comparison logic block outputs.
        
        Args:
            data: Dictionary of content data
            blocks: Dictionary of logic block outputs
            
        Returns:
            Rendered comparison page content dictionary
        """
        products = data["products"]
        
        # Process Product A
        product_a = self._process_product(products.get("product_a", {}))
        
        # Process Product B
        product_b = self._process_product(products.get("product_b", {}))
        
        # Build comparison structure
        comparison = self._build_comparison(data, blocks)
        
        # Generate recommendation
        recommendation = data.get(
            "recommendation", 
            self._generate_recommendation(product_a, product_b, comparison)
        )
        
        return {
            "page_type": self.template_type,
            "products": {
                "product_a": product_a,
                "product_b": product_b
            },
            "comparison": comparison,
            "recommendation": recommendation
        }
    
    def _process_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process product data into consistent structure.
        
        Args:
            product: Raw product dictionary
            
        Returns:
            Processed product dictionary
        """
        return {
            "name": product.get("name", "Unknown Product"),
            "concentration": product.get("concentration", ""),
            "key_ingredients": product.get("key_ingredients", []),
            "benefits": product.get("benefits", []),
            "skin_type": product.get("skin_type", []),
            "price": product.get("price", "")
        }
    
    def _build_comparison(
        self, 
        data: Dict[str, Any], 
        blocks: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build comparison structure from data and blocks.
        
        Args:
            data: Dictionary of content data
            blocks: Dictionary of logic block outputs
            
        Returns:
            Comparison dictionary
        """
        base_comparison = data.get("comparison", {})
        
        return {
            "ingredients": blocks.get("compare_ingredients_block", 
                base_comparison.get("ingredients", {})),
            "benefits": blocks.get("compare_benefits_block", 
                base_comparison.get("benefits", {})),
            "concentration": base_comparison.get("concentration", {
                "product_a": "",
                "product_b": "",
                "analysis": ""
            }),
            "price": blocks.get("pricing_block", 
                base_comparison.get("price", {})),
            "suitability": base_comparison.get("suitability", {
                "product_a_best_for": [],
                "product_b_best_for": []
            })
        }
    
    def _generate_recommendation(
        self, 
        product_a: Dict[str, Any], 
        product_b: Dict[str, Any],
        comparison: Dict[str, Any]
    ) -> str:
        """
        Generate a recommendation based on comparison data.
        
        Args:
            product_a: Product A data
            product_b: Product B data
            comparison: Comparison data
            
        Returns:
            Recommendation text
        """
        # Simple heuristic-based recommendation
        price_info = comparison.get("price", {})
        cheaper = price_info.get("cheaper_product", product_a.get("name"))
        
        return (
            f"Choose {product_a.get('name')} for value and proven brightening benefits. "
            f"Consider {product_b.get('name')} if seeking higher concentration or additional "
            f"anti-aging properties. Both products are effective for their intended purposes."
        )
