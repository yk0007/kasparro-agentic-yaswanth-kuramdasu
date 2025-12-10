"""
Base Template for Content Generation.

Provides the abstract base class for all content templates.
Each template defines required fields, optional fields, and logic block dependencies.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime


class BaseTemplate(ABC):
    """
    Abstract base class for content templates.
    
    Templates define the structure and validation rules for generated content.
    Each template specifies required fields, optional fields, and which
    logic blocks are needed to generate the content.
    
    Attributes:
        template_type: Type identifier for the template (e.g., "faq", "product")
        required_fields: List of fields that must be present
        optional_fields: List of fields that may be present
        required_blocks: List of logic block names needed for this template
    """
    
    template_type: str = ""
    required_fields: List[str] = []
    optional_fields: List[str] = []
    required_blocks: List[str] = []
    
    def __init__(self):
        """Initialize the template."""
        self._errors: List[str] = []
        self._warnings: List[str] = []
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate data against template requirements.
        
        Checks that all required fields are present and non-empty.
        Additional validation can be implemented by subclasses.
        
        Args:
            data: Dictionary of content data to validate
            
        Returns:
            Tuple of (is_valid: bool, errors: List[str])
            
        Example:
            >>> template = FAQTemplate()
            >>> is_valid, errors = template.validate({"questions": []})
            >>> is_valid
            False
            >>> errors
            ["questions must have at least 5 items"]
        """
        self._errors = []
        self._warnings = []
        
        # Check required fields
        for field in self.required_fields:
            if field not in data:
                self._errors.append(f"Missing required field: {field}")
            elif data[field] is None or (isinstance(data[field], (str, list, dict)) and not data[field]):
                self._errors.append(f"Required field '{field}' is empty")
        
        # Run template-specific validation
        self._validate_specific(data)
        
        return len(self._errors) == 0, self._errors
    
    @abstractmethod
    def _validate_specific(self, data: Dict[str, Any]) -> None:
        """
        Template-specific validation rules.
        
        Override in subclasses to add custom validation.
        Add errors to self._errors list.
        
        Args:
            data: Dictionary of content data
        """
        pass
    
    def render(self, data: Dict[str, Any], blocks: Dict[str, Any]) -> Dict[str, Any]:
        """
        Render the final output using data and logic blocks.
        
        Validates data first, then applies template structure and adds metadata.
        
        Args:
            data: Dictionary of content data
            blocks: Dictionary of logic block outputs
            
        Returns:
            Rendered content dictionary with metadata
            
        Raises:
            ValueError: If validation fails
        """
        # Validate first
        is_valid, errors = self.validate(data)
        if not is_valid:
            raise ValueError(f"Validation failed: {'; '.join(errors)}")
        
        # Build the output structure
        output = self._render_structure(data, blocks)
        
        # Add metadata
        output["metadata"] = self._generate_metadata(blocks)
        
        return output
    
    @abstractmethod
    def _render_structure(self, data: Dict[str, Any], blocks: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build the output structure specific to this template.
        
        Override in subclasses to define the output format.
        
        Args:
            data: Dictionary of content data
            blocks: Dictionary of logic block outputs
            
        Returns:
            Rendered content dictionary (without metadata)
        """
        pass
    
    def _generate_metadata(self, blocks: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate metadata for the output.
        
        Args:
            blocks: Dictionary of logic block outputs
            
        Returns:
            Metadata dictionary
        """
        return {
            "generated_at": datetime.now().isoformat(),
            "template_type": self.template_type,
            "version": "1.0",
            "logic_blocks_used": list(blocks.keys())
        }
    
    def get_required_blocks(self) -> List[str]:
        """
        Get the list of required logic blocks for this template.
        
        Returns:
            List of logic block names
        """
        return self.required_blocks.copy()
    
    def get_template_info(self) -> Dict[str, Any]:
        """
        Get information about this template.
        
        Returns:
            Dictionary with template information
        """
        return {
            "type": self.template_type,
            "required_fields": self.required_fields,
            "optional_fields": self.optional_fields,
            "required_blocks": self.required_blocks
        }
