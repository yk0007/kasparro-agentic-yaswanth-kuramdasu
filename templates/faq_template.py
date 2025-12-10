"""
FAQ Template for Content Generation.

Defines the structure and validation for FAQ page content.
"""

from typing import Dict, List, Any
from templates.base_template import BaseTemplate


class FAQTemplate(BaseTemplate):
    """
    Template for FAQ page content.
    
    Requires minimum 5 questions with answers.
    Uses benefits, usage, and safety logic blocks for answer generation.
    """
    
    template_type: str = "faq"
    required_fields: List[str] = ["product_name", "questions"]
    optional_fields: List[str] = ["description", "category_summary"]
    required_blocks: List[str] = ["benefits_block", "usage_block", "safety_block"]
    
    # Minimum questions required
    MIN_QUESTIONS: int = 5
    
    def _validate_specific(self, data: Dict[str, Any]) -> None:
        """
        Validate FAQ-specific requirements.
        
        - Ensures minimum 5 questions
        - Validates question structure
        - Checks answers are present
        
        Args:
            data: Dictionary of content data
        """
        # Check questions exist and meet minimum
        if "questions" in data:
            questions = data["questions"]
            
            if not isinstance(questions, list):
                self._errors.append("questions must be a list")
                return
            
            if len(questions) < self.MIN_QUESTIONS:
                self._errors.append(
                    f"FAQ must have at least {self.MIN_QUESTIONS} questions, "
                    f"got {len(questions)}"
                )
            
            # Validate each question structure
            for i, q in enumerate(questions):
                if not isinstance(q, dict):
                    self._errors.append(f"Question {i+1} must be a dictionary")
                    continue
                
                # Check required question fields
                if "question" not in q or not q.get("question"):
                    self._errors.append(f"Question {i+1} is missing question text")
                
                if "answer" not in q or not q.get("answer"):
                    self._errors.append(f"Question {i+1} is missing answer")
                
                # Optional: check category
                if "category" in q and not q["category"]:
                    self._warnings.append(f"Question {i+1} has empty category")
    
    def _render_structure(
        self, 
        data: Dict[str, Any], 
        blocks: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build the FAQ output structure.
        
        Args:
            data: Dictionary of content data
            blocks: Dictionary of logic block outputs
            
        Returns:
            Rendered FAQ content dictionary
        """
        # Process questions to add logic block attribution
        processed_questions = []
        for i, q in enumerate(data["questions"]):
            processed_q = {
                "id": q.get("id", f"q{i+1}"),
                "category": q.get("category", "General"),
                "question": q["question"],
                "answer": q["answer"],
                "logic_blocks_used": q.get("logic_blocks_used", [])
            }
            processed_questions.append(processed_q)
        
        # Build category summary
        categories = {}
        for q in processed_questions:
            cat = q["category"]
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "page_type": self.template_type,
            "product_name": data["product_name"],
            "questions": processed_questions,
            "total_questions": len(processed_questions),
            "category_summary": categories
        }
