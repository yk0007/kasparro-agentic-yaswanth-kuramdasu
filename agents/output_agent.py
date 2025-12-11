"""
Output Agent.

Responsible for formatting and saving final JSON outputs.
Single responsibility: Validate against templates, add metadata, write files.
"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, Any, Tuple, List


from templates import FAQTemplate, ProductTemplate, ComparisonTemplate


logger = logging.getLogger(__name__)


class OutputAgent:
    """
    Agent responsible for formatting and saving JSON outputs.
    
    Takes all generated content, validates against templates,
    adds metadata, and writes to the output directory.
    
    Attributes:
        name: Agent identifier
        output_dir: Directory for output files
    """
    
    name: str = "output_agent"
    output_dir: str = "output"
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize the Output Agent.
        
        Args:
            output_dir: Directory to write output files
        """
        self.output_dir = output_dir
        self._ensure_output_dir()
        logger.info(f"Initialized {self.name}, output dir: {self.output_dir}")
    
    def _ensure_output_dir(self) -> None:
        """Ensure output directory exists."""
        # Get absolute path relative to project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.output_path = os.path.join(project_root, self.output_dir)
        os.makedirs(self.output_path, exist_ok=True)
    
    def execute(
        self,
        faq_content: Dict[str, Any],
        product_content: Dict[str, Any],
        comparison_content: Dict[str, Any]
    ) -> Tuple[List[str], List[str]]:
        """
        Format and save all content as JSON files.
        
        Validates each content type against its template,
        adds metadata, and writes to output directory.
        
        Args:
            faq_content: FAQ page content
            product_content: Product page content
            comparison_content: Comparison page content
            
        Returns:
            Tuple of (list of output file paths, list of errors)
        """
        logger.info(f"{self.name}: Starting output generation")
        output_files: List[str] = []
        errors: List[str] = []
        
        # Process FAQ
        try:
            faq_path = self._process_faq(faq_content)
            output_files.append(faq_path)
            logger.info(f"{self.name}: Generated {faq_path}")
        except Exception as e:
            error = f"Failed to generate FAQ: {str(e)}"
            logger.error(f"{self.name}: {error}")
            errors.append(error)
        
        # Process Product Page
        try:
            product_path = self._process_product_page(product_content)
            output_files.append(product_path)
            logger.info(f"{self.name}: Generated {product_path}")
        except Exception as e:
            error = f"Failed to generate product page: {str(e)}"
            logger.error(f"{self.name}: {error}")
            errors.append(error)
        
        # Process Comparison Page
        try:
            comparison_path = self._process_comparison(comparison_content)
            output_files.append(comparison_path)
            logger.info(f"{self.name}: Generated {comparison_path}")
        except Exception as e:
            error = f"Failed to generate comparison page: {str(e)}"
            logger.error(f"{self.name}: {error}")
            errors.append(error)
        
        logger.info(f"{self.name}: Generated {len(output_files)} output files")
        return output_files, errors
    
    def _process_faq(self, content: Dict[str, Any]) -> str:
        """Process and save FAQ content."""
        template = FAQTemplate()
        
        # Extract blocks for metadata
        blocks = content.pop("blocks", {})
        
        # Validate
        is_valid, validation_errors = template.validate(content)
        if not is_valid:
            logger.warning(f"{self.name}: FAQ validation issues: {validation_errors}")
        
        # Build output structure
        output = {
            "page_type": "faq",
            "product_name": content.get("product_name", ""),
            "questions": content.get("questions", []),
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "agent": self.name,
                "version": "1.0",
                "total_questions": len(content.get("questions", [])),
                "logic_blocks_used": list(blocks.keys())
            }
        }
        
        # Write to file
        filepath = os.path.join(self.output_path, "faq.json")
        self._write_json(filepath, output)
        
        return filepath
    
    def _process_product_page(self, content: Dict[str, Any]) -> str:
        """Process and save product page content."""
        template = ProductTemplate()
        
        # Extract blocks for metadata
        blocks = content.pop("blocks", {})
        
        # Build output structure  
        product_data = content.get("product", {})
        
        output = {
            "page_type": "product",
            "product": {
                "name": product_data.get("name", ""),
                "tagline": product_data.get("tagline", ""),
                "headline": product_data.get("headline", ""),
                "description": product_data.get("description", ""),
                "product_type": product_data.get("product_type", ""),
                "key_features": product_data.get("key_features", []),
                "ingredients": product_data.get("ingredients", {}),
                "benefits": product_data.get("benefits", {}),
                "how_to_use": product_data.get("how_to_use", {}),
                "suitable_for": product_data.get("suitable_for", []),
                "safety_information": product_data.get("safety_information", {}),
                "price": product_data.get("price", {})
            },
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "agent": self.name,
                "version": "1.0",
                "logic_blocks_used": list(blocks.keys())
            }
        }
        
        # Write to file
        filepath = os.path.join(self.output_path, "product_page.json")
        self._write_json(filepath, output)
        
        return filepath
    
    def _process_comparison(self, content: Dict[str, Any]) -> str:
        """Process and save comparison page content."""
        template = ComparisonTemplate()
        
        # Extract blocks for metadata
        blocks = content.pop("blocks", {})
        
        # Build output structure
        output = {
            "page_type": "comparison",
            "products": content.get("products", {}),
            "comparison": content.get("comparison", {}),
            "recommendation": content.get("recommendation", ""),
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "agent": self.name,
                "version": "1.0",
                "logic_blocks_used": list(blocks.keys())
            }
        }
        
        # Write to file
        filepath = os.path.join(self.output_path, "comparison_page.json")
        self._write_json(filepath, output)
        
        return filepath
    
    def _write_json(self, filepath: str, data: Dict[str, Any]) -> None:
        """Write data to JSON file with pretty formatting."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_output_paths(self) -> Dict[str, str]:
        """Get paths to all output files."""
        return {
            "faq": os.path.join(self.output_path, "faq.json"),
            "product_page": os.path.join(self.output_path, "product_page.json"),
            "comparison_page": os.path.join(self.output_path, "comparison_page.json")
        }
