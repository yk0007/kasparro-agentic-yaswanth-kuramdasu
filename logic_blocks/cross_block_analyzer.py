"""
Cross-Block Analyzer.

Analyzes relationships and conflicts between logic blocks.
Provides risk-benefit ratios and ingredient-benefit links.
"""

from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


def analyze_benefit_safety_conflicts(
    benefits_block: Dict[str, Any],
    safety_block: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Identify benefits that may conflict with safety warnings.
    
    Example: "Fast-acting" benefit + "May cause irritation" warning
    = potential trade-off users should know about.
    
    Args:
        benefits_block: Output from generate_benefits_block()
        safety_block: Output from generate_safety_block()
        
    Returns:
        Dictionary with conflict analysis and risk-benefit ratio
    """
    conflicts = []
    trade_offs = []
    
    # Get high-impact benefits
    high_impact_benefits = [
        b for b in benefits_block.get("detailed_benefits", [])
        if isinstance(b, dict) and b.get("impact_score", 0) >= 7
    ]
    
    # Get high-severity warnings
    high_severity_warnings = []
    for severity in ["high", "critical"]:
        warnings = safety_block.get("warnings_by_severity", {}).get(severity, [])
        high_severity_warnings.extend(warnings)
    
    # Also check usage_warnings directly if structured
    for warning in safety_block.get("usage_warnings", []):
        if isinstance(warning, dict) and warning.get("severity") in ["high", "critical"]:
            if warning not in high_severity_warnings:
                high_severity_warnings.append(warning)
    
    # Analyze potential conflicts
    for benefit in high_impact_benefits:
        for warning in high_severity_warnings:
            warning_text = warning.get("warning") if isinstance(warning, dict) else str(warning)
            
            # Check for speed vs safety conflicts
            if benefit.get("category") == "immediate_result":
                conflict_type = "speed_vs_safety"
                recommendation = "Users seeking fast results should carefully review safety precautions"
            elif benefit.get("sustainability") == "short-term":
                conflict_type = "temporary_benefit_with_risk"
                recommendation = "Consider whether short-term benefit justifies the associated precautions"
            else:
                conflict_type = "general_trade_off"
                recommendation = "Weigh the benefit against the safety consideration"
            
            conflicts.append({
                "benefit": benefit.get("benefit"),
                "benefit_impact": benefit.get("impact_score", 0),
                "warning": warning_text,
                "warning_severity": warning.get("severity") if isinstance(warning, dict) else "unknown",
                "conflict_type": conflict_type,
                "recommendation": recommendation
            })
    
    # Calculate risk-benefit ratio
    risk_benefit_ratio = _calculate_risk_benefit_ratio(benefits_block, safety_block)
    
    # Generate summary
    risk_level = safety_block.get("risk_level", "medium")
    avg_benefit = benefits_block.get("metrics", {}).get("avg_impact_score", 5.0)
    
    if risk_benefit_ratio >= 7:
        overall_assessment = "Highly favorable - benefits significantly outweigh risks"
    elif risk_benefit_ratio >= 5:
        overall_assessment = "Favorable - benefits outweigh risks with reasonable precautions"
    elif risk_benefit_ratio >= 3:
        overall_assessment = "Balanced - benefits and risks are comparable, careful use advised"
    else:
        overall_assessment = "Caution advised - risks may outweigh benefits for some users"
    
    return {
        "conflicts_found": len(conflicts),
        "conflicts": conflicts,
        "risk_benefit_ratio": risk_benefit_ratio,
        "overall_assessment": overall_assessment,
        "high_impact_benefits_count": len(high_impact_benefits),
        "high_severity_warnings_count": len(high_severity_warnings),
        "metrics": {
            "avg_benefit_score": avg_benefit,
            "risk_score": safety_block.get("risk_score", 5.0),
            "risk_level": risk_level
        }
    }


def _calculate_risk_benefit_ratio(
    benefits_block: Dict[str, Any],
    safety_block: Dict[str, Any]
) -> float:
    """
    Calculate risk-benefit ratio (higher = more benefits relative to risks).
    
    Formula: (benefit_score / 10) * (1 - risk_score / 10) * 10
    
    Returns:
        Float from 0-10 (10 = high benefit, low risk)
    """
    avg_benefit_score = benefits_block.get("metrics", {}).get("avg_impact_score", 5.0)
    risk_score = safety_block.get("risk_score", 5.0)
    
    # Normalize: high benefit + low risk = high ratio
    # If benefit = 10 and risk = 0, ratio = 10
    # If benefit = 5 and risk = 5, ratio = 2.5
    # If benefit = 0 and risk = 10, ratio = 0
    ratio = (avg_benefit_score / 10) * (1 - risk_score / 10) * 10
    return round(max(0, min(10, ratio)), 2)


def analyze_ingredient_benefit_links(
    ingredients_block: Dict[str, Any],
    benefits_block: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Link ingredients/features to specific benefits they provide.
    
    Args:
        ingredients_block: Output from generate_ingredients_block()
        benefits_block: Output from generate_benefits_block()
        
    Returns:
        Dictionary mapping ingredients to benefits
    """
    ingredient_benefit_map = {}
    key_contributors = []
    synergies = []
    
    # Get active ingredients/features
    active_ingredients = ingredients_block.get("active_ingredients", [])
    if not active_ingredients:
        active_ingredients = ingredients_block.get("key_features", [])
    
    # Get detailed benefits
    detailed_benefits = benefits_block.get("detailed_benefits", [])
    
    # Simple keyword matching for ingredient-benefit links
    for ingredient in active_ingredients:
        ingredient_name = ingredient.get("name", str(ingredient)) if isinstance(ingredient, dict) else str(ingredient)
        linked_benefits = []
        
        for benefit in detailed_benefits:
            benefit_text = benefit.get("benefit", "") + " " + benefit.get("description", "")
            # Simple overlap check
            if ingredient_name.lower() in benefit_text.lower():
                linked_benefits.append(benefit.get("benefit", ""))
        
        if linked_benefits:
            ingredient_benefit_map[ingredient_name] = linked_benefits
            key_contributors.append({
                "ingredient": ingredient_name,
                "benefits_count": len(linked_benefits),
                "benefits": linked_benefits
            })
    
    # Sort by contribution
    key_contributors.sort(key=lambda x: x["benefits_count"], reverse=True)
    
    return {
        "ingredient_benefit_map": ingredient_benefit_map,
        "key_contributors": key_contributors[:5],  # Top 5 contributors
        "synergies": synergies,
        "total_links_found": sum(len(v) for v in ingredient_benefit_map.values())
    }


def generate_cross_block_summary(
    benefits_block: Dict[str, Any],
    safety_block: Dict[str, Any],
    usage_block: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Generate comprehensive cross-block analysis summary.
    
    Args:
        benefits_block: Benefits analysis
        safety_block: Safety analysis
        usage_block: Optional usage analysis
        
    Returns:
        Complete cross-block intelligence report
    """
    # Get conflict analysis
    conflicts = analyze_benefit_safety_conflicts(benefits_block, safety_block)
    
    # Build summary
    summary = {
        "cross_block_analysis": conflicts,
        "key_insights": [],
        "recommendations": []
    }
    
    # Generate insights
    if conflicts["risk_benefit_ratio"] >= 7:
        summary["key_insights"].append("Product has excellent risk-benefit profile")
    
    if conflicts["conflicts_found"] > 0:
        summary["key_insights"].append(f"Found {conflicts['conflicts_found']} potential trade-offs to communicate to users")
        summary["recommendations"].append("Consider adding trade-off information to product page")
    
    if safety_block.get("metrics", {}).get("has_critical_warnings"):
        summary["key_insights"].append("Product has critical safety warnings requiring prominent display")
        summary["recommendations"].append("Ensure critical warnings are visible before purchase")
    
    high_impact = benefits_block.get("metrics", {}).get("high_impact_count", 0)
    if high_impact >= 3:
        summary["key_insights"].append(f"Product has {high_impact} high-impact benefits - strong value proposition")
        summary["recommendations"].append("Highlight top benefits in marketing materials")
    
    return summary
