"""
Comparison Agent.

Responsible for creating product comparison page with a competitor product.
Uses LLM to generate realistic competitor product based on actual market research.
"""

import logging
import json
from typing import Dict, Any, Tuple, List

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ProductModel
from config import invoke_with_retry
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
    
    def execute(self, product: ProductModel) -> Tuple[Dict[str, Any], List[str]]:
        """
        Create comparison page content.
        
        Generates a realistic competitor Product B and compares it with Product A.
        
        Args:
            product: Validated ProductModel (Product A)
            
        Returns:
            Tuple of (comparison content dict, list of errors)
        """
        logger.info(f"{self.name}: Creating comparison for {product.name}")
        errors: List[str] = []
        
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
            return comparison_content, errors
            
        except Exception as e:
            error = f"Error creating comparison: {str(e)}"
            logger.error(f"{self.name}: {error}")
            errors.append(error)
            return {}, errors
    
    def _generate_product_b(self, product_a: ProductModel) -> ProductModel:
        """
        Generate a realistic competitor product based on the input product.
        
        Uses LLM to research and create a comparable competitor.
        
        Args:
            product_a: The input product to compare against
            
        Returns:
            ProductModel for competitor Product B
        """
        logger.debug(f"{self.name}: Generating competitor product")
        
        prompt = f"""Based on this product, research and suggest a REAL competitor product that exists in the market.

INPUT PRODUCT:
- Name: {product_a.name}
- Category/Type: {product_a.concentration}
- Key Features: {', '.join(product_a.key_ingredients)}
- Benefits: {', '.join(product_a.benefits)}
- Target Users: {', '.join(product_a.skin_type)}
- Price: {product_a.price}

Create a realistic competitor product that:
1. Is a REAL or realistic product that would compete in the same market
2. Has similar but different features/capabilities
3. Is priced competitively (can be higher or lower)
4. Targets a similar audience

Output as JSON with this exact structure:
{{
    "name": "Real Competitor Product Name",
    "concentration": "Key differentiator or version",
    "skin_type": ["Target User 1", "Target User 2"],
    "key_ingredients": ["Feature 1", "Feature 2", "Feature 3"],
    "benefits": ["Benefit 1", "Benefit 2", "Benefit 3"],
    "how_to_use": "How to use or get started",
    "side_effects": "Limitations or considerations",
    "price": "Pricing"
}}

IMPORTANT: 
- Research real competitors in this product category
- Make it realistic and comparable
- Output ONLY the JSON, no other text"""

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
            required = ["name", "concentration", "skin_type", "key_ingredients", 
                       "benefits", "how_to_use", "side_effects", "price"]
            for field in required:
                if field not in data:
                    raise ValueError(f"Missing field: {field}")
            
            # Ensure lists are lists
            for list_field in ["skin_type", "key_ingredients", "benefits"]:
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
            "concentration": f"Premium {product_a.concentration}",
            "skin_type": product_a.skin_type,
            "key_ingredients": product_a.key_ingredients[:2] + ["Enhanced Features"],
            "benefits": product_a.benefits[:2] + ["Premium Support"],
            "how_to_use": product_a.how_to_use,
            "side_effects": "Similar considerations apply",
            "price": "Premium pricing"
        }
    
    def _generate_comparison_blocks(
        self, 
        product_a: ProductModel, 
        product_b: ProductModel
    ) -> Dict[str, Any]:
        """Generate comparison logic blocks."""
        logger.debug(f"{self.name}: Generating comparison blocks")
        
        return {
            "compare_ingredients_block": compare_ingredients_block(product_a, product_b),
            "compare_benefits_block": compare_benefits_block(product_a, product_b),
            "pricing_block": generate_pricing_block(product_a, product_b)
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
            "concentration": {
                "product_a": product_a.concentration,
                "product_b": product_b.concentration,
                "analysis": f"{product_a.name} offers {product_a.concentration}, while {product_b.name} provides {product_b.concentration}."
            },
            "price": blocks["pricing_block"],
            "suitability": {
                "product_a_best_for": product_a.skin_type,
                "product_b_best_for": product_b.skin_type,
                "overlap": list(set(product_a.skin_type) & set(product_b.skin_type))
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
            "concentration": product.concentration,
            "key_ingredients": product.key_ingredients,
            "benefits": product.benefits,
            "skin_type": product.skin_type,
            "price": product.price,
            "how_to_use": product.how_to_use,
            "side_effects": product.side_effects
        }
