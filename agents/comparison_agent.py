"""
Comparison Agent.

Responsible for creating product comparison page with a fictional competitor product.
Always generates a fictional competitor - no external search.
"""

import logging
import json
from typing import Dict, Any, Tuple, List


from models import ProductModel
from config import invoke_with_retry, invoke_with_metrics
from logic_blocks import (
    compare_ingredients_block,
    compare_benefits_block,
    generate_pricing_block
)


logger = logging.getLogger(__name__)


class ComparisonAgent:
    """
    Agent responsible for creating product comparison content.
    
    Generates a realistic competitor product using LLM based on
    the product category, then creates a structured comparison.
    
    Attributes:
        name: Agent identifier
    """
    
    name: str = "comparison_agent"
    
    def __init__(self):
        """Initialize the Comparison Agent."""
        logger.info(f"Initialized {self.name}")
    
    def execute(self, product: ProductModel) -> Tuple[Dict[str, Any], List[str], Dict[str, Any]]:
        """
        Create comparison page content.
        
        Generates a realistic competitor Product B and compares it with Product A.
        
        Args:
            product: Validated ProductModel (Product A)
            
        Returns:
            Tuple of (comparison content dict, list of errors, agent_metrics dict)
        """
        logger.info(f"{self.name}: Creating comparison for {product.name}")
        errors: List[str] = []
        agent_metrics = {"tokens_in": 0, "tokens_out": 0, "output_len": 0, "prompts": {}}
        
        try:
            # Generate realistic competitor using LLM
            product_b = self._generate_product_b(product)
            logger.info(f"{self.name}: Generated competitor: {product_b.name}")
            
            # Generate comparison logic blocks
            blocks = self._generate_comparison_blocks(product, product_b)
            
            # Build comparison structure
            comparison_data = self._build_comparison(product, product_b, blocks)
            
            # Generate recommendation
            recommendation = self._generate_recommendation(product, product_b, blocks)
            
            comparison_content = {
                "products": {
                    "product_a": self._product_to_dict(product),
                    "product_b": self._product_to_dict(product_b)
                },
                "comparison": comparison_data,
                "recommendation": recommendation,
                "blocks": blocks
            }
            
            logger.info(f"{self.name}: Comparison page created successfully")
            return comparison_content, errors, agent_metrics
            
        except Exception as e:
            error = f"Error creating comparison: {str(e)}"
            logger.error(f"{self.name}: {error}")
            errors.append(error)
            return {}, errors, agent_metrics
    
    def _generate_product_b(self, product_a: ProductModel) -> ProductModel:
        """
        Generate a realistic competitor product based on the input product.
        
        Uses LLM to research and create a comparable competitor.
        
        Args:
            product_a: The input product to compare against
            
        Returns:
            ProductModel for competitor Product B
        """
        # Always create fictional competitor (no external search)
        prompt = f"""Create a realistic FICTIONAL competitor product that would compete in the same market.

INPUT PRODUCT (Main Product):
- Name: {product_a.name}
- Type: {product_a.product_type}
- Features: {', '.join(product_a.key_features)}
- Benefits: {', '.join(product_a.benefits)}
- Target: {', '.join(product_a.target_users)}
- Price: {product_a.price}

Create a SIMPLER competitor product. IMPORTANT: Keep ALL text SHORT and CONCISE.
- Product type: max 5 words
- Target users: max 2 items
- Key features: max 2 items, each max 3 words
- Benefits: max 2 items, each max 5 words  
- Considerations: max 10 words
- Price: simple format

Output as JSON:
{{
    "name": "Short Competitor Name",
    "product_type": "Brief type (max 5 words)",
    "target_users": ["User 1", "User 2"],
    "key_features": ["Feature 1", "Feature 2"],
    "benefits": ["Benefit 1", "Benefit 2"],
    "how_to_use": "Brief usage",
    "considerations": "Short limitation",
    "price": "Simple price"
}}

Output ONLY the JSON, no other text."""

        try:
            raw = invoke_with_retry(prompt)
            product_b_data = self._parse_product_b_response(raw, product_a)
            return ProductModel(**product_b_data)
            
        except Exception as e:
            logger.warning(f"{self.name}: Failed to generate competitor: {e}")
            return self._fallback_product_b(product_a)
    
    def _parse_product_b_response(
        self, 
        response: str, 
        product_a: ProductModel
    ) -> Dict[str, Any]:
        """Parse LLM response for Product B."""
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        try:
            data = json.loads(response)
            
            # Validate required fields
            required = ["name", "product_type", "target_users", "key_features", 
                       "benefits", "how_to_use", "considerations", "price"]
            for field in required:
                if field not in data:
                    raise ValueError(f"Missing field: {field}")
            
            # Ensure lists are lists
            for list_field in ["target_users", "key_features", "benefits"]:
                if isinstance(data[list_field], str):
                    data[list_field] = [x.strip() for x in data[list_field].split(",")]
            
            return data
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"{self.name}: Failed to parse competitor JSON: {e}")
            return self._fallback_product_b_data(product_a)
    
    def _fallback_product_b(self, product_a: ProductModel) -> ProductModel:
        """Generate fallback Product B if LLM fails."""
        return ProductModel(**self._fallback_product_b_data(product_a))
    
    def _fallback_product_b_data(self, product_a: ProductModel) -> Dict[str, Any]:
        """Generate fallback Product B data based on product A's category."""
        # Create a generic competitor based on input product
        return {
            "name": f"Alternative to {product_a.name}",
            "product_type": f"Premium {product_a.product_type}",
            "target_users": product_a.target_users,
            "key_features": product_a.key_features[:2] + ["Enhanced Features"],
            "benefits": product_a.benefits[:2] + ["Premium Support"],
            "how_to_use": product_a.how_to_use,
            "considerations": "Similar considerations apply",
            "price": "Premium pricing"
        }
    
    def _generate_comparison_blocks(
        self, 
        product_a: ProductModel, 
        product_b: ProductModel
    ) -> Dict[str, Any]:
        """Generate comparison logic blocks with cross-block analysis."""
        from logic_blocks import (
            generate_benefits_block, 
            generate_safety_block
        )
        from logic_blocks.cross_block_analyzer import (
            analyze_benefit_safety_conflicts,
            generate_cross_block_summary
        )
        
        logger.debug(f"{self.name}: Generating comparison blocks")
        
        # Generate individual blocks for both products
        benefits_a = generate_benefits_block(product_a)
        safety_a = generate_safety_block(product_a)
        benefits_b = generate_benefits_block(product_b)
        safety_b = generate_safety_block(product_b)
        
        # Cross-block analysis for both products
        conflicts_a = analyze_benefit_safety_conflicts(benefits_a, safety_a)
        conflicts_b = analyze_benefit_safety_conflicts(benefits_b, safety_b)
        
        return {
            "compare_ingredients_block": compare_ingredients_block(product_a, product_b),
            "compare_benefits_block": compare_benefits_block(product_a, product_b),
            "pricing_block": generate_pricing_block(product_a, product_b),
            "cross_block_analysis": {
                "product_a": {
                    "benefit_safety_conflicts": conflicts_a,
                    "risk_benefit_ratio": conflicts_a.get("risk_benefit_ratio", 5.0)
                },
                "product_b": {
                    "benefit_safety_conflicts": conflicts_b,
                    "risk_benefit_ratio": conflicts_b.get("risk_benefit_ratio", 5.0)
                }
            }
        }
    
    def _build_comparison(
        self, 
        product_a: ProductModel, 
        product_b: ProductModel,
        blocks: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build comparison data structure."""
        return {
            "ingredients": blocks["compare_ingredients_block"],
            "benefits": blocks["compare_benefits_block"],
            "product_type": {
                "product_a": product_a.product_type,
                "product_b": product_b.product_type,
                "analysis": f"{product_a.name} offers {product_a.product_type}, while {product_b.name} provides {product_b.product_type}."
            },
            "price": blocks["pricing_block"],
            "suitability": {
                "product_a_best_for": product_a.target_users,
                "product_b_best_for": product_b.target_users,
                "overlap": list(set(product_a.target_users) & set(product_b.target_users))
            }
        }
    
    def _generate_recommendation(
        self, 
        product_a: ProductModel, 
        product_b: ProductModel,
        blocks: Dict[str, Any]
    ) -> str:
        """Generate comparison recommendation."""
        return (f"{product_a.name} ({product_a.price}) offers {', '.join(product_a.benefits[:2])}. "
               f"{product_b.name} ({product_b.price}) provides {', '.join(product_b.benefits[:2])}. "
               f"Choose based on your specific needs and budget.")
    
    def _product_to_dict(self, product: ProductModel) -> Dict[str, Any]:
        """Convert ProductModel to serializable dict."""
        return {
            "name": product.name,
            "product_type": product.product_type,
            "key_features": product.key_features,
            "benefits": product.benefits,
            "target_users": product.target_users,
            "price": product.price,
            "how_to_use": product.how_to_use,
            "considerations": product.considerations
        }
