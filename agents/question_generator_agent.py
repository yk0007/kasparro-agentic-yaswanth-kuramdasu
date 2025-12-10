"""
Question Generator Agent.

Responsible for generating categorized user questions using Gemini LLM.
Single responsibility: Generate 15+ questions in 5 categories.
"""

import logging
import json
from typing import List, Dict, Any, Tuple

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ProductModel, QuestionModel, QuestionCategory
from config import invoke_with_retry


logger = logging.getLogger(__name__)


class QuestionGeneratorAgent:
    """
    Agent responsible for generating categorized user questions.
    
    Uses Gemini to generate diverse, relevant questions across 5 categories:
    - Informational: What is this product?
    - Safety: Side effects, precautions
    - Usage: How to use, frequency
    - Purchase: Price, availability
    - Comparison: vs other products
    
    Attributes:
        name: Agent identifier
        min_questions: Minimum number of questions to generate
    """
    
    name: str = "question_generator_agent"
    min_questions: int = 15
    
    def __init__(self):
        """Initialize the Question Generator Agent."""
        logger.info(f"Initialized {self.name}")
    
    def execute(self, product: ProductModel) -> Tuple[List[QuestionModel], List[str]]:
        """
        Generate categorized questions for the product.
        
        Uses Gemini LLM with automatic API key rotation to generate 
        at least 15 questions across 5 different categories.
        
        Args:
            product: Validated ProductModel
            
        Returns:
            Tuple of (list of QuestionModels, list of errors)
        """
        logger.info(f"{self.name}: Generating questions for {product.name}")
        errors: List[str] = []
        questions: List[QuestionModel] = []
        
        try:
            # Generate questions using LLM with key rotation
            prompt = self._build_prompt(product)
            logger.debug(f"{self.name}: Calling Gemini for question generation")
            
            # Use invoke_with_retry for automatic key rotation on rate limits
            raw_response = invoke_with_retry(prompt)
            
            # Parse the response
            questions = self._parse_response(raw_response, product)
            
            # Validate we have enough questions
            if len(questions) < self.min_questions:
                logger.warning(
                    f"{self.name}: Generated {len(questions)} questions, "
                    f"expected at least {self.min_questions}"
                )
                # Try to generate more if needed
                additional = self._generate_additional_questions(product, questions)
                questions.extend(additional)
            
            logger.info(f"{self.name}: Generated {len(questions)} questions")
            return questions, errors
            
        except Exception as e:
            error = f"Error generating questions: {str(e)}"
            logger.error(f"{self.name}: {error}")
            errors.append(error)
            
            # Return fallback questions
            fallback = self._generate_fallback_questions(product)
            return fallback, errors
    
    def _build_prompt(self, product: ProductModel) -> str:
        """Build the prompt for question generation."""
        return f"""Generate exactly 18 user questions about this skincare product.
The questions should be what a potential customer might ask.

Product Information:
- Name: {product.name}
- Concentration: {product.concentration}
- Skin Types: {', '.join(product.skin_type)}
- Key Ingredients: {', '.join(product.key_ingredients)}
- Benefits: {', '.join(product.benefits)}
- How to Use: {product.how_to_use}
- Side Effects: {product.side_effects}
- Price: {product.price}

Generate questions in these 5 categories (at least 3 per category):
1. Informational - About what the product is and contains
2. Safety - About side effects, precautions, suitability
3. Usage - About how and when to use
4. Purchase - About price, value, availability
5. Comparison - About how it compares to alternatives

Output as JSON array with this structure:
[
    {{"category": "Informational", "question": "What is...?"}},
    {{"category": "Safety", "question": "Is it safe...?"}},
    ...
]

IMPORTANT: 
- Output ONLY the JSON array, no other text
- Generate exactly 18 questions total
- Make questions natural and customer-focused
- Base questions ONLY on the provided product data"""
    
    def _parse_response(
        self, 
        response: str, 
        product: ProductModel
    ) -> List[QuestionModel]:
        """Parse LLM response into QuestionModels."""
        questions = []
        
        try:
            # Clean up the response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            # Parse JSON
            parsed = json.loads(response)
            
            if not isinstance(parsed, list):
                logger.warning(f"{self.name}: Expected list, got {type(parsed)}")
                return self._generate_fallback_questions(product)
            
            # Convert to QuestionModels
            for i, item in enumerate(parsed):
                if isinstance(item, dict) and "question" in item:
                    category_str = item.get("category", "Informational")
                    try:
                        category = QuestionCategory(category_str)
                    except ValueError:
                        category = QuestionCategory.INFORMATIONAL
                    
                    question = QuestionModel(
                        id=f"q{i+1}",
                        category=category,
                        question=item["question"]
                    )
                    questions.append(question)
            
            return questions
            
        except json.JSONDecodeError as e:
            logger.error(f"{self.name}: Failed to parse JSON: {e}")
            return self._generate_fallback_questions(product)
    
    def _generate_additional_questions(
        self, 
        product: ProductModel, 
        existing: List[QuestionModel]
    ) -> List[QuestionModel]:
        """Generate additional questions to meet minimum requirement."""
        additional = []
        existing_count = len(existing)
        needed = self.min_questions - existing_count
        
        if needed <= 0:
            return additional
        
        # Template questions by category
        templates = {
            QuestionCategory.INFORMATIONAL: [
                f"What makes {product.name} unique?",
                f"What ingredients are in {product.name}?",
                f"How concentrated is the active ingredient in {product.name}?",
            ],
            QuestionCategory.SAFETY: [
                f"Is {product.name} safe for sensitive skin?",
                f"Are there any side effects of using {product.name}?",
                f"Can I use {product.name} during pregnancy?",
            ],
            QuestionCategory.USAGE: [
                f"How often should I use {product.name}?",
                f"When is the best time to apply {product.name}?",
                f"How many drops of {product.name} should I use?",
            ],
            QuestionCategory.PURCHASE: [
                f"What is the price of {product.name}?",
                f"Is {product.name} worth the price?",
                f"Where can I buy {product.name}?",
            ],
            QuestionCategory.COMPARISON: [
                f"How does {product.name} compare to other vitamin C serums?",
                f"Is {product.name} better than higher concentration alternatives?",
                f"What's the difference between {product.name} and generic serums?",
            ],
        }
        
        # Add questions from each category
        idx = existing_count
        for category, questions in templates.items():
            for q in questions:
                if len(additional) >= needed:
                    break
                additional.append(QuestionModel(
                    id=f"q{idx + len(additional) + 1}",
                    category=category,
                    question=q
                ))
        
        return additional[:needed]
    
    def _generate_fallback_questions(self, product: ProductModel) -> List[QuestionModel]:
        """Generate fallback questions if LLM fails."""
        logger.info(f"{self.name}: Generating fallback questions")
        
        fallback = [
            # Informational (4)
            (QuestionCategory.INFORMATIONAL, f"What is {product.name}?"),
            (QuestionCategory.INFORMATIONAL, f"What are the key ingredients in {product.name}?"),
            (QuestionCategory.INFORMATIONAL, f"What skin concerns does {product.name} address?"),
            (QuestionCategory.INFORMATIONAL, f"What concentration of Vitamin C is in {product.name}?"),
            # Safety (3)
            (QuestionCategory.SAFETY, f"Is {product.name} suitable for sensitive skin?"),
            (QuestionCategory.SAFETY, f"What are the potential side effects of {product.name}?"),
            (QuestionCategory.SAFETY, f"Can I use {product.name} with other skincare products?"),
            # Usage (4)
            (QuestionCategory.USAGE, f"How do I use {product.name}?"),
            (QuestionCategory.USAGE, f"When should I apply {product.name}?"),
            (QuestionCategory.USAGE, f"How much product should I use per application?"),
            (QuestionCategory.USAGE, f"Should I use sunscreen after applying {product.name}?"),
            # Purchase (2)
            (QuestionCategory.PURCHASE, f"What is the price of {product.name}?"),
            (QuestionCategory.PURCHASE, f"Is {product.name} a good value for the price?"),
            # Comparison (3)
            (QuestionCategory.COMPARISON, f"How does {product.name} compare to similar products?"),
            (QuestionCategory.COMPARISON, f"Is 10% Vitamin C concentration enough?"),
            (QuestionCategory.COMPARISON, f"What makes {product.name} different from competitors?"),
        ]
        
        return [
            QuestionModel(id=f"q{i+1}", category=cat, question=q)
            for i, (cat, q) in enumerate(fallback)
        ]
