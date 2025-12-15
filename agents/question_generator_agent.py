"""
Question Generator Agent.

Responsible for generating categorized user questions using Groq LLM.
Single responsibility: Generate 15+ questions in 5 categories.
"""

import logging
import json
from typing import List, Dict, Any, Tuple


from models import ProductModel, QuestionModel, QuestionCategory
from config import invoke_with_retry, invoke_with_metrics


logger = logging.getLogger(__name__)


def _to_question_category(raw: str) -> QuestionCategory:
    """
    Map a free-form category string to a QuestionCategory enum.
    
    Tries exact value match, case-insensitive value, then enum name,
    and defaults to INFORMATIONAL if no match is found.
    
    Args:
        raw: Raw category string from LLM response
        
    Returns:
        Matched QuestionCategory or INFORMATIONAL as fallback
    """
    if not raw:
        return QuestionCategory.INFORMATIONAL
    s = str(raw).strip()
    
    # 1) Exact value match
    for cat in QuestionCategory:
        if s == cat.value:
            return cat
    
    # 2) Case-insensitive value match
    s_lower = s.lower()
    for cat in QuestionCategory:
        if s_lower == cat.value.lower():
            return cat
    
    # 3) Enum name match (e.g., "informational" -> INFORMATIONAL)
    for cat in QuestionCategory:
        if s_lower == cat.name.lower():
            return cat
    
    # Default fallback
    return QuestionCategory.INFORMATIONAL


class QuestionGeneratorAgent:
    """
    Agent responsible for generating categorized user questions.
    
    Uses Groq LLM to generate diverse, relevant questions across 5 categories:
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
        
        Uses Groq LLM to generate at least 15 questions across 5 different 
        categories. Includes automatic retry logic with LLM regeneration and 
        template-based fallback to meet minimum question count.
        
        Args:
            product: Validated ProductModel
            
        Returns:
            Tuple of (list of QuestionModels, list of errors, agent_metrics dict)
        """
        logger.info(f"{self.name}: Generating questions for {product.name}")
        errors: List[str] = []
        questions: List[QuestionModel] = []
        agent_metrics = {"tokens_in": 0, "tokens_out": 0, "output_len": 0, "prompts": {}}
        
        try:
            # Generate questions using LLM with metrics tracking
            prompt = self._build_prompt(product)
            logger.debug(f"{self.name}: Calling Groq for question generation")
            
            # Use invoke_with_metrics for automatic metrics tracking
            raw_response, metrics, prompt_text = invoke_with_metrics(prompt)
            
            # Aggregate metrics
            agent_metrics["tokens_in"] += metrics.get("tokens_in", 0)
            agent_metrics["tokens_out"] += metrics.get("tokens_out", 0)
            agent_metrics["output_len"] += metrics.get("output_len", 0)
            agent_metrics["prompts"][metrics["prompt_hash"]] = prompt_text
            
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
            return questions, errors, agent_metrics
            
        except Exception as e:
            error = f"Error generating questions: {str(e)}"
            logger.error(f"{self.name}: {error}")
            errors.append(error)
            
            # Return fallback questions
            fallback = self._generate_fallback_questions(product)
            return fallback, errors, agent_metrics
    
    def _build_prompt(self, product: ProductModel) -> str:
        """Build the prompt for question generation."""
        return f"""Generate exactly {self.min_questions} user questions about this product.
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
- Generate exactly {self.min_questions} questions total
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
            
            # Robust JSON extraction: find JSON array even with leading/trailing text
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                response = json_match.group()
            
            # Parse JSON
            parsed = json.loads(response)
            
            # Comment 4: Handle non-list responses by attempting to locate 'questions' array
            if not isinstance(parsed, list):
                logger.warning(
                    "%s: LLM response root is %s, attempting to locate 'questions' array",
                    self.name,
                    type(parsed).__name__
                )
                if isinstance(parsed, dict):
                    candidate = parsed.get("questions") or parsed.get("items")
                    if isinstance(candidate, list):
                        parsed = candidate
                    else:
                        logger.warning(
                            "%s: No usable list found under 'questions' or 'items'; falling back to defaults",
                            self.name
                        )
                        return self._generate_fallback_questions(product)
                else:
                    logger.warning(
                        "%s: Non-list, non-dict JSON root; falling back to defaults",
                        self.name
                    )
                    return self._generate_fallback_questions(product)
            
            # Convert to QuestionModels using _to_question_category helper
            for i, item in enumerate(parsed):
                if isinstance(item, dict) and "question" in item:
                    category_str = item.get("category", "Informational")
                    category = _to_question_category(category_str)
                    
                    # Log if unknown category was mapped to default
                    if category == QuestionCategory.INFORMATIONAL and category_str:
                        if category_str.lower() not in (
                            QuestionCategory.INFORMATIONAL.value.lower(),
                            QuestionCategory.INFORMATIONAL.name.lower()
                        ):
                            logger.warning(
                                "%s: Unknown category '%s' for question %d, falling back to INFORMATIONAL",
                                self.name,
                                category_str,
                                i + 1
                            )
                    
                    question = QuestionModel(
                        id=f"q{i+1}",
                        category=category,
                        question=item["question"]
                    )
                    questions.append(question)
            
            return questions
            
        except json.JSONDecodeError as e:
            logger.error(f"{self.name}: Failed to parse JSON: {e}, response: {response[:200]}...")
            return self._generate_fallback_questions(product)
    
    def _generate_additional_questions(
        self, 
        product: ProductModel, 
        existing: List[QuestionModel]
    ) -> List[QuestionModel]:
        """
        Generate additional questions to meet minimum requirement.
        
        Uses a regeneration loop:
        1. First tries LLM-based regeneration with exclusion list
        2. Falls back to template-based questions if LLM fails
        
        Args:
            product: Product model
            existing: List of already generated questions
            
        Returns:
            List of additional questions needed to meet min_questions
        """
        existing_count = len(existing)
        needed = self.min_questions - existing_count
        
        if needed <= 0:
            return []
        
        logger.info(f"{self.name}: Need {needed} more questions, attempting LLM regeneration")
        
        # Step 1: Try LLM-based regeneration with exclusion list
        try:
            existing_questions = [q.question for q in existing]
            additional = self._regenerate_with_llm(product, existing_questions, needed)
            if len(additional) >= needed:
                logger.info(f"{self.name}: LLM regeneration successful, got {len(additional)} questions")
                return additional[:needed]
        except Exception as e:
            logger.warning(f"{self.name}: LLM regeneration failed: {e}, using templates")
        
        # Step 2: Fall back to template-based questions
        logger.info(f"{self.name}: Using template-based fallback for {needed} questions")
        return self._template_fallback_questions(product, existing_count, needed)
    
    def _regenerate_with_llm(
        self,
        product: ProductModel,
        existing_questions: List[str],
        count: int
    ) -> List[QuestionModel]:
        """
        Regenerate questions using LLM with exclusion list.
        
        Args:
            product: Product model
            existing_questions: List of questions to exclude
            count: Number of new questions needed
            
        Returns:
            List of new QuestionModels
        """
        exclusion_list = "\n".join(f"- {q}" for q in existing_questions[:10])  # Limit to 10 for prompt size
        
        prompt = f"""Generate {count} ADDITIONAL user questions about this product.
These questions must be DIFFERENT from the existing ones listed below.

Product: {product.name}
Type: {product.product_type}
Key Features: {', '.join(product.key_features)}
Benefits: {', '.join(product.benefits)}
Price: {product.price}

EXISTING QUESTIONS (do NOT repeat these):
{exclusion_list}

Generate {count} NEW questions across categories: Informational, Safety, Usage, Purchase, Comparison.
Output ONLY a JSON array: [{{"category": "X", "question": "Y?"}}]"""

        response = invoke_with_retry(prompt)
        response = response.strip()
        
        # Clean markdown fences
        if "```" in response:
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        response = response.strip()
        
        # Robust JSON extraction
        import re
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            response = json_match.group()
        
        data = json.loads(response)
        
        questions = []
        for i, item in enumerate(data):
            if isinstance(item, dict) and "question" in item:
                category = _to_question_category(item.get("category", "Informational"))
                questions.append(QuestionModel(
                    id=f"q_regen_{i+1}",
                    category=category,
                    question=item["question"]
                ))
        
        return questions
    
    def _template_fallback_questions(
        self,
        product: ProductModel,
        existing_count: int,
        needed: int
    ) -> List[QuestionModel]:
        """Generate template-based fallback questions."""
        additional = []
        
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
        """Generate fallback questions using LLM with retry logic."""
        logger.info(f"{self.name}: Generating fallback questions via LLM with retry")
        
        max_attempts = 3
        
        for attempt in range(max_attempts):
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
                
                # Validate we got enough questions
                if len(questions) >= 15:
                    logger.info(f"{self.name}: Fallback generated {len(questions)} questions")
                    return questions[:15]
                else:
                    logger.warning(f"{self.name}: Fallback attempt {attempt+1} only got {len(questions)} questions")
                    if attempt < max_attempts - 1:
                        continue  # Retry
                    
            except Exception as e:
                logger.warning(f"{self.name}: Fallback attempt {attempt+1} failed: {e}")
                if attempt < max_attempts - 1:
                    continue  # Retry
        
        # Absolute minimal fallback with 15 questions (only if all retries fail)
        logger.warning(f"{self.name}: All fallback attempts failed, using template questions")
        return [
            QuestionModel(id="q1", category=QuestionCategory.INFORMATIONAL, question=f"What is {product.name}?"),
            QuestionModel(id="q2", category=QuestionCategory.INFORMATIONAL, question=f"What does {product.name} do?"),
            QuestionModel(id="q3", category=QuestionCategory.INFORMATIONAL, question=f"What are the key features of {product.name}?"),
            QuestionModel(id="q4", category=QuestionCategory.USAGE, question=f"How do I use {product.name}?"),
            QuestionModel(id="q5", category=QuestionCategory.USAGE, question=f"How often should I use {product.name}?"),
            QuestionModel(id="q6", category=QuestionCategory.USAGE, question=f"When is the best time to use {product.name}?"),
            QuestionModel(id="q7", category=QuestionCategory.SAFETY, question=f"Are there any issues with {product.name}?"),
            QuestionModel(id="q8", category=QuestionCategory.SAFETY, question=f"Who should not use {product.name}?"),
            QuestionModel(id="q9", category=QuestionCategory.SAFETY, question=f"What precautions should I take with {product.name}?"),
            QuestionModel(id="q10", category=QuestionCategory.PURCHASE, question=f"What is the price of {product.name}?"),
            QuestionModel(id="q11", category=QuestionCategory.PURCHASE, question=f"Is {product.name} worth the price?"),
            QuestionModel(id="q12", category=QuestionCategory.PURCHASE, question=f"Where can I buy {product.name}?"),
            QuestionModel(id="q13", category=QuestionCategory.COMPARISON, question=f"How does {product.name} compare to alternatives?"),
            QuestionModel(id="q14", category=QuestionCategory.COMPARISON, question=f"What makes {product.name} different from competitors?"),
            QuestionModel(id="q15", category=QuestionCategory.COMPARISON, question=f"Is {product.name} better than similar products?"),
        ]


