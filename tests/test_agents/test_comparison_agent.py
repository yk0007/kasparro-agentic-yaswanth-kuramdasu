"""
Tests for ComparisonAgent.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents import ComparisonAgent


class TestComparisonAgent:
    """Tests for ComparisonAgent class."""
    
    def test_comparison_agent_initialization(self):
        """Test that ComparisonAgent initializes correctly."""
        agent = ComparisonAgent()
        assert agent.name == "comparison_agent"
    
    def test_fallback_product_b(self, sample_product):
        """Test that fallback Product B is generated correctly."""
        agent = ComparisonAgent()
        product_b = agent._fallback_product_b(sample_product)
        
        assert product_b is not None
        assert product_b.name != sample_product.name  # Should be different
        assert len(product_b.key_features) > 0
    
    def test_product_to_dict(self, sample_product):
        """Test that product is converted to dict correctly."""
        agent = ComparisonAgent()
        result = agent._product_to_dict(sample_product)
        
        assert isinstance(result, dict)
        assert "name" in result
        assert "key_features" in result
        assert result["name"] == sample_product.name
    
    def test_no_grounding_import(self):
        """Test that comparison_agent does not import grounding functions."""
        # This test verifies that no external search is used
        import agents.comparison_agent as module
        source_code = open(module.__file__).read()
        
        assert "invoke_grounded" not in source_code
        assert "is_grounding_available" not in source_code
        assert "Google Search" not in source_code
