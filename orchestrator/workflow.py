"""
LangGraph Workflow for Multi-Agent Content Generation.

Defines the StateGraph that orchestrates all 6 agents:
START -> Parser -> Question Generator -> [FAQ, Product, Comparison] -> Output -> END
"""

import logging
from typing import Dict, Any, Callable, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END


from orchestrator.state import WorkflowState, create_initial_state
from models import ProductModel, QuestionModel
from agents import (
    ParserAgent,
    QuestionGeneratorAgent,
    FAQAgent,
    ProductPageAgent,
    ComparisonAgent,
    OutputAgent
)


logger = logging.getLogger(__name__)


# ===== Node Functions =====

def parse_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Node: Parse and validate product data.
    
    Args:
        state: Current workflow state
        
    Returns:
        State updates dictionary
    """
    logger.info("🔄 Parser Agent: Starting")
    
    agent = ParserAgent()
    product_model, errors = agent.execute(state["product_data"])
    
    updates = {
        "current_step": "parsed",
        "logs": state["logs"] + [f"{datetime.now().isoformat()} - Parser Agent completed"]
    }
    
    if product_model:
        # Convert to dict for state serialization
        updates["product_model"] = product_model.model_dump()
        logger.info("✅ Parser Agent: Success")
    else:
        updates["errors"] = state["errors"] + errors
        logger.error(f"❌ Parser Agent: Failed - {errors}")
    
    return updates


def generate_questions_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Node: Generate categorized questions.
    
    Args:
        state: Current workflow state
        
    Returns:
        State updates dictionary
    """
    logger.info("🔄 Question Generator Agent: Starting")
    
    if not state.get("product_model"):
        return {
            "errors": state["errors"] + ["Cannot generate questions: Product not parsed"],
            "current_step": "questions_failed"
        }
    
    # Reconstruct ProductModel from state
    product = ProductModel(**state["product_model"])
    
    agent = QuestionGeneratorAgent()
    questions, errors = agent.execute(product)
    
    updates = {
        "current_step": "questions_generated",
        "logs": state["logs"] + [
            f"{datetime.now().isoformat()} - Question Generator Agent: Generated {len(questions)} questions"
        ]
    }
    
    if questions:
        # Convert to dicts for serialization
        updates["questions"] = [q.model_dump() for q in questions]
        logger.info(f"✅ Question Generator: Generated {len(questions)} questions")
    
    if errors:
        updates["errors"] = state["errors"] + errors
    
    return updates


def faq_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Node: Create FAQ page content.
    
    Args:
        state: Current workflow state
        
    Returns:
        State updates dictionary
    """
    logger.info("🔄 FAQ Agent: Starting")
    
    if not state.get("product_model"):
        return {
            "errors": state["errors"] + ["Cannot create FAQ: Product not parsed"],
            "current_step": "faq_failed"
        }
    
    product = ProductModel(**state["product_model"])
    questions = [QuestionModel(**q) for q in state.get("questions", [])]
    
    agent = FAQAgent()
    faq_content, errors = agent.execute(product, questions)
    
    updates = {
        "faq_content": faq_content,
        "logs": state["logs"] + [
            f"{datetime.now().isoformat()} - FAQ Agent: Created {len(faq_content.get('questions', []))} FAQs"
        ]
    }
    
    if errors:
        updates["errors"] = state["errors"] + errors
    
    logger.info(f"✅ FAQ Agent: Complete")
    return updates


def product_page_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Node: Create product page content.
    
    Args:
        state: Current workflow state
        
    Returns:
        State updates dictionary
    """
    logger.info("🔄 Product Page Agent: Starting")
    
    if not state.get("product_model"):
        return {
            "errors": state["errors"] + ["Cannot create product page: Product not parsed"],
            "current_step": "product_failed"
        }
    
    product = ProductModel(**state["product_model"])
    
    agent = ProductPageAgent()
    product_content, errors = agent.execute(product)
    
    updates = {
        "product_content": product_content,
        "logs": state["logs"] + [
            f"{datetime.now().isoformat()} - Product Page Agent: Page created"
        ]
    }
    
    if errors:
        updates["errors"] = state["errors"] + errors
    
    logger.info("✅ Product Page Agent: Complete")
    return updates


def comparison_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Node: Create comparison page content.
    
    Args:
        state: Current workflow state
        
    Returns:
        State updates dictionary
    """
    logger.info("🔄 Comparison Agent: Starting")
    
    if not state.get("product_model"):
        return {
            "errors": state["errors"] + ["Cannot create comparison: Product not parsed"],
            "current_step": "comparison_failed"
        }
    
    product = ProductModel(**state["product_model"])
    
    agent = ComparisonAgent()
    comparison_content, errors = agent.execute(product)
    
    updates = {
        "comparison_content": comparison_content,
        "logs": state["logs"] + [
            f"{datetime.now().isoformat()} - Comparison Agent: Comparison created"
        ]
    }
    
    if errors:
        updates["errors"] = state["errors"] + errors
    
    logger.info("✅ Comparison Agent: Complete")
    return updates


def output_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Node: Format and save JSON outputs.
    
    Args:
        state: Current workflow state
        
    Returns:
        State updates dictionary
    """
    logger.info("🔄 Output Agent: Starting")
    
    agent = OutputAgent()
    output_files, errors = agent.execute(
        faq_content=state.get("faq_content", {}),
        product_content=state.get("product_content", {}),
        comparison_content=state.get("comparison_content", {})
    )
    
    updates = {
        "output_files": output_files,
        "current_step": "completed",
        "logs": state["logs"] + [
            f"{datetime.now().isoformat()} - Output Agent: Generated {len(output_files)} files"
        ]
    }
    
    if errors:
        updates["errors"] = state["errors"] + errors
    
    logger.info(f"✅ Output Agent: Generated {len(output_files)} files")
    return updates


# ===== Routing Functions =====

def should_continue(state: WorkflowState) -> str:
    """
    Determine if workflow should continue after question generation.
    
    Returns:
        Next step identifier
    """
    if state.get("errors") and not state.get("questions"):
        return "end"
    return "continue"


# ===== Workflow Builder =====

def create_workflow() -> StateGraph:
    """
    Create the LangGraph StateGraph workflow.
    
    Workflow pattern:
    START -> parse -> generate_questions -> [faq, product, comparison] -> output -> END
    
    The FAQ, Product, and Comparison nodes run after questions are generated,
    then all converge to the Output node.
    
    Returns:
        Compiled StateGraph workflow
    """
    logger.info("Creating LangGraph workflow")
    
    # Create the graph
    workflow = StateGraph(WorkflowState)
    
    # Add nodes
    workflow.add_node("parse", parse_node)
    workflow.add_node("generate_questions", generate_questions_node)
    workflow.add_node("faq", faq_node)
    workflow.add_node("product_page", product_page_node)
    workflow.add_node("comparison", comparison_node)
    workflow.add_node("output", output_node)
    
    # Set entry point
    workflow.set_entry_point("parse")
    
    # Add edges - sequential flow
    # START -> parse -> generate_questions -> faq -> product_page -> comparison -> output -> END
    workflow.add_edge("parse", "generate_questions")
    workflow.add_edge("generate_questions", "faq")
    workflow.add_edge("faq", "product_page")
    workflow.add_edge("product_page", "comparison")
    workflow.add_edge("comparison", "output")
    workflow.add_edge("output", END)
    
    # Compile the graph
    compiled = workflow.compile()
    
    logger.info("Workflow created successfully")
    return compiled


def run_workflow(
    product_data: Dict[str, Any],
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> WorkflowState:
    """
    Run the complete multi-agent workflow using LangGraph.
    
    Executes the compiled StateGraph workflow, properly utilizing LangGraph's
    orchestration capabilities instead of manual node execution.
    
    Args:
        product_data: Raw product data dictionary
        progress_callback: Optional callback for progress updates
                          Signature: callback(step_name: str, progress: float)
        
    Returns:
        Final workflow state with all outputs
        
    Example:
        >>> data = {"name": "GlowBoost...", ...}
        >>> result = run_workflow(data)
        >>> result["output_files"]
        ["output/faq.json", "output/product_page.json", "output/comparison_page.json"]
    """
    logger.info("Starting multi-agent workflow using LangGraph")
    
    try:
        if progress_callback:
            progress_callback("Initializing workflow...", 0.0)
        
        # Create initial state
        state = create_initial_state(product_data)
        
        # Create the compiled LangGraph workflow
        compiled = create_workflow()
        
        if progress_callback:
            progress_callback("Executing LangGraph workflow...", 0.1)
        
        # Execute workflow using LangGraph's compiled.invoke()
        # This is the proper LangGraph execution mechanism
        result = compiled.invoke(state)
        
        if progress_callback:
            progress_callback("Completed", 1.0)
        
        logger.info("Workflow completed successfully via LangGraph")
        return result
        
    except Exception as e:
        logger.error(f"Workflow failed: {str(e)}")
        state = create_initial_state(product_data)
        state["errors"].append(f"Workflow error: {str(e)}")
        state["current_step"] = "failed"
        return state


# Also provide access to the StateGraph for documentation/visualization
def get_workflow_graph() -> StateGraph:
    """
    Get the StateGraph definition for visualization/documentation.
    
    Returns:
        Compiled StateGraph
    """
    return create_workflow()

