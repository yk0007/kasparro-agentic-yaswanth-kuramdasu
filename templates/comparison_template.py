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
    competitor generated using Groq LLM - always fictional).
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
                required_b_fields = ["name", "benefits", "price"]
                for field in required_b_fields:
                    if field not in product_b or not product_b.get(field):
                        self._warnings.append(
                            f"Product B should have '{field}' field"
                        )
        
        if "comparison" in data:
            comparison = data["comparison"]
            
            if not isinstance(comparison, dict):
                self._errors.append("comparison must be a dictionary")
                return
            
            # Check comparison has required sections
            recommended_sections = ["features", "benefits", "price"]
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
        
        Pass-through the data built by ComparisonAgent.
        
        Args:
            data: Dictionary of content data (built by agent)
            blocks: Dictionary of logic block outputs
            
        Returns:
            Rendered comparison page content dictionary
        """
        # Pass-through the agent-built structure
        return {
            "page_type": self.template_type,
            "products": data.get("products", {}),
            "comparison": data.get("comparison", {}),
            "recommendation": data.get("recommendation", "")
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
            "type": product.get("product_type", ""),
            "key_features": product.get("key_features", product.get("key_features", [])),
            "benefits": product.get("benefits", []),
            "target_users": product.get("target_users", product.get("target_users", [])),
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
            "features": blocks.get("compare_ingredients_block", 
                base_comparison.get("ingredients", base_comparison.get("features", {}))),
            "benefits": blocks.get("compare_benefits_block", 
                base_comparison.get("benefits", {})),
            "type": base_comparison.get("product_type", {
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
            f"Choose {product_a.get('name')} for value and proven benefits. "
            f"Consider {product_b.get('name')} for alternative features. "
            f"Both products serve their intended purposes effectively."
        )
