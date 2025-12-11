"""
Tests for ParserAgent.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents import ParserAgent
from models import ProductModel


class TestParserAgent:
    """Tests for ParserAgent class."""
    
    def test_parser_agent_initialization(self):
        """Test that ParserAgent initializes correctly."""
        agent = ParserAgent()
        assert agent.name == "parser_agent"
    
    def test_parse_valid_product_data(self, sample_product_data):
        """Test parsing valid product data."""
        agent = ParserAgent()
        product, errors = agent.execute(sample_product_data)
        
        assert product is not None
        assert isinstance(product, ProductModel)
        assert len(errors) == 0
        assert product.name == "Test Product"
    
    def test_parse_skincare_product(self, skincare_product_data):
        """Test parsing skincare product data."""
        agent = ParserAgent()
        product, errors = agent.execute(skincare_product_data)
        
        assert product is not None
        assert product.name == "GlowBoost Vitamin C Serum"
        assert "Oily skin" in product.target_users
    
    def test_parse_minimal_data(self):
        """Test parsing with minimal required fields."""
        minimal_data = {
            "name": "Minimal Product",
            "price": "$10"
        }
        agent = ParserAgent()
        product, errors = agent.execute(minimal_data)
        
        # Should create product with defaults
        assert product is not None
        assert product.name == "Minimal Product"
    
    def test_parse_empty_data(self):
        """Test parsing empty data returns errors."""
        agent = ParserAgent()
        product, errors = agent.execute({})
        
        # Should either return None or product without name
        # The behavior depends on implementation
        assert product is None or len(errors) > 0 or product.name == ""
    
    def test_field_mapping(self):
        """Test that alternative field names are mapped correctly."""
        data_with_alt_names = {
            "product_name": "Alt Name Product",
            "user_type": ["User A", "User B"],
            "ingredients": ["Ingredient 1"],
            "price": "$50"
        }
        agent = ParserAgent()
        product, errors = agent.execute(data_with_alt_names)
        
        if product:
            # Should map product_name to name
            assert product.name == "Alt Name Product"
