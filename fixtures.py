"""
Fixtures for example product data.

Separates example data from core models for cleaner code organization.
"""

EXAMPLE_PRODUCT_DATA = {
    "name": "GlowBoost Vitamin C Serum",
    "product_type": "10% Vitamin C Serum",
    "target_users": ["Oily skin", "Combination skin", "Anti-aging enthusiasts"],
    "key_features": [
        "10% Vitamin C (L-Ascorbic Acid)",
        "Hyaluronic Acid",
        "Niacinamide",
        "Plant extracts"
    ],
    "benefits": [
        "Brightening",
        "Dark spot fading",
        "Antioxidant protection",
        "Hydration"
    ],
    "how_to_use": "Apply 2-3 drops to face and neck each morning after cleansing and toning. Follow with moisturizer and sunscreen.",
    "considerations": "May cause mild tingling for sensitive skin. Always patch test before first use.",
    "price": "₹699"
}


# Minimal example for testing
MINIMAL_PRODUCT_DATA = {
    "name": "Test Product",
    "price": "$99"
}


def get_example_product() -> dict:
    """Get example product data for UI defaults."""
    return EXAMPLE_PRODUCT_DATA.copy()
