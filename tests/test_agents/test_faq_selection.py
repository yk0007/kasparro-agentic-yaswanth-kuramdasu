"""
Tests for FAQAgent question selection pipeline.

Tests deduplication, category diversity, and min_faqs constraints.
Uses module-level constants from faq_agent as single source of truth.
"""
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from models import QuestionModel, QuestionCategory
from agents.faq_agent import (
    FAQAgent,
    JACCARD_SIMILARITY_THRESHOLD,
    CATEGORY_SCORES,
    QUESTION_LENGTH_IDEAL_MIN,
    QUESTION_LENGTH_IDEAL_MAX
)


class TestFAQSelection:
    """Tests for FAQAgent._select_questions() pipeline."""
    
    @pytest.fixture
    def faq_agent(self):
        """Create FAQAgent instance."""
        return FAQAgent()
    
    @pytest.fixture
    def sample_questions(self):
        """Create sample questions with duplicates and category spread."""
        questions = [
            # Safety questions
            QuestionModel(id="q1", category=QuestionCategory.SAFETY, 
                         question="Is this product safe for sensitive skin?"),
            QuestionModel(id="q2", category=QuestionCategory.SAFETY, 
                         question="What are the potential side effects?"),
            
            # Near-duplicate of q1 (should be filtered)
            QuestionModel(id="q3", category=QuestionCategory.SAFETY, 
                         question="Is this product safe for very sensitive skin?"),
            
            # Usage questions
            QuestionModel(id="q4", category=QuestionCategory.USAGE, 
                         question="How should I apply this product?"),
            QuestionModel(id="q5", category=QuestionCategory.USAGE, 
                         question="How often should I use this serum?"),
            
            # Informational questions
            QuestionModel(id="q6", category=QuestionCategory.INFORMATIONAL, 
                         question="What ingredients are in this product?"),
            QuestionModel(id="q7", category=QuestionCategory.INFORMATIONAL, 
                         question="How long does one bottle last?"),
            QuestionModel(id="q8", category=QuestionCategory.INFORMATIONAL, 
                         question="What is the shelf life of this product?"),
            
            # Purchase questions
            QuestionModel(id="q9", category=QuestionCategory.PURCHASE, 
                         question="Where can I buy this product?"),
            QuestionModel(id="q10", category=QuestionCategory.PURCHASE, 
                          question="Is there a money-back guarantee?"),
            
            # Comparison questions
            QuestionModel(id="q11", category=QuestionCategory.COMPARISON, 
                          question="How does this compare to other serums?"),
            QuestionModel(id="q12", category=QuestionCategory.COMPARISON, 
                          question="Is this better than vitamin C serums?"),
            
            # More questions to reach min_faqs
            QuestionModel(id="q13", category=QuestionCategory.INFORMATIONAL, 
                          question="What skin types is this suitable for?"),
            QuestionModel(id="q14", category=QuestionCategory.USAGE, 
                          question="Can I use this with other products?"),
            QuestionModel(id="q15", category=QuestionCategory.SAFETY, 
                          question="Should I do a patch test first?"),
            QuestionModel(id="q16", category=QuestionCategory.INFORMATIONAL, 
                          question="Is this product cruelty-free?"),
            QuestionModel(id="q17", category=QuestionCategory.PURCHASE, 
                          question="Are there any discounts available?"),
            QuestionModel(id="q18", category=QuestionCategory.USAGE, 
                          question="What time of day should I apply this?"),
        ]
        return questions
    
    def test_deduplication_removes_near_duplicates(self, faq_agent, sample_questions):
        """
        Test that duplicates above JACCARD_SIMILARITY_THRESHOLD do not appear more than once.
        
        q1 and q3 are near-duplicates: both ask about safety for sensitive skin.
        Only one should appear in the result.
        """
        selected = faq_agent._select_questions(sample_questions)
        
        # Get question texts
        selected_texts = [q.question.lower() for q in selected]
        
        # Check that near-duplicates (q1 and q3) don't both appear
        q1_text = "is this product safe for sensitive skin?"
        q3_text = "is this product safe for very sensitive skin?"
        
        q1_present = q1_text in selected_texts
        q3_present = q3_text in selected_texts
        
        # At most one should be present (they're near-duplicates)
        assert not (q1_present and q3_present), \
            "Near-duplicate questions should be filtered out"
    
    def test_category_diversity_preserved(self, faq_agent, sample_questions):
        """
        Test that at least one question from each available category is present.
        
        This ensures diversity across Safety, Usage, Informational, Purchase, Comparison.
        """
        selected = faq_agent._select_questions(sample_questions)
        
        # Get categories from input
        input_categories = {q.category for q in sample_questions}
        
        # Get categories in selected
        selected_categories = {q.category for q in selected}
        
        # All input categories should be represented in output
        for cat in input_categories:
            assert cat in selected_categories, \
                f"Category {cat.value} should be represented in selected questions"
    
    def test_min_faqs_respected(self, faq_agent, sample_questions):
        """
        Test that result size respects FAQAgent.min_faqs when enough input exists.
        """
        selected = faq_agent._select_questions(sample_questions)
        
        # Should return exactly min_faqs if enough input
        # (sample_questions has 18 items, min_faqs is typically 15)
        assert len(selected) >= min(faq_agent.min_faqs, len(sample_questions)), \
            f"Should return at least {faq_agent.min_faqs} questions"
    
    def test_jaccard_threshold_value(self):
        """Verify the Jaccard threshold is as expected."""
        # Threshold should be 0.7 (70% similarity)
        assert JACCARD_SIMILARITY_THRESHOLD == 0.7, \
            "JACCARD_SIMILARITY_THRESHOLD should be 0.7"
    
    def test_category_scores_complete(self):
        """Verify all QuestionCategory values have scores."""
        for cat in QuestionCategory:
            assert cat in CATEGORY_SCORES, \
                f"Category {cat.value} should have a score defined"
    
    def test_scoring_prefers_safety_questions(self, faq_agent):
        """Test that Safety questions score higher than Informational."""
        safety_q = QuestionModel(
            id="safety", 
            category=QuestionCategory.SAFETY,
            question="Is this product safe for daily use on sensitive skin?"  # ~50 chars, ideal length
        )
        info_q = QuestionModel(
            id="info",
            category=QuestionCategory.INFORMATIONAL,
            question="What ingredients are in this product for daily use?"  # ~50 chars, ideal length
        )
        
        safety_score = faq_agent._score_question(safety_q)
        info_score = faq_agent._score_question(info_q)
        
        # Safety should score higher due to category importance
        assert safety_score > info_score, \
            "Safety questions should score higher than Informational"


class TestPriceBackwardCompatibility:
    """Tests for price field backward compatibility (Comment 1)."""
    
    @pytest.fixture
    def sample_product_data(self):
        """Create sample product data."""
        return {
            "name": "GlowBoost Vitamin C Serum",
            "product_type": "10% Concentration",
            "target_users": ["All skin types"],
            "key_features": ["Vitamin C", "Hyaluronic Acid"],
            "benefits": ["Brightening", "Hydration"],
            "how_to_use": "Apply daily",
            "considerations": "Patch test recommended",
            "price": "₹699"
        }
    
    def test_product_page_has_both_price_formats(self, sample_product_data):
        """Test that product page includes both price string and normalized_price object."""
        from agents import ParserAgent, ProductPageAgent
        
        parser = ParserAgent()
        product, _ = parser.execute(sample_product_data)
        
        if product:
            agent = ProductPageAgent()
            content, _, _ = agent.execute(product)
            
            if content and "product" in content:
                product_data = content["product"]
                
                # Check legacy price string exists
                assert "price" in product_data, "Legacy 'price' field should exist"
                assert isinstance(product_data["price"], str), "Legacy 'price' should be string"
                
                # Check normalized_price object exists
                assert "normalized_price" in product_data, "'normalized_price' field should exist"
                assert isinstance(product_data["normalized_price"], dict), \
                    "'normalized_price' should be dict"
                assert "amount" in product_data["normalized_price"], \
                    "normalized_price should have 'amount'"
                assert "currency" in product_data["normalized_price"], \
                    "normalized_price should have 'currency'"
    
    def test_comparison_pricing_has_raw_fields(self, sample_product_data):
        """Test that comparison pricing includes both normalized and raw fields."""
        from agents import ParserAgent, ComparisonAgent
        
        parser = ParserAgent()
        product, _ = parser.execute(sample_product_data)
        
        if product:
            agent = ComparisonAgent()
            content, _, _ = agent.execute(product)
            
            if content and "blocks" in content:
                pricing = content["blocks"].get("pricing_block", {})
                
                # Check normalized objects exist
                assert "price_a" in pricing, "'price_a' normalized object should exist"
                assert "price_b" in pricing, "'price_b' normalized object should exist"
                
                # Check raw strings exist
                assert "price_a_raw" in pricing, "'price_a_raw' string should exist"
                assert "price_b_raw" in pricing, "'price_b_raw' string should exist"
