"""
Pydantic models for Multi-Agent Content Generation System.

This module defines all data models for type-safe handling of:
- Product data (input)
- Generated questions
- Content structures (FAQ, Product, Comparison)
"""

from datetime import datetime
from typing import List, Dict, Optional, Literal
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class QuestionCategory(str, Enum):
    """Categories for generated user questions."""
    INFORMATIONAL = "Informational"
    SAFETY = "Safety"
    USAGE = "Usage"
    PURCHASE = "Purchase"
    COMPARISON = "Comparison"


class ProductModel(BaseModel):
    """
    Validated product data model.
    
    This is the core data structure that flows through the entire system.
    All content generation is based on this model.
    """
    name: str = Field(..., description="Product name")
    product_type: str = Field(..., description="Product type, version, or specification")
    target_users: List[str] = Field(..., description="Target users or audience")
    key_features: List[str] = Field(..., description="Key features or components")
    benefits: List[str] = Field(..., description="Product benefits")
    how_to_use: str = Field(..., description="Usage instructions")
    considerations: str = Field(..., description="Limitations or considerations")
    price: str = Field(..., description="Product price")
    
    @field_validator("name", "product_type", "how_to_use", "considerations", "price")
    @classmethod
    def validate_non_empty_string(cls, v: str) -> str:
        """Ensure string fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()
    
    @field_validator("target_users", "key_features", "benefits")
    @classmethod
    def validate_non_empty_list(cls, v: List[str]) -> List[str]:
        """Ensure list fields have at least one item."""
        if not v:
            raise ValueError("List cannot be empty")
        return [item.strip() for item in v if item.strip()]


class QuestionModel(BaseModel):
    """
    Model for generated user questions.
    
    Each question is categorized and may include an answer (for FAQ).
    """
    id: str = Field(..., description="Unique question identifier")
    category: QuestionCategory = Field(..., description="Question category")
    question: str = Field(..., description="The question text")
    answer: Optional[str] = Field(None, description="Answer text (for FAQ)")
    logic_blocks_used: List[str] = Field(default_factory=list, description="Logic blocks used to answer")
    
    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        """Ensure question is not empty and ends with ?"""
        if not v or not v.strip():
            raise ValueError("Question cannot be empty")
        v = v.strip()
        if not v.endswith("?"):
            v += "?"
        return v


class FAQItem(BaseModel):
    """Single FAQ item with question and answer."""
    id: str
    category: str
    question: str
    answer: str
    logic_blocks_used: List[str] = Field(default_factory=list)


class FAQContent(BaseModel):
    """
    FAQ page content structure.
    
    Requires minimum 5 questions with answers.
    """
    page_type: Literal["faq"] = "faq"
    product_name: str
    questions: List[FAQItem] = Field(..., min_length=5)
    metadata: Dict = Field(default_factory=dict)
    
    @field_validator("questions")
    @classmethod
    def validate_min_questions(cls, v: List[FAQItem]) -> List[FAQItem]:
        """Ensure minimum 5 questions."""
        if len(v) < 5:
            raise ValueError("FAQ must have at least 5 questions")
        return v


class ProductPageContent(BaseModel):
    """
    Product page content structure.
    
    Contains all product information organized for display.
    """
    page_type: Literal["product"] = "product"
    product: Dict = Field(..., description="Complete product information")
    metadata: Dict = Field(default_factory=dict)


class ComparisonProduct(BaseModel):
    """Product structure for comparison page."""
    name: str
    product_type: str
    key_features: List[str]
    benefits: List[str]
    target_users: List[str]
    price: str


class ComparisonContent(BaseModel):
    """
    Comparison page content structure.
    
    Compares Product A (input) with fictional Product B.
    """
    page_type: Literal["comparison"] = "comparison"
    products: Dict[str, ComparisonProduct] = Field(
        ..., 
        description="Product A and Product B data"
    )
    comparison: Dict = Field(..., description="Comparison analysis")
    metadata: Dict = Field(default_factory=dict)


class ContentMetadata(BaseModel):
    """Metadata for generated content."""
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    agent: str
    version: str = "1.0"
    logic_blocks_used: List[str] = Field(default_factory=list)
    total_questions: Optional[int] = None


# Example product data for testing
EXAMPLE_PRODUCT_DATA = {
    "name": "GlowBoost Vitamin C Serum",
    "product_type": "10% Vitamin C",
    "target_users": ["Oily", "Combination"],
    "key_features": ["Vitamin C", "Hyaluronic Acid"],
    "benefits": ["Brightening", "Fades dark spots"],
    "how_to_use": "Apply 2–3 drops in the morning before sunscreen",
    "considerations": "Mild tingling for sensitive skin",
    "price": "₹699"
}
