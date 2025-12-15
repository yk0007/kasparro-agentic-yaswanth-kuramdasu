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
        """Process and save FAQ content using template with strict validation."""
        template = FAQTemplate()
        # Use .get() instead of .pop() to avoid mutating original content
        blocks = content.get("blocks", {})
        content_copy = {k: v for k, v in content.items() if k != "blocks"}
        
        # Strict validation - all failures propagate (no fallback)
        output = template.render(content_copy, blocks)
        logger.info(f"{self.name}: FAQ validation passed")
        
        filepath = os.path.join(self.output_path, "faq.json")
        self._write_json(filepath, output)
        return filepath
    
    def _process_product_page(self, content: Dict[str, Any]) -> str:
        """Process and save product page content using template with strict validation."""
        template = ProductTemplate()
        # Use .get() instead of .pop() to avoid mutating original content
        blocks = content.get("blocks", {})
        content_copy = {k: v for k, v in content.items() if k != "blocks"}
        
        # Strict validation - all failures propagate (no fallback)
        output = template.render(content_copy, blocks)
        logger.info(f"{self.name}: Product page validation passed")
        
        filepath = os.path.join(self.output_path, "product_page.json")
        self._write_json(filepath, output)
        return filepath
    
    def _process_comparison(self, content: Dict[str, Any]) -> str:
        """Process and save comparison page content using template with strict validation."""
        template = ComparisonTemplate()
        # Use .get() instead of .pop() to avoid mutating original content
        blocks = content.get("blocks", {})
        content_copy = {k: v for k, v in content.items() if k != "blocks"}
        
        # Strict validation - all failures propagate (no fallback)
        output = template.render(content_copy, blocks)
        logger.info(f"{self.name}: Comparison page validation passed")
        
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
