"""
FAQ Agent.

Responsible for creating FAQ page content with questions and answers.
Single responsibility: Select questions and generate answers using logic blocks.
"""

import logging
import json
from typing import List, Dict, Any, Tuple


from models import ProductModel, QuestionModel, QuestionCategory
from config import invoke_with_retry, invoke_with_metrics
from logic_blocks import (
    generate_benefits_block,
    generate_usage_block,
    generate_safety_block
)


logger = logging.getLogger(__name__)


# =============================================================================
# FAQ Selection Constants (Comment 3)
# =============================================================================
# These constants control the question selection behavior. They are documented
# here to facilitate tuning and testing.

# Jaccard similarity threshold for deduplication (0.0-1.0)
# Set to 0.7 to treat questions as duplicates only when they share >70% of words
# This keeps phrasing variants that add nuance while collapsing truly redundant questions
JACCARD_SIMILARITY_THRESHOLD = 0.7

# Question length scoring thresholds (in characters)
# Ideal length range gets highest bonus; acceptable range gets smaller bonus
QUESTION_LENGTH_IDEAL_MIN = 40
QUESTION_LENGTH_IDEAL_MAX = 100
QUESTION_LENGTH_ACCEPTABLE_MIN = 20
QUESTION_LENGTH_ACCEPTABLE_MAX = 150

# Category importance scores for FAQ prioritization
# Safety/Usage questions are more critical than informational ones
CATEGORY_SCORES = {
    QuestionCategory.SAFETY: 2.5,      # Highest priority - user safety is paramount
    QuestionCategory.USAGE: 2.0,       # High priority - practical usage info
    QuestionCategory.COMPARISON: 1.5,  # Medium priority - competitive context
    QuestionCategory.INFORMATIONAL: 1.0,
    QuestionCategory.PURCHASE: 1.0,
}


class FAQAgent:
    """
    Agent responsible for creating FAQ page content.
    
    Selects a subset of generated questions (minimum 5) and generates
    comprehensive answers using logic blocks and LLM.
    
    Attributes:
        name: Agent identifier
        min_faqs: Minimum number of FAQ items
    """
    
    # Minimum FAQ items required per assignment specification
    MIN_FAQ_QUESTIONS: int = 15
    
    name: str = "faq_agent"
    min_faqs: int = MIN_FAQ_QUESTIONS
    
    def __init__(self):
        """Initialize the FAQ Agent."""
        logger.info(f"Initialized {self.name}")
    
    def execute(
        self, 
        product: ProductModel, 
        questions: List[QuestionModel]
    ) -> Tuple[Dict[str, Any], List[str], Dict[str, Any]]:
        """
        Create FAQ page content.
        
        Selects diverse questions from different categories and generates
        detailed answers using logic blocks and LLM.
        
        Args:
            product: Validated ProductModel
            questions: List of generated questions
            
        Returns:
            Tuple of (FAQ content dict, list of errors, agent_metrics dict)
        """
        logger.info(f"{self.name}: Creating FAQ for {product.name}")
        errors: List[str] = []
        agent_metrics = {"tokens_in": 0, "tokens_out": 0, "output_len": 0, "prompts": {}}
        
        try:
            # Select questions for FAQ (ensure diversity)
            selected = self._select_questions(questions)
            logger.info(f"{self.name}: Selected {len(selected)} questions for FAQ")
            
            # Generate logic blocks
            blocks = self._generate_blocks(product)
            
            # Generate answers for each question with metrics tracking
            faq_items = []
            for question in selected:
                answer, blocks_used, call_metrics = self._generate_answer(product, question, blocks)
                faq_items.append({
                    "id": question.id,
                    "category": question.category.value,
                    "question": question.question,
                    "answer": answer,
                    "logic_blocks_used": blocks_used
                })
                # Aggregate per-call metrics
                if call_metrics:
                    agent_metrics["tokens_in"] += call_metrics.get("tokens_in", 0)
                    agent_metrics["tokens_out"] += call_metrics.get("tokens_out", 0)
                    agent_metrics["output_len"] += call_metrics.get("output_len", 0)
                    if "prompt_hash" in call_metrics:
                        agent_metrics["prompts"][call_metrics["prompt_hash"]] = call_metrics.get("prompt_text", "")
            
            # Build final FAQ content
            faq_content = {
                "product_name": product.name,
                "questions": faq_items,
                "blocks": blocks
            }
            
            logger.info(f"{self.name}: Generated {len(faq_items)} FAQ items")
            return faq_content, errors, agent_metrics
            
        except Exception as e:
            error = f"Error creating FAQ: {str(e)}"
            logger.error(f"{self.name}: {error}")
            errors.append(error)
            return {}, errors, agent_metrics
    
    def _select_questions(self, questions: List[QuestionModel]) -> List[QuestionModel]:
        """
        Select diverse, high-quality questions for FAQ.
        
        Uses:
        - Deduplication: removes near-duplicate questions
        - Scoring: prioritizes questions by quality metrics
        - Category diversity: ensures coverage across categories
        
        Args:
            questions: All generated questions
            
        Returns:
            Selected questions for FAQ (minimum 15)
        """
        # Step 1: Deduplicate questions
        unique_questions = self._deduplicate_questions(questions)
        logger.debug(f"{self.name}: {len(questions)} -> {len(unique_questions)} after deduplication")
        
        # Step 2: Score and sort questions
        scored_questions = [(q, self._score_question(q)) for q in unique_questions]
        scored_questions.sort(key=lambda x: x[1], reverse=True)
        
        # Step 3: Select with category diversity
        selected = []
        by_category: Dict[QuestionCategory, List[QuestionModel]] = {}
        
        # Group by category
        for q, score in scored_questions:
            if q.category not in by_category:
                by_category[q.category] = []
            by_category[q.category].append(q)
        
        # Select top question from each category first (ensures diversity)
        for category in QuestionCategory:
            if category in by_category and by_category[category]:
                selected.append(by_category[category][0])
        
        # Fill remaining slots with highest-scored questions
        for q, score in scored_questions:
            if len(selected) >= self.min_faqs:
                break
            if q not in selected:
                selected.append(q)
        
        logger.info(f"{self.name}: Selected {len(selected)} questions (min required: {self.min_faqs})")
        return selected[:self.min_faqs]
    
    def _deduplicate_questions(self, questions: List[QuestionModel]) -> List[QuestionModel]:
        """
        Remove near-duplicate questions using Jaccard word-overlap similarity.
        
        The JACCARD_SIMILARITY_THRESHOLD is set to filter out questions that share
        too much content while keeping phrasing variants that add genuine nuance.
        
        Args:
            questions: List of questions to deduplicate
            
        Returns:
            List of unique questions with duplicates removed
        """
        unique = []
        for q in questions:
            is_duplicate = False
            q_words = set(q.question.lower().split())
            for existing in unique:
                existing_words = set(existing.question.lower().split())
                # Check word overlap (Jaccard similarity)
                if len(q_words) > 0 and len(existing_words) > 0:
                    intersection = len(q_words & existing_words)
                    union = len(q_words | existing_words)
                    similarity = intersection / union
                    if similarity > JACCARD_SIMILARITY_THRESHOLD:
                        is_duplicate = True
                        logger.debug(f"{self.name}: Duplicate detected: '{q.question[:50]}...'")
                        break
            if not is_duplicate:
                unique.append(q)
        return unique
    
    def _score_question(self, question: QuestionModel) -> float:
        """
        Score question quality on a 0-10 scale.
        
        Scoring factors (using module-level constants):
        - Length: Questions in the ideal range (40-100 chars) get +2.0;
                 acceptable range (20-150 chars) gets +1.0
        - Category: Safety/Usage > Comparison > Informational/Purchase,
                   to push more critical content into the FAQ
        - Specificity: Bonus for product-specific wording
        
        Args:
            question: The question to score
            
        Returns:
            Quality score from 0-10
        """
        score = 5.0  # Base score
        
        # Length scoring using module-level constants
        length = len(question.question)
        if QUESTION_LENGTH_IDEAL_MIN <= length <= QUESTION_LENGTH_IDEAL_MAX:
            score += 2.0
        elif QUESTION_LENGTH_ACCEPTABLE_MIN <= length <= QUESTION_LENGTH_ACCEPTABLE_MAX:
            score += 1.0
        
        # Category importance using module-level constant
        score += CATEGORY_SCORES.get(question.category, 1.0)
        
        # Specificity bonus (questions with product-specific terms)
        q_lower = question.question.lower()
        if any(term in q_lower for term in ["this product", "the serum", "this serum"]):
            score += 0.5
        
        return score
    
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
        
        # Generate answer using LLM with metrics tracking
        prompt = self._build_answer_prompt(product, question, relevant_data)
        
        try:
            answer, metrics, prompt_text = invoke_with_metrics(prompt)
            answer = answer.strip()
            
            # Clean up answer
            if answer.startswith('"') and answer.endswith('"'):
                answer = answer[1:-1]
            
            # Build call_metrics for aggregation
            call_metrics = {
                "tokens_in": metrics.get("tokens_in", 0),
                "tokens_out": metrics.get("tokens_out", 0),
                "output_len": metrics.get("output_len", 0),
                "prompt_hash": metrics.get("prompt_hash", ""),
                "prompt_text": prompt_text
            }
            
            return answer, blocks_used, call_metrics
            
        except Exception as e:
            logger.error(f"{self.name}: Error generating answer: {e}")
            # Return fallback answer with empty metrics
            return self._fallback_answer(product, question), blocks_used, {}
    
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

