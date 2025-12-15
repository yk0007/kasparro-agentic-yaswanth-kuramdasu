"""
Safety Logic Block.

Transforms product safety information using LLM with risk assessment.
Includes severity scoring, contraindications, and detailed mitigations.
"""

from typing import Dict, List, Any
import json
import logging

from models import ProductModel
from config import invoke_with_retry
from utils import clean_json_response

logger = logging.getLogger(__name__)


def generate_safety_block(product: ProductModel) -> Dict[str, Any]:
    """
    Transform product safety info with deep risk assessment.
    
    Provides:
    - Severity-rated warnings (low/medium/high/critical)
    - Consequences for each warning
    - Mitigation strategies
    - Overall risk score (0-10)
    - Contraindications list
    - Warnings categorized by severity
    
    Args:
        product: Validated ProductModel
        
    Returns:
        Dictionary containing structured safety data with risk assessment
    """
    considerations = product.considerations
    target_users = product.target_users.copy()
    
    try:
        prompt = f"""Analyze safety information for "{product.name}" with detailed risk assessment.

Known considerations: {considerations}
Target users: {', '.join(target_users)}
Product type: {product.product_type}

For each safety item, provide:
1. Type: usage_warning or suitability_flag
2. Severity: low/medium/high/critical
   - Critical: Immediate danger (e.g., "Do not ingest", "Keep away from fire")
   - High: Serious risk (e.g., "May cause allergic reaction", "Not for medical use")
   - Medium: Moderate concern (e.g., "Avoid contact with eyes", "Use in ventilated area")
   - Low: Minor precaution (e.g., "Store in cool place", "Keep out of reach of children")
3. Consequence: What happens if ignored?
4. Mitigation: How to prevent or address the issue?

Also provide:
- Overall Risk Score (0-10): 0=safest, 10=highest risk
- Contraindications: Who should NOT use this product?

Return JSON: {{
  "usage_warnings": [{{
    "warning": "...",
    "severity": "medium",
    "consequence": "...",
    "mitigation": "..."
  }}],
  "suitability_flags": [{{
    "flag": "...",
    "reason": "...",
    "alternative": "..."
  }}],
  "risk_score": 3.5,
  "contraindications": ["condition1", "condition2"],
  "storage": "...",
  "precautions": ["..."]
}}
Output ONLY valid JSON."""

        response = invoke_with_retry(prompt).strip()
        
        response = clean_json_response(response)
        
        expanded = json.loads(response)
        
        # Extract data with defaults
        usage_warnings = expanded.get("usage_warnings", [])
        suitability_flags = expanded.get("suitability_flags", [])
        risk_score = expanded.get("risk_score", 5.0)
        contraindications = expanded.get("contraindications", [])
        
        # Categorize warnings by severity
        warnings_by_severity = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }
        for warning in usage_warnings:
            if isinstance(warning, dict):
                severity = warning.get("severity", "low")
                if severity in warnings_by_severity:
                    warnings_by_severity[severity].append(warning)
                else:
                    warnings_by_severity["low"].append(warning)
            else:
                # Legacy string format
                warnings_by_severity["low"].append({"warning": warning, "severity": "low"})
        
        # Calculate risk level
        risk_level = "low" if risk_score < 3 else "medium" if risk_score < 7 else "high"
        
        # Count warnings by severity
        severity_counts = {k: len(v) for k, v in warnings_by_severity.items()}
        
        return {
            "considerations": considerations,
            "target_users": target_users,
            "suitable_for": target_users,
            "usage_warnings": usage_warnings,
            "suitability_flags": suitability_flags,
            "warnings_by_severity": warnings_by_severity,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "contraindications": contraindications,
            "expanded_safety": expanded,
            "product_name": product.name,
            "metrics": {
                "total_warnings": len(usage_warnings),
                "severity_distribution": severity_counts,
                "has_critical_warnings": severity_counts.get("critical", 0) > 0,
                "has_contraindications": len(contraindications) > 0
            }
        }
    except Exception as e:
        logger.warning(f"Safety block LLM failed: {e}")
        # Fallback with structured warnings
        fallback_warning = {
            "warning": considerations if considerations else "Follow product guidelines",
            "severity": "low",
            "consequence": "May not achieve optimal results",
            "mitigation": "Read all instructions before use"
        }
        return {
            "considerations": considerations,
            "target_users": target_users,
            "suitable_for": target_users,
            "usage_warnings": [fallback_warning] if considerations else [],
            "suitability_flags": [{"flag": f"Designed for: {', '.join(target_users)}", "reason": "Product formulation", "alternative": "Consult specialist"}] if target_users else [],
            "warnings_by_severity": {
                "critical": [],
                "high": [],
                "medium": [],
                "low": [fallback_warning] if considerations else []
            },
            "risk_score": 3.0,
            "risk_level": "low",
            "contraindications": [],
            "expanded_safety": {
                "usage_warnings": [fallback_warning] if considerations else [],
                "suitability_flags": [],
                "storage": "Follow guidelines",
                "precautions": [considerations] if considerations else []
            },
            "product_name": product.name,
            "metrics": {
                "total_warnings": 1 if considerations else 0,
                "severity_distribution": {"critical": 0, "high": 0, "medium": 0, "low": 1 if considerations else 0},
                "has_critical_warnings": False,
                "has_contraindications": False
            }
        }
