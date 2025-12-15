"""
Benefits Logic Block.

Transforms product benefits into structured content using LLM.
Includes deep evaluation with impact scoring, confidence levels, and user segmentation.
"""

from typing import Dict, List, Any
import json
import logging

from models import ProductModel
from config import invoke_with_retry
from utils import clean_json_response

logger = logging.getLogger(__name__)


def generate_benefits_block(product: ProductModel) -> Dict[str, Any]:
    """
    Transform product benefits into structured content with deep evaluation.
    
    Provides:
    - Impact scoring (0-10 scale)
    - Confidence levels (high/medium/low)
    - User segment targeting
    - Time-to-effect estimates
    - Sustainability assessment
    - Aggregate metrics and rankings
    
    Args:
        product: Validated ProductModel
        
    Returns:
        Dictionary containing structured benefits data with scoring and analysis
    """
    try:
        prompt = f"""Analyze and score each benefit for "{product.name}".

Product: {product.name}
Type: {product.product_type}
Benefits: {', '.join(product.benefits)}
Target Users: {', '.join(product.target_users)}

For each benefit, provide:
1. Category: immediate_result, long_term_care, or quality_of_life
2. Impact Score (0-10): How significant is this benefit?
   - 9-10: Life-changing, addresses critical needs
   - 7-8: Highly valuable, clear improvement
   - 5-6: Moderate value, nice to have
   - 3-4: Minor improvement
   - 1-2: Negligible impact
3. Confidence: high/medium/low (based on how well the benefit is supported by product features)
4. Evidence Strength: strong/moderate/weak (how verifiable is this benefit?)
5. User Segments: Who benefits most? (e.g., "busy professionals", "sensitive skin users")
6. Time to Effect: How long until users see results? (e.g., "immediate", "2-4 weeks")
7. Sustainability: short-term, long-term, or permanent

Return JSON array: [{{
  "benefit": "X",
  "description": "...",
  "category": "immediate_result|long_term_care|quality_of_life",
  "impact_score": 8.5,
  "confidence": "high",
  "evidence_strength": "strong",
  "user_segments": ["segment1", "segment2"],
  "time_to_effect": "2-4 weeks",
  "sustainability": "long-term"
}}]
Output ONLY valid JSON array."""

        response = invoke_with_retry(prompt).strip()
        
        # Clean markdown code blocks using utility function
        response = clean_json_response(response)
        
        detailed = json.loads(response)
        
        # Organize by category for easier template access
        by_category = {
            "immediate_result": [],
            "long_term_care": [],
            "quality_of_life": []
        }
        
        for item in detailed:
            cat = item.get("category", "quality_of_life")
            if cat in by_category:
                by_category[cat].append(item)
            else:
                by_category["quality_of_life"].append(item)
        
        # Calculate aggregate metrics
        impact_scores = [item.get("impact_score", 5.0) for item in detailed]
        avg_impact = sum(impact_scores) / len(impact_scores) if impact_scores else 0
        
        # Rank benefits by impact
        ranked_benefits = sorted(detailed, key=lambda x: x.get("impact_score", 0), reverse=True)
        
        # Count by confidence level
        confidence_counts = {"high": 0, "medium": 0, "low": 0}
        for item in detailed:
            conf = item.get("confidence", "medium")
            if conf in confidence_counts:
                confidence_counts[conf] += 1
        
        return {
            "primary_benefits": product.benefits.copy(),
            "detailed_benefits": detailed,
            "ranked_benefits": ranked_benefits,  # Sorted by impact
            "benefits_by_category": by_category,
            "total_benefits": len(product.benefits),
            "metrics": {  # Aggregate metrics
                "avg_impact_score": round(avg_impact, 2),
                "high_impact_count": len([s for s in impact_scores if s >= 7]),
                "top_benefit": ranked_benefits[0]["benefit"] if ranked_benefits else None,
                "confidence_distribution": confidence_counts
            }
        }
    except Exception as e:
        logger.warning(f"Benefits block LLM failed: {e}")
        # Fallback with basic scoring
        fallback_detailed = [
            {
                "benefit": b, 
                "description": f"{product.name} provides {b}.", 
                "category": "quality_of_life",
                "impact_score": 5.0,
                "confidence": "medium",
                "evidence_strength": "moderate",
                "user_segments": product.target_users,
                "time_to_effect": "varies",
                "sustainability": "long-term"
            } 
            for b in product.benefits
        ]
        return {
            "primary_benefits": product.benefits.copy(),
            "detailed_benefits": fallback_detailed,
            "ranked_benefits": fallback_detailed,
            "benefits_by_category": {
                "immediate_result": [],
                "long_term_care": [],
                "quality_of_life": fallback_detailed
            },
            "total_benefits": len(product.benefits),
            "metrics": {
                "avg_impact_score": 5.0,
                "high_impact_count": 0,
                "top_benefit": product.benefits[0] if product.benefits else None,
                "confidence_distribution": {"high": 0, "medium": len(product.benefits), "low": 0}
            }
        }
