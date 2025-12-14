"""
Workflow State Schema for LangGraph.

Defines the typed state that flows through the multi-agent workflow.
"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
import operator


def _merge_dicts(left: Dict, right: Dict) -> Dict:
    """Merge two dicts, combining their keys."""
    result = left.copy()
    result.update(right)
    return result


class WorkflowState(TypedDict):
    """
    State schema for the multi-agent workflow.
    
    This typed dictionary defines all data that flows through the
    LangGraph StateGraph. Each agent reads from and writes to this state.
    
    Note: logs, errors, prompts, and metrics use Annotated with reducers
    to allow concurrent updates from parallel nodes (fan-out/fan-in pattern).
    
    Attributes:
        product_data: Raw input product data (dict)
        product_model: Validated ProductModel (serialized)
        questions: List of generated questions
        faq_content: FAQ page content
        product_content: Product page content
        comparison_content: Comparison page content
        output_files: List of generated file paths
        errors: List of error messages (supports concurrent append)
        logs: List of log messages (supports concurrent append)
        prompts: Dict of prompt_hash -> prompt_text for observability
        metrics: Dict of node_name -> {tokens_in, tokens_out, output_len, elapsed_s}
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
    
    # Metadata - use Annotated for concurrent append in parallel nodes
    errors: Annotated[List[str], operator.add]
    warnings: Annotated[List[str], operator.add]
    logs: Annotated[List[str], operator.add]
    
    # Observability - prompts and metrics for tracking
    prompts: Annotated[Dict[str, str], _merge_dicts]
    metrics: Annotated[Dict[str, Dict[str, Any]], _merge_dicts]
    
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
        warnings=[],
        logs=["Workflow initialized"],
        prompts={},
        metrics={},
        current_step="initialized"
    )
