"""
FAQ Agent.

Responsible for creating FAQ page content with questions and answers.
Single responsibility: Select questions and generate answers using logic blocks.
"""

import logging
import json
from typing import List, Dict, Any, Tuple

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ProductModel, QuestionModel, QuestionCategory
from config import invoke_with_retry
from logic_blocks import (
    generate_benefits_block,
    generate_usage_block,
    generate_safety_block
)


logger = logging.getLogger(__name__)


class FAQAgent:
    """
    Agent responsible for creating FAQ page content.
    
    Selects a subset of generated questions (minimum 5) and generates
    comprehensive answers using logic blocks and LLM.
    
    Attributes:
        name: Agent identifier
        min_faqs: Minimum number of FAQ items
    """
    
    name: str = "faq_agent"
    min_faqs: int = 5
    
    def __init__(self):
        """Initialize the FAQ Agent."""
        logger.info(f"Initialized {self.name}")
    
    def execute(
        self, 
        product: ProductModel, 
        questions: List[QuestionModel]
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Create FAQ page content.
        
        Selects diverse questions from different categories and generates
        detailed answers using logic blocks and LLM.
        
        Args:
            product: Validated ProductModel
            questions: List of generated questions
            
        Returns:
            Tuple of (FAQ content dict, list of errors)
        """
        logger.info(f"{self.name}: Creating FAQ for {product.name}")
        errors: List[str] = []
        
        try:
            # Select questions for FAQ (ensure diversity)
            selected = self._select_questions(questions)
            logger.info(f"{self.name}: Selected {len(selected)} questions for FAQ")
            
            # Generate logic blocks
            blocks = self._generate_blocks(product)
            
            # Generate answers for each question
            faq_items = []
            for question in selected:
                answer, blocks_used = self._generate_answer(product, question, blocks)
                faq_items.append({
                    "id": question.id,
                    "category": question.category.value,
                    "question": question.question,
                    "answer": answer,
                    "logic_blocks_used": blocks_used
                })
            
            # Build final FAQ content
            faq_content = {
                "product_name": product.name,
                "questions": faq_items,
                "blocks": blocks
            }
            
            logger.info(f"{self.name}: Generated {len(faq_items)} FAQ items")
            return faq_content, errors
            
        except Exception as e:
            error = f"Error creating FAQ: {str(e)}"
            logger.error(f"{self.name}: {error}")
            errors.append(error)
            return {}, errors
    
    def _select_questions(self, questions: List[QuestionModel]) -> List[QuestionModel]:
        """
        Select diverse questions for FAQ.
        
        Ensures at least one question from each category if available.
        
        Args:
            questions: All generated questions
            
        Returns:
            Selected questions for FAQ
        """
        selected = []
        by_category: Dict[QuestionCategory, List[QuestionModel]] = {}
        
        # Group by category
        for q in questions:
            if q.category not in by_category:
                by_category[q.category] = []
            by_category[q.category].append(q)
        
        # Select at least one from each category
        for category in QuestionCategory:
            if category in by_category and by_category[category]:
                selected.append(by_category[category][0])
        
        # Add more to reach minimum if needed
        for category, qs in by_category.items():
            for q in qs[1:]:
                if len(selected) >= max(self.min_faqs, 7):
                    break
                if q not in selected:
                    selected.append(q)
        
        return selected[:max(self.min_faqs, 7)]
    
    def _generate_blocks(self, product: ProductModel) -> Dict[str, Any]:
        """Generate all logic blocks for answer generation."""
        return {
            "benefits_block": generate_benefits_block(product),
            "usage_block": generate_usage_block(product),
            "safety_block": generate_safety_block(product)
        }
    
    def _generate_answer(
        self, 
        product: ProductModel, 
        question: QuestionModel,
        blocks: Dict[str, Any]
    ) -> Tuple[str, List[str]]:
        """
        Generate answer for a question using LLM and logic blocks.
        
        Args:
            product: Product model
            question: Question to answer
            blocks: Pre-generated logic blocks
            
        Returns:
            Tuple of (answer text, list of logic blocks used)
        """
        blocks_used = []
        
        # Determine relevant blocks based on category
        relevant_data = {}
        
        if question.category == QuestionCategory.INFORMATIONAL:
            relevant_data["benefits"] = blocks["benefits_block"]
            blocks_used.append("benefits_block")
        elif question.category == QuestionCategory.SAFETY:
            relevant_data["safety"] = blocks["safety_block"]
            blocks_used.append("safety_block")
        elif question.category == QuestionCategory.USAGE:
            relevant_data["usage"] = blocks["usage_block"]
            blocks_used.append("usage_block")
        elif question.category == QuestionCategory.PURCHASE:
            relevant_data["benefits"] = blocks["benefits_block"]
            blocks_used.append("benefits_block")
        elif question.category == QuestionCategory.COMPARISON:
            relevant_data["benefits"] = blocks["benefits_block"]
            relevant_data["safety"] = blocks["safety_block"]
            blocks_used.extend(["benefits_block", "safety_block"])
        
        # Generate answer using LLM with key rotation
        prompt = self._build_answer_prompt(product, question, relevant_data)
        
        try:
            answer = invoke_with_retry(prompt).strip()
            
            # Clean up answer
            if answer.startswith('"') and answer.endswith('"'):
                answer = answer[1:-1]
            
            return answer, blocks_used
            
        except Exception as e:
            logger.error(f"{self.name}: Error generating answer: {e}")
            # Return fallback answer
            return self._fallback_answer(product, question), blocks_used
    
    def _build_answer_prompt(
        self, 
        product: ProductModel, 
        question: QuestionModel,
        relevant_data: Dict[str, Any]
    ) -> str:
        """Build prompt for answer generation."""
        return f"""Answer this customer question about a product.
Use ONLY the provided product information. Be concise but helpful.

Product: {product.name}
Type/Version: {product.product_type}  
Key Features: {', '.join(product.key_features)}
Benefits: {', '.join(product.benefits)}
How to Use: {product.how_to_use}
Considerations: {product.considerations}
Price: {product.price}
Target Users: {', '.join(product.target_users)}

Additional Context:
{json.dumps(relevant_data, indent=2)}

Question: {question.question}

Provide a helpful, accurate answer in 1-2 sentences. Be direct and straight to the point. Do not add information beyond what's provided.
IMPORTANT: Adapt terminology to the product type:
- Tech products: use "features", "specifications", "capabilities"
- Food products: use "ingredients", "nutrition", "recipe"
- Fashion products: use "materials", "style", "design"
- Beauty products: use "ingredients", "skin benefits"
Output only the answer text, no formatting or prefixes."""
    
    def _fallback_answer(self, product: ProductModel, question: QuestionModel) -> str:
        """Generate fallback answer based on category."""
        category = question.category
        
        if category == QuestionCategory.INFORMATIONAL:
            return (f"{product.name} is a {product.product_type} product "
                   f"that delivers {', '.join(product.benefits).lower()}. "
                   f"Key features include {', '.join(product.key_features)}.")
        elif category == QuestionCategory.SAFETY:
            return (f"{product.considerations}. This product is designed for "
                   f"{', '.join(product.target_users).lower()}. "
                   f"Please review the considerations before use.")
        elif category == QuestionCategory.USAGE:
            return (f"{product.how_to_use}. For best results, "
                   f"follow the recommended usage guidelines.")
        elif category == QuestionCategory.PURCHASE:
            return (f"{product.name} is priced at {product.price}. "
                   f"It offers {', '.join(product.benefits).lower()} benefits "
                   f"at this price point.")
        else:  # COMPARISON
            return (f"{product.name} features {product.product_type} with "
                   f"{', '.join(product.key_features)}. "
                   f"It's designed for {', '.join(product.target_users).lower()}.")

