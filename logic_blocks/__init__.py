"""
Logic Blocks package for content generation.

This package contains pure, reusable functions for transforming
product data into structured content. Each block is:
- Pure (no side effects)
- Type-hinted
- Independently testable
- Composable
"""

from logic_blocks.benefits_block import generate_benefits_block
from logic_blocks.usage_block import generate_usage_block
from logic_blocks.ingredients_block import generate_ingredients_block
from logic_blocks.safety_block import generate_safety_block
from logic_blocks.comparison_blocks import (
    compare_ingredients_block,
    compare_benefits_block,
    generate_pricing_block
)
from logic_blocks.cross_block_analyzer import (
    analyze_benefit_safety_conflicts,
    analyze_ingredient_benefit_links,
    generate_cross_block_summary
)

__all__ = [
    "generate_benefits_block",
    "generate_usage_block",
    "generate_ingredients_block",
    "generate_safety_block",
    "compare_ingredients_block",
    "compare_benefits_block",
    "generate_pricing_block",
    "analyze_benefit_safety_conflicts",
    "analyze_ingredient_benefit_links",
    "generate_cross_block_summary"
]
