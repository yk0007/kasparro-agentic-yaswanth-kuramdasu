"""
Pytest fixtures for Multi-Agent Content Generation System tests.
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ProductModel


@pytest.fixture
def sample_product_data():
    """Sample product data dictionary for testing."""
    return {
        "name": "Test Product",
        "product_type": "Software Tool",
        "target_users": ["Developers", "Testers"],
        "key_features": ["Feature 1", "Feature 2", "Feature 3"],
        "benefits": ["Benefit 1", "Benefit 2"],
        "how_to_use": "Install and run the application",
        "considerations": "Requires Python 3.9+",
        "price": "$99/month"
    }


@pytest.fixture
def sample_product(sample_product_data):
    """Sample ProductModel for testing."""
    return ProductModel(**sample_product_data)


@pytest.fixture
def skincare_product_data():
    """Sample skincare product data for testing."""
    return {
        "name": "GlowBoost Vitamin C Serum",
        "product_type": "10% Vitamin C Serum",
        "target_users": ["Oily skin", "Combination skin"],
        "key_features": ["Vitamin C", "Hyaluronic Acid"],
        "benefits": ["Brightening", "Dark spot fading"],
        "how_to_use": "Apply 2-3 drops to face and neck each morning",
        "considerations": "Mild tingling for sensitive skin",
        "price": "₹699"
    }


@pytest.fixture
def skincare_product(skincare_product_data):
    """Sample skincare ProductModel for testing."""
    return ProductModel(**skincare_product_data)
