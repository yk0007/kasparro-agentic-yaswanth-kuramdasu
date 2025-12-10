"""
Agents package for Multi-Agent Content Generation System.

This package contains 6 distinct agents, each with single responsibility:
- ParserAgent: Parse and validate product data
- QuestionGeneratorAgent: Generate categorized questions
- FAQAgent: Create FAQ page content
- ProductPageAgent: Create product page content
- ComparisonAgent: Create comparison page with fictional Product B
- OutputAgent: Format and save JSON outputs
"""

from agents.parser_agent import ParserAgent
from agents.question_generator_agent import QuestionGeneratorAgent
from agents.faq_agent import FAQAgent
from agents.product_page_agent import ProductPageAgent
from agents.comparison_agent import ComparisonAgent
from agents.output_agent import OutputAgent

__all__ = [
    "ParserAgent",
    "QuestionGeneratorAgent",
    "FAQAgent",
    "ProductPageAgent",
    "ComparisonAgent",
    "OutputAgent"
]
