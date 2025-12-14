"""
Product Page Agent.

Responsible for creating comprehensive product page content.
Single responsibility: Build complete product page using logic blocks.
"""

import logging
from typing import Dict, Any, Tuple, List


from models import ProductModel, NormalizedPrice
from config import invoke_with_retry, invoke_with_metrics
from logic_blocks import (
    generate_benefits_block,
    generate_usage_block,
    generate_ingredients_block,
    generate_safety_block
)


logger = logging.getLogger(__name__)


class ProductPageAgent:
    """
    Agent responsible for creating product page content.
    
    Builds a comprehensive product page using all relevant logic blocks.
    The page includes product description, features, benefits, ingredients,
    usage instructions, and safety information.
    
    Attributes:
        name: Agent identifier
    """
    
    name: str = "product_page_agent"
    
    def __init__(self):
        """Initialize the Product Page Agent."""
        logger.info(f"Initialized {self.name}")
    
    def execute(self, product: ProductModel) -> Tuple[Dict[str, Any], List[str], Dict[str, Any]]:
        """
        Create product page content.
        
        Uses all logic blocks to build a comprehensive product page
        with enriched content.
        
        Args:
            product: Validated ProductModel
            
        Returns:
            Tuple of (product page content dict, list of errors, agent_metrics dict)
        """
        logger.info(f"{self.name}: Creating product page for {product.name}")
        errors: List[str] = []
        agent_metrics = {"tokens_in": 0, "tokens_out": 0, "output_len": 0, "prompts": {}}
        
        try:
            # Generate all logic blocks
            blocks = self._generate_all_blocks(product)
            logger.info(f"{self.name}: Generated {len(blocks)} logic blocks")
            
            # Generate enhanced descriptions using LLM (tracked separately)
            tagline = self._generate_tagline(product)
            headline = self._generate_headline(product)
            description = self._generate_description(product, blocks)
            
            # Build product page structure
            product_content = {
                "product": {
                    "name": product.name,
                    "product_type": product.product_type,
                    "tagline": tagline,
                    "headline": headline,
                    "description": description,
                    
                    "key_features": self._build_key_features(product, blocks),
                    
                    "ingredients": blocks["ingredients_block"],
                    "benefits": blocks["benefits_block"],
                    "how_to_use": blocks["usage_block"],
                    
                    "suitable_for": product.target_users,
                    
                    "safety_information": blocks["safety_block"],
                    
                    # Comment 1: Backward-compatible price fields
                    # Keep legacy "price" as string for older consumers
                    "price": product.price,
                    # Add normalized_price with currency/amount for newer consumers
                    "normalized_price": NormalizedPrice.from_string(product.price).model_dump()
                },
                "blocks": blocks
            }
            
            logger.info(f"{self.name}: Product page created successfully")
            return product_content, errors, agent_metrics
            
        except Exception as e:
            error = f"Error creating product page: {str(e)}"
            logger.error(f"{self.name}: {error}")
            errors.append(error)
            return {}, errors, agent_metrics
    
    def _generate_all_blocks(self, product: ProductModel) -> Dict[str, Any]:
        """Generate all logic blocks for the product page."""
        logger.debug(f"{self.name}: Generating logic blocks")
        
        return {
            "benefits_block": generate_benefits_block(product),
            "usage_block": generate_usage_block(product),
            "ingredients_block": generate_ingredients_block(product),
            "safety_block": generate_safety_block(product)
        }
    
    def _generate_tagline(self, product: ProductModel) -> str:
        """Generate a catchy tagline for the product."""
        try:
            prompt = f"""Create a short, catchy tagline (max 10 words) for this product:
Product: {product.name}
Key Benefits: {', '.join(product.benefits)}
Key Feature: {product.key_features[0] if product.key_features else 'premium quality'}

Output only the tagline text, nothing else."""
            
            tagline = invoke_with_retry(prompt).strip().strip('"')
            return tagline
            
        except Exception as e:
            logger.warning(f"{self.name}: Failed to generate tagline: {e}")
            return f"Experience {product.product_type} excellence"
    
    def _generate_headline(self, product: ProductModel) -> str:
        """Generate a headline for the product page."""
        try:
            prompt = f"""Create a compelling headline (max 15 words) for this product page:
Product: {product.name}
Type: {product.product_type}
Main Benefit: {product.benefits[0] if product.benefits else 'quality'}

Output only the headline text, nothing else."""
            
            headline = invoke_with_retry(prompt).strip().strip('"')
            return headline
            
        except Exception as e:
            logger.warning(f"{self.name}: Failed to generate headline: {e}")
            return f"{product.name} - Your Path to {product.benefits[0] if product.benefits else 'Excellence'}"
    
    def _generate_description(
        self, 
        product: ProductModel, 
        blocks: Dict[str, Any]
    ) -> str:
        """Generate a comprehensive product description."""
        try:
            benefits_info = blocks["benefits_block"]
            ingredients_info = blocks["ingredients_block"]
            
            prompt = f"""Write a compelling product description (3-4 sentences) for:
Product: {product.name}
Concentration: {product.product_type}
Key Ingredients: {', '.join(product.key_features)}
Benefits: {benefits_info.get('primary_benefits', product.benefits)}
Suitable For: {', '.join(product.target_users)}

Focus on benefits and what makes this product special. Be enthusiastic but factual.
Output only the description text, nothing else."""
            
            description = invoke_with_retry(prompt).strip()
            return description
            
        except Exception as e:
            logger.warning(f"{self.name}: Failed to generate description: {e}")
            return (f"{product.name} features {product.product_type} to deliver "
                   f"{' and '.join(product.benefits).lower()}. "
                   f"Built with {' and '.join(product.key_features)}, "
                   f"this product is perfect for {' and '.join(product.target_users).lower()}. "
                   f"{product.how_to_use}")
    
    def _build_key_features(
        self, 
        product: ProductModel, 
        blocks: Dict[str, Any]
    ) -> List[str]:
        """Build list of key features from product and blocks."""
        features = []
        
        # Add concentration as feature
        features.append(f"{product.product_type}")
        
        # Add key features
        for feature in product.key_features[:3]:
            features.append(f"Includes {feature}")
        
        # Add primary benefits
        for benefit in product.benefits:
            features.append(f"{benefit}")
        
        # Add suitability
        features.append(f"Designed for {' & '.join(product.target_users)}")
        
        return features
