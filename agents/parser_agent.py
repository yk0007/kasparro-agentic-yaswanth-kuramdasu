"""
Parser Agent.

Responsible for parsing and validating raw product data.
Single responsibility: Convert raw dict to validated ProductModel.
Handles flexible field names with automatic mapping.
"""

import logging
from typing import Dict, Any, Tuple, Optional, List
from pydantic import ValidationError

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ProductModel


logger = logging.getLogger(__name__)


# Field name mappings for flexibility
FIELD_MAPPINGS = {
    # name alternatives
    "name": ["name", "product_name", "title", "product_title"],
    # product_type alternatives  
    "product_type": ["product_type", "concentration", "type", "version", "strength", "potency", "formula"],
    # target_users alternatives
    "target_users": ["target_users", "skin_type", "skin_types", "user_type", "target_audience", "suitable_for", "for"],
    # key_features alternatives
    "key_features": ["key_features", "key_ingredients", "ingredients", "features", "active_ingredients"],
    # benefits alternatives
    "benefits": ["benefits", "advantages", "key_benefits", "pros"],
    # how_to_use alternatives
    "how_to_use": ["how_to_use", "usage", "instructions", "how_to", "directions"],
    # considerations alternatives
    "considerations": ["considerations", "side_effects", "warnings", "cautions", "notes", "limitations"],
    # price alternatives
    "price": ["price", "cost", "pricing", "amount"],
}


class ParserAgent:
    """
    Agent responsible for parsing and validating product data.
    
    This agent is the entry point of the workflow. It takes raw product
    JSON data and converts it to a validated ProductModel.
    Supports flexible field names with automatic mapping.
    
    Attributes:
        name: Agent identifier
    """
    
    name: str = "parser_agent"
    
    def __init__(self):
        """Initialize the Parser Agent."""
        logger.info(f"Initialized {self.name}")
    
    def _map_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map alternative field names to standard names.
        
        Args:
            data: Raw input data with potentially non-standard field names
            
        Returns:
            Data with standardized field names
        """
        mapped = {}
        used_keys = set()
        
        # Map known fields
        for standard_name, alternatives in FIELD_MAPPINGS.items():
            for alt in alternatives:
                if alt in data and alt not in used_keys:
                    value = data[alt]
                    # Convert string to list for list fields
                    if standard_name in ["target_users", "key_features", "benefits"]:
                        if isinstance(value, str):
                            value = [v.strip() for v in value.split(",")]
                    mapped[standard_name] = value
                    used_keys.add(alt)
                    break
        
        # Copy any unmapped fields as-is (for extensibility)
        for key, value in data.items():
            if key not in used_keys and key not in mapped:
                mapped[key] = value
        
        return mapped
    
    def _apply_defaults(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values for missing required fields."""
        defaults = {
            "name": data.get("product_name", "Product"),
            "product_type": "Standard",
            "target_users": ["All"],
            "key_features": data.get("key_features", ["Premium ingredients"]),
            "benefits": ["Quality product"],
            "how_to_use": "Use as directed",
            "considerations": "None known",
            "price": "Contact for pricing",
        }
        
        for field, default in defaults.items():
            if field not in data or not data[field]:
                data[field] = default
        
        return data
    
    def execute(self, product_data: Dict[str, Any]) -> Tuple[Optional[ProductModel], List[str]]:
        """
        Parse and validate product data.
        
        Takes raw product dictionary, maps field names, applies defaults,
        and validates against ProductModel schema.
        
        Args:
            product_data: Raw product dictionary from user input
            
        Returns:
            Tuple of (ProductModel or None, list of errors)
        """
        logger.info(f"{self.name}: Starting product data parsing")
        errors: List[str] = []
        
        try:
            # Validate input is a dict
            if not isinstance(product_data, dict):
                error = f"Expected dict, got {type(product_data).__name__}"
                logger.error(f"{self.name}: {error}")
                errors.append(error)
                return None, errors
            
            # Check for empty input
            if not product_data:
                error = "Product data is empty"
                logger.error(f"{self.name}: {error}")
                errors.append(error)
                return None, errors
            
            # Map field names to standard names
            mapped_data = self._map_fields(product_data)
            logger.debug(f"{self.name}: Mapped fields: {list(mapped_data.keys())}")
            
            # Apply defaults for missing fields
            mapped_data = self._apply_defaults(mapped_data)
            
            # Parse and validate using Pydantic
            logger.debug(f"{self.name}: Validating against ProductModel schema")
            product_model = ProductModel(**mapped_data)
            
            logger.info(f"{self.name}: Successfully parsed product: {product_model.name}")
            return product_model, errors
            
        except ValidationError as e:
            # Extract validation errors
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                msg = f"Validation error in '{field}': {error['msg']}"
                logger.error(f"{self.name}: {msg}")
                errors.append(msg)
            return None, errors
            
        except Exception as e:
            error = f"Unexpected error during parsing: {str(e)}"
            logger.error(f"{self.name}: {error}")
            errors.append(error)
            return None, errors
    
    def validate_structure(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Pre-validate data structure without full parsing.
        
        Quick check to ensure data is a non-empty dict.
        
        Args:
            data: Dictionary to validate
            
        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []
        
        if not isinstance(data, dict):
            issues.append("Input must be a JSON object")
        elif len(data) == 0:
            issues.append("Input cannot be empty")
        
        return len(issues) == 0, issues
