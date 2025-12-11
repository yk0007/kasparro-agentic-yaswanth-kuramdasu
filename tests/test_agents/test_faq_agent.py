"""
Tests for FAQAgent.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents import FAQAgent
from models import QuestionModel, QuestionCategory


class TestFAQAgent:
    """Tests for FAQAgent class."""
    
    def test_faq_agent_initialization(self):
        """Test that FAQAgent initializes correctly."""
        agent = FAQAgent()
        assert agent.name == "faq_agent"
        assert agent.min_faqs == 15  # Per assignment requirement
    
    def test_min_faqs_constant(self):
        """Test that MIN_FAQ_QUESTIONS constant is 15."""
        assert FAQAgent.MIN_FAQ_QUESTIONS == 15
    
    def test_select_questions_returns_minimum(self, sample_product):
        """Test that _select_questions returns at least min_faqs questions."""
        agent = FAQAgent()
        
        # Create mock questions
        questions = []
        for i in range(20):
            category = list(QuestionCategory)[i % len(QuestionCategory)]
            questions.append(QuestionModel(
                id=f"q{i}",
                category=category,
                question=f"Test question {i}?"
            ))
        
        selected = agent._select_questions(questions)
        
        # Should select at least min_faqs (15) questions
        assert len(selected) >= agent.min_faqs
    
    def test_select_questions_category_diversity(self, sample_product):
        """Test that _select_questions includes questions from multiple categories."""
        agent = FAQAgent()
        
        # Create questions from different categories
        questions = []
        for i, category in enumerate(QuestionCategory):
            for j in range(4):
                questions.append(QuestionModel(
                    id=f"q{i}_{j}",
                    category=category,
                    question=f"Test question {i}_{j}?"
                ))
        
        selected = agent._select_questions(questions)
        
        # Should have questions from multiple categories
        selected_categories = set(q.category for q in selected)
        assert len(selected_categories) >= 3  # At least 3 different categories
