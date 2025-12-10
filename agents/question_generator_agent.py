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
        return f"""Generate exactly 18 user questions about this product.
The questions should be what a potential customer might ask.

Product Information:
- Name: {product.name}
- Type/Version: {product.product_type}
- Target Users: {', '.join(product.target_users)}
- Key Features: {', '.join(product.key_features)}
- Benefits: {', '.join(product.benefits)}
- How to Use: {product.how_to_use}
- Considerations: {product.considerations}
- Price: {product.price}

Generate questions in these 5 categories (at least 3 per category):
1. Informational - About what the product is and what it does
2. Safety - About limitations, considerations, suitability
3. Usage - About how to use and get started
4. Purchase - About price, value, availability
5. Comparison - About how it compares to alternatives

Output as JSON array with this structure:
[
    {{"category": "Informational", "question": "What is...?"}},
    {{"category": "Safety", "question": "Are there any...?"}},
    ...
]

IMPORTANT: 
- Output ONLY the JSON array, no other text
- Generate exactly 18 questions total
- Make questions natural and customer-focused
- Base questions ONLY on the provided product data
- Make questions specific to THIS product type"""
    
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
        
        # Template questions by category (generic for any product type)
        templates = {
            QuestionCategory.INFORMATIONAL: [
                f"What makes {product.name} unique?",
                f"What are the key features of {product.name}?",
                f"What is {product.product_type}?",
            ],
            QuestionCategory.SAFETY: [
                f"Are there any limitations or considerations for {product.name}?",
                f"What should I be aware of before using {product.name}?",
                f"What are the potential issues with {product.name}?",
            ],
            QuestionCategory.USAGE: [
                f"How do I use {product.name}?",
                f"How do I get started with {product.name}?",
                f"What is the best way to use {product.name}?",
            ],
            QuestionCategory.PURCHASE: [
                f"What is the price of {product.name}?",
                f"Is {product.name} worth the price?",
                f"Where can I get {product.name}?",
            ],
            QuestionCategory.COMPARISON: [
                f"How does {product.name} compare to alternatives?",
                f"What makes {product.name} different from competitors?",
                f"Is {product.name} better than similar products?",
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
        """Generate fallback questions using LLM if main generation fails."""
        logger.info(f"{self.name}: Generating fallback questions via LLM")
        
        try:
            prompt = f"""Generate 15 simple user questions about "{product.name}".

Product: {product.name}
Type: {product.product_type}
Features: {', '.join(product.key_features)}
Benefits: {', '.join(product.benefits)}
Price: {product.price}

Categories: Informational, Safety, Usage, Purchase, Comparison (3 each)

Output JSON array: [{{"category": "X", "question": "Y?"}}]
Output ONLY valid JSON array."""

            response = invoke_with_retry(prompt).strip()
            
            if "```" in response:
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            response = response.strip()
            
            import json
            data = json.loads(response)
            
            questions = []
            for i, item in enumerate(data):
                cat = item.get("category", "Informational")
                q = item.get("question", "")
                if q:
                    try:
                        category = QuestionCategory[cat.upper()]
                    except KeyError:
                        category = QuestionCategory.INFORMATIONAL
                    questions.append(QuestionModel(id=f"q{i+1}", category=category, question=q))
            
            return questions[:15]
            
        except Exception as e:
            logger.warning(f"{self.name}: LLM fallback failed: {e}, using minimal questions")
            # Absolute minimal fallback
            return [
                QuestionModel(id="q1", category=QuestionCategory.INFORMATIONAL, question=f"What is {product.name}?"),
                QuestionModel(id="q2", category=QuestionCategory.INFORMATIONAL, question=f"What does {product.name} do?"),
                QuestionModel(id="q3", category=QuestionCategory.USAGE, question=f"How do I use {product.name}?"),
                QuestionModel(id="q4", category=QuestionCategory.PURCHASE, question=f"What is the price of {product.name}?"),
                QuestionModel(id="q5", category=QuestionCategory.SAFETY, question=f"Are there any issues with {product.name}?"),
            ]

