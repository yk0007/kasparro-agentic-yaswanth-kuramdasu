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
    import time
    start_time = time.time()
    logger.info("🔄 Parser Agent: Starting")
    
    agent = ParserAgent()
    product_model, errors = agent.execute(state["product_data"])
    
    elapsed = time.time() - start_time
    updates = {
        "current_step": "parsed",
        "logs": [f"{datetime.now().isoformat()} - Parser Agent completed ({elapsed:.2f}s)"],
        "metrics": {"parse": {"elapsed_s": round(elapsed, 2), "tokens_in": 0, "tokens_out": 0}}
    }
    
    if product_model:
        # Convert to dict for state serialization
        updates["product_model"] = product_model.model_dump()
        logger.info(f"✅ Parser Agent: Success ({elapsed:.2f}s)")
    else:
        updates["errors"] = errors
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
    import time
    start_time = time.time()
    logger.info("🔄 Question Generator Agent: Starting")
    
    if not state.get("product_model"):
        return {
            "errors": ["Cannot generate questions: Product not parsed"],
            "current_step": "questions_failed"
        }
    
    # Reconstruct ProductModel from state
    product = ProductModel(**state["product_model"])
    
    agent = QuestionGeneratorAgent()
    questions, errors, agent_metrics = agent.execute(product)
    
    elapsed = time.time() - start_time
    
    # Build node metrics with agent token counts
    node_metrics = {
        "elapsed_s": round(elapsed, 2),
        "count": len(questions),
        "tokens_in": agent_metrics.get("tokens_in", 0),
        "tokens_out": agent_metrics.get("tokens_out", 0),
        "output_len": agent_metrics.get("output_len", 0)
    }
    
    updates = {
        "current_step": "questions_generated",
        "logs": [
            f"{datetime.now().isoformat()} - Question Generator Agent: Generated {len(questions)} questions"
        ],
        "metrics": {"questions": node_metrics},
        "prompts": agent_metrics.get("prompts", {})
    }
    
    if questions:
        # Convert to dicts for serialization
        updates["questions"] = [q.model_dump() for q in questions]
        logger.info(f"✅ Question Generator: Generated {len(questions)} questions")
    
    if errors:
        updates["errors"] = errors
    
    return updates


def faq_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Node: Create FAQ page content.
    
    Args:
        state: Current workflow state
        
    Returns:
        State updates dictionary
    """
    import time
    start_time = time.time()
    logger.info("🔄 FAQ Agent: Starting")
    
    if not state.get("product_model"):
        return {
            "errors": ["Cannot create FAQ: Product not parsed"],
            "current_step": "faq_failed"
        }
    
    product = ProductModel(**state["product_model"])
    questions = [QuestionModel(**q) for q in state.get("questions", [])]
    
    agent = FAQAgent()
    faq_content, errors, agent_metrics = agent.execute(product, questions)
    
    elapsed = time.time() - start_time
    faq_count = len(faq_content.get('questions', []))
    
    # Build node metrics with agent token counts
    node_metrics = {
        "elapsed_s": round(elapsed, 2),
        "count": faq_count,
        "tokens_in": agent_metrics.get("tokens_in", 0),
        "tokens_out": agent_metrics.get("tokens_out", 0),
        "output_len": agent_metrics.get("output_len", 0)
    }
    
    updates = {
        "faq_content": faq_content,
        "logs": [
            f"{datetime.now().isoformat()} - FAQ Agent: Created {faq_count} FAQs"
        ],
        "metrics": {"faq": node_metrics},
        "prompts": agent_metrics.get("prompts", {})
    }
    
    if errors:
        updates["errors"] = errors
    
    logger.info(f"✅ FAQ Agent: Complete ({elapsed:.2f}s)")
    return updates


def product_page_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Node: Create product page content.
    
    Args:
        state: Current workflow state
        
    Returns:
        State updates dictionary
    """
    import time
    start_time = time.time()
    logger.info("🔄 Product Page Agent: Starting")
    
    if not state.get("product_model"):
        return {
            "errors": ["Cannot create product page: Product not parsed"],
            "current_step": "product_failed"
        }
    
    product = ProductModel(**state["product_model"])
    
    agent = ProductPageAgent()
    product_content, errors, agent_metrics = agent.execute(product)
    
    elapsed = time.time() - start_time
    
    # Build node metrics with agent token counts
    node_metrics = {
        "elapsed_s": round(elapsed, 2),
        "tokens_in": agent_metrics.get("tokens_in", 0),
        "tokens_out": agent_metrics.get("tokens_out", 0),
        "output_len": agent_metrics.get("output_len", 0)
    }
    
    updates = {
        "product_content": product_content,
        "logs": [
            f"{datetime.now().isoformat()} - Product Page Agent: Page created"
        ],
        "metrics": {"product": node_metrics},
        "prompts": agent_metrics.get("prompts", {})
    }
    
    if errors:
        updates["errors"] = errors
    
    logger.info(f"✅ Product Page Agent: Complete ({elapsed:.2f}s)")
    return updates


def comparison_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Node: Create comparison page content.
    
    Args:
        state: Current workflow state
        
    Returns:
        State updates dictionary
    """
    import time
    start_time = time.time()
    logger.info("🔄 Comparison Agent: Starting")
    
    if not state.get("product_model"):
        return {
            "errors": ["Cannot create comparison: Product not parsed"],
            "current_step": "comparison_failed"
        }
    
    product = ProductModel(**state["product_model"])
    
    agent = ComparisonAgent()
    comparison_content, errors, agent_metrics = agent.execute(product)
    
    elapsed = time.time() - start_time
    
    # Build node metrics with agent token counts
    node_metrics = {
        "elapsed_s": round(elapsed, 2),
        "tokens_in": agent_metrics.get("tokens_in", 0),
        "tokens_out": agent_metrics.get("tokens_out", 0),
        "output_len": agent_metrics.get("output_len", 0)
    }
    
    updates = {
        "comparison_content": comparison_content,
        "logs": [
            f"{datetime.now().isoformat()} - Comparison Agent: Comparison created"
        ],
        "metrics": {"comparison": node_metrics},
        "prompts": agent_metrics.get("prompts", {})
    }
    
    if errors:
        updates["errors"] = errors
    
    logger.info(f"✅ Comparison Agent: Complete ({elapsed:.2f}s)")
    return updates


def validate_content_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Node: Validate that all required content exists before output.
    
    This is an explicit quality gate that ensures all 3 content types
    (FAQ, Product, Comparison) are present and have required structure
    before the output_node writes JSON files.
    
    Returns:
        State updates with validation status in 'content_valid' field
    """
    logger.info("🔄 Content Validation: Starting quality gate check")
    
    errors_found = []
    
    # Check FAQ content
    faq_content = state.get("faq_content", {})
    if not faq_content:
        errors_found.append("FAQ content is missing")
    elif not faq_content.get("questions"):
        errors_found.append("FAQ content has no questions")
    elif len(faq_content.get("questions", [])) < 15:
        actual = len(faq_content.get("questions", []))
        errors_found.append(f"FAQ has only {actual} questions (minimum 15 required)")
    
    # Check Product content
    product_content = state.get("product_content", {})
    if not product_content:
        errors_found.append("Product content is missing")
    elif not product_content.get("product"):
        errors_found.append("Product content has no product data")
    
    # Check Comparison content
    comparison_content = state.get("comparison_content", {})
    if not comparison_content:
        errors_found.append("Comparison content is missing")
    elif not comparison_content.get("products"):
        errors_found.append("Comparison content has no products data")
    
    # Check for existing workflow errors
    existing_errors = state.get("errors", [])
    
    if errors_found or existing_errors:
        all_errors = list(existing_errors) + errors_found
        logger.warning(f"❌ Content Validation Failed: {len(all_errors)} issues found")
        return {
            "current_step": "validation_failed",
            "errors": all_errors,
            "logs": [
                f"{datetime.now().isoformat()} - Content Validation: FAILED - {len(all_errors)} issues"
            ]
        }
    
    logger.info("✅ Content Validation: All content passed quality gates")
    return {
        "current_step": "validated",
        "logs": [
            f"{datetime.now().isoformat()} - Content Validation: PASSED"
        ]
    }


def should_output(state: WorkflowState) -> str:
    """
    Routing function: Determine if output should be generated.
    
    Returns 'output' to proceed with file generation, or 'end' to skip output
    when validation has failed or errors exist.
    
    Args:
        state: Current workflow state
        
    Returns:
        'output' if content is valid, 'end' otherwise
    """
    # Check for explicit validation failure
    if state.get("current_step") == "validation_failed":
        logger.info("Routing: Skipping output due to validation failure")
        return "end"
    
    # Check for any errors in state
    if state.get("errors"):
        logger.info("Routing: Skipping output due to workflow errors")
        return "end"
    
    logger.info("Routing: Proceeding to output")
    return "output"


def output_node(state: WorkflowState) -> Dict[str, Any]:
    """Node: Format and save JSON outputs.

    This node now supports partial outputs:
    - If no content exists at all, it fails fast and writes nothing.
    - If some pages are available (e.g., FAQ and Product succeed but Comparison fails),
      it writes whatever validates successfully and marks the step as completed
      when at least one file is produced.
    
    Also checks for quality issues and logs them explicitly.
    """
    logger.info("🔄 Output Agent: Starting")

    errors = state.get("errors", [])
    faq_content = state.get("faq_content")
    product_content = state.get("product_content")
    comparison_content = state.get("comparison_content")
    
    # Check for quality issues
    quality_issues = []
    
    # Check FAQ quality
    if faq_content:
        faq_count = len(faq_content.get("questions", []))
        if faq_count < 15:
            quality_issues.append(f"FAQ has only {faq_count} items (minimum 15 required)")
        
        # Check for safety warnings
        safety_block = faq_content.get("blocks", {}).get("safety_block", {})
        if not safety_block.get("usage_warnings") and not safety_block.get("suitability_flags"):
            quality_issues.append("FAQ safety block has no warnings or suitability flags")
    
    # Check Product quality
    if product_content:
        if not product_content.get("product"):
            quality_issues.append("Product content missing product data")
    
    # Check Comparison quality
    if comparison_content:
        if not comparison_content.get("products"):
            quality_issues.append("Comparison content missing products data")

    # If we truly have nothing to write, skip entirely.
    if not any([faq_content, product_content, comparison_content]):
        logger.warning("⚠️ Output Agent: No content available to write")
        return {
            "output_files": [],
            "current_step": "failed",
            "logs": [
                f"{datetime.now().isoformat()} - Output Agent: No content available"
            ],
            "errors": errors or ["No content available for output"],
        }

    agent = OutputAgent()
    output_files, output_errors = agent.execute(
        faq_content=faq_content or {},
        product_content=product_content or {},
        comparison_content=comparison_content or {},
    )

    updates: Dict[str, Any] = {
        "output_files": output_files,
        # Mark completed if we produced at least one file, otherwise failed.
        "current_step": "completed" if output_files else "failed",
        "logs": [
            f"{datetime.now().isoformat()} - Output Agent: Generated {len(output_files)} files"
        ],
    }
    
    # Log quality issues if any
    if quality_issues:
        logger.warning(f"⚠️ Output Agent: Quality issues detected: {quality_issues}")
        updates["logs"].append(
            f"{datetime.now().isoformat()} - Output Agent: Quality issues: {'; '.join(quality_issues)}"
        )

    # Merge workflow-level errors with any OutputAgent-specific errors
    merged_errors = []
    if errors:
        merged_errors.extend(errors)
    if output_errors:
        merged_errors.extend(output_errors)
    if merged_errors:
        updates["errors"] = merged_errors

    logger.info(
        "✅ Output Agent: Generated %d files (partial_outputs=%s, quality_issues=%d)",
        len(output_files),
        bool(errors),
        len(quality_issues),
    )
    return updates


# Note: Routing logic is now handled via fan-out/fan-in graph structure
# rather than conditional routing functions.


# ===== Workflow Builder =====

def create_workflow() -> StateGraph:
    """
    Create the LangGraph StateGraph workflow with explicit quality gates.
    
    Workflow pattern:
    START -> parse -> generate_questions -> [faq, product, comparison] -> validate_content -> output/END
    
    The workflow includes:
    1. Sequential: parse -> generate_questions
    2. Fan-out (PARALLEL): generate_questions -> [faq, product_page, comparison]
    3. Fan-in: All 3 converge to validate_content
    4. Conditional routing: validate_content -> output (if valid) OR END (if errors)
    5. Final: output -> END
    
    This design ensures:
    - Parallel execution for content generation agents
    - Explicit quality gate before writing output files
    - No output written if validation fails (fail-fast)
    
    Returns:
        Compiled StateGraph workflow
    """
    logger.info("Creating LangGraph workflow with explicit quality gates")
    
    # Create the graph
    workflow = StateGraph(WorkflowState)
    
    # Add nodes
    workflow.add_node("parse", parse_node)
    workflow.add_node("generate_questions", generate_questions_node)
    workflow.add_node("faq", faq_node)
    workflow.add_node("product_page", product_page_node)
    workflow.add_node("comparison", comparison_node)
    workflow.add_node("validate_content", validate_content_node)  # Quality gate
    workflow.add_node("output", output_node)
    
    # Set entry point
    workflow.set_entry_point("parse")
    
    # Sequential edges: START -> parse -> generate_questions
    workflow.add_edge("parse", "generate_questions")
    
    # Fan-out: generate_questions -> 3 parallel agents
    # These run in PARALLEL after questions are generated
    workflow.add_edge("generate_questions", "faq")
    workflow.add_edge("generate_questions", "product_page")
    workflow.add_edge("generate_questions", "comparison")
    
    # Fan-in: all 3 agents converge to validate_content (quality gate)
    workflow.add_edge("faq", "validate_content")
    workflow.add_edge("product_page", "validate_content")
    workflow.add_edge("comparison", "validate_content")
    
    # Conditional routing: validate_content -> output OR END
    # Uses should_output() routing function to decide
    workflow.add_conditional_edges(
        "validate_content",
        should_output,
        {
            "output": "output",
            "end": END
        }
    )
    
    # Final edge: output -> END
    workflow.add_edge("output", END)
    
    # Compile the graph
    compiled = workflow.compile()
    
    logger.info("Workflow created successfully with parallel execution and quality gates")
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
    
    # Node-to-progress percentage mapping
    NODE_PROGRESS = {
        "parse": ("Parser Agent", 0.15),
        "generate_questions": ("Question Generator", 0.30),
        "faq": ("FAQ Agent", 0.50),
        "product_page": ("Product Page Agent", 0.65),
        "comparison": ("Comparison Agent", 0.80),
        "validate_content": ("Content Validation", 0.90),
        "output": ("Output Agent", 0.98),
    }
    
    try:
        if progress_callback:
            progress_callback("Initializing workflow...", 0.05)
        
        # Create initial state
        state = create_initial_state(product_data)
        
        # Create the compiled LangGraph workflow
        compiled = create_workflow()
        
        if progress_callback:
            progress_callback("Executing LangGraph workflow...", 0.10)
        
        # Use stream() to get per-node updates for progress tracking.
        # LangGraph handles Annotated list merging internally, so we
        # simply keep track of the latest merged state object it yields.
        final_state = None
        for node_output in compiled.stream(state):
            # node_output is a dict with the node name as key
            for node_name, node_result in node_output.items():
                if node_name in NODE_PROGRESS:
                    step_name, pct = NODE_PROGRESS[node_name]
                    # Extract metrics from node result for enriched callback
                    node_metrics = node_result.get("metrics", {}) if isinstance(node_result, dict) else {}
                    if progress_callback:
                        # Pass metrics as optional third argument (backward compatible)
                        try:
                            progress_callback(f"{step_name} complete", pct, node_metrics)
                        except TypeError:
                            # Fallback for callbacks that don't accept metrics
                            progress_callback(f"{step_name} complete", pct)
                    logger.info(f"Progress: {step_name} ({int(pct*100)}%)")
                # node_result is already the merged state produced by LangGraph
                if isinstance(node_result, dict):
                    final_state = node_result
        
        # Defer to the final state produced by LangGraph instead of
        # shallow-updating the initial state.
        if final_state is not None:
            state = final_state
        
        # A1: Mark as failed if any errors occurred during workflow
        if state.get("errors"):
            state["current_step"] = "failed"
            logger.warning(f"Workflow completed with {len(state['errors'])} errors")
        
        if progress_callback:
            progress_callback("Completed", 1.0)
        
        logger.info("Workflow completed successfully via LangGraph")
        return state
        
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

