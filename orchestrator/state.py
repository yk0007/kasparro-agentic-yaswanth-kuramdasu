"""
Workflow State Schema for LangGraph.

Defines the typed state that flows through the multi-agent workflow.
"""

from typing import TypedDict, List, Dict, Any, Optional


class WorkflowState(TypedDict):
    """
    State schema for the multi-agent workflow.
    
    This typed dictionary defines all data that flows through the
    LangGraph StateGraph. Each agent reads from and writes to this state.
    
    Attributes:
        product_data: Raw input product data (dict)
        product_model: Validated ProductModel (serialized)
        questions: List of generated questions
        faq_content: FAQ page content
        product_content: Product page content
        comparison_content: Comparison page content
        output_files: List of generated file paths
        errors: List of error messages
        logs: List of log messages
        current_step: Name of current workflow step
    """
    # Input
    product_data: Dict[str, Any]
    
    # Parsed data (ProductModel as dict for serialization)
    product_model: Optional[Dict[str, Any]]
    
    # Generated questions
    questions: List[Dict[str, Any]]
    
    # Content outputs
    faq_content: Dict[str, Any]
    product_content: Dict[str, Any]
    comparison_content: Dict[str, Any]
    
    # Final outputs
    output_files: List[str]
    
    # Metadata
    errors: List[str]
    logs: List[str]
    current_step: str


def create_initial_state(product_data: Dict[str, Any]) -> WorkflowState:
    """
    Create initial workflow state with product data.
    
    Args:
        product_data: Raw product data dictionary
        
    Returns:
        Initialized WorkflowState
        
    Example:
        >>> data = {"name": "GlowBoost...", ...}
        >>> state = create_initial_state(data)
        >>> state["current_step"]
        "initialized"
    """
    return WorkflowState(
        product_data=product_data,
        product_model=None,
        questions=[],
        faq_content={},
        product_content={},
        comparison_content={},
        output_files=[],
        errors=[],
        logs=["Workflow initialized"],
        current_step="initialized"
    )
