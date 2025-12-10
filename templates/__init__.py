"""
Templates package for content generation.

This package provides a custom template engine with:
- BaseTemplate abstract class
- Validation and rendering
- Required/optional field definitions
- Logic block dependencies
"""

from templates.base_template import BaseTemplate
from templates.faq_template import FAQTemplate
from templates.product_template import ProductTemplate
from templates.comparison_template import ComparisonTemplate

__all__ = [
    "BaseTemplate",
    "FAQTemplate",
    "ProductTemplate",
    "ComparisonTemplate"
]
