"""
Streamlit Demo Application for Multi-Agent Content Generation System.

Provides a user interface to:
- Input product data (JSON or text format)
- Run the multi-agent workflow
- View and download generated content
- Preview as a modern ecommerce webpage
"""

import streamlit as st
import json
import time
from datetime import datetime
import os
import sys
from typing import Tuple, Optional, Dict, Any
import asyncio
import nest_asyncio

# Apply nest_asyncio to allow nested event loops in Streamlit
nest_asyncio.apply()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import EXAMPLE_PRODUCT_DATA
from orchestrator import run_workflow


# Page configuration
st.set_page_config(
    page_title="Multi-Agent Content Generator",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-top: 0;
    }
    .success-box {
        background-color: #E8F5E9;
        border-left: 4px solid #4CAF50;
        padding: 1rem;
        border-radius: 4px;
    }
    .error-box {
        background-color: #FFEBEE;
        border-left: 4px solid #F44336;
        padding: 1rem;
        border-radius: 4px;
    }
    .agent-step {
        padding: 0.5rem 1rem;
        margin: 0.25rem 0;
        border-radius: 4px;
        background-color: #F5F5F5;
    }
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #6b7280 0%, #4b5563 100%);
    }
    .metric-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if "workflow_running" not in st.session_state:
        st.session_state.workflow_running = False
    if "results" not in st.session_state:
        st.session_state.results = None
    if "logs" not in st.session_state:
        st.session_state.logs = []
    if "current_step" not in st.session_state:
        st.session_state.current_step = ""
    if "show_preview" not in st.session_state:
        st.session_state.show_preview = False


def validate_json(json_str: str) -> Tuple[Optional[Dict], Optional[str]]:
    """Validate JSON input structure only (not field names)."""
    try:
        data = json.loads(json_str)
        if not isinstance(data, dict):
            return None, "Input must be a JSON object"
        
        if len(data) == 0:
            return None, "JSON object cannot be empty"
        
        return data, None
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON syntax: {str(e)}"


def run_generation(product_data: Dict[str, Any]):
    """Run the multi-agent workflow."""
    st.session_state.workflow_running = True
    st.session_state.logs = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    steps = [
        ("🔄 Parser Agent", "Validating product data..."),
        ("🔄 Parser Agent", "Parsing product data...", 20),
        ("🔄 Question Generator", "Generating user questions...", 40),
        ("🔄 FAQ Agent", "Creating FAQ content...", 60),
        ("🔄 Product Page Agent", "Building product page...", 80),
        ("🔄 Comparison Agent", "Generating comparison...", 95),
        ("✅ Complete", "Saving JSON files...", 100)
    ]
    
    # Create a placeholder for real-time log updates in sidebar
    log_placeholder = st.sidebar.empty()
    
    def progress_callback(step: str, progress: float, metrics: Dict[str, Any] = None):
        """Callback for workflow progress updates.

        Uses the numeric progress reported by the workflow and ensures the
        Streamlit progress bar is **monotonic** (never moves backwards).
        """
        log_entry = f"{step}"
        st.session_state.logs.append(log_entry)
        st.session_state.current_step = step

        # Aggregate per-node metrics into session state
        if metrics:
            if "workflow_metrics" not in st.session_state:
                st.session_state.workflow_metrics = {}
            st.session_state.workflow_metrics.update(metrics)

        # Initialize last_progress in session state
        if "last_progress" not in st.session_state:
            st.session_state.last_progress = 0.0

        # Clamp progress between 0 and 1 and enforce monotonicity
        pct = max(0.0, min(1.0, float(progress)))
        if pct < st.session_state.last_progress:
            pct = st.session_state.last_progress
        st.session_state.last_progress = pct

        # Update progress bar and status
        progress_bar.progress(pct)
        status_text.markdown(f"**{step}** ({int(pct * 100)}%)")

        # Update logs display in sidebar (WITHOUT adding another header)
        recent_logs = st.session_state.logs[-6:]
        log_display = ""
        for log in recent_logs:
            display_log = log[:55] + "..." if len(log) > 55 else log
            log_display += f"• {display_log}\n\n"
        log_placeholder.markdown(log_display)
    
    # Run actual workflow with real progress
    status_text.markdown("**Starting workflow...**")
    progress_bar.progress(0.05)
    
    try:
        result = run_workflow(product_data, progress_callback)
        st.session_state.results = result
        
        if result.get("errors"):
            st.session_state.logs.extend(result["errors"])
        
        st.session_state.logs.extend(result.get("logs", []))
        progress_bar.progress(1.0)
        status_text.markdown("**✅ Generation complete! (100%)**")
        
    except Exception as e:
        st.error(f"Workflow failed: {str(e)}")
        st.session_state.logs.append(f"ERROR: {str(e)}")
    
    st.session_state.workflow_running = False


# HTML Generation - extracted to services/html_generator.py
from services import HtmlGenerator

def generate_ecommerce_html(
    product_data: Dict[str, Any],
    faq_data: Dict[str, Any],
    comparison_data: Dict[str, Any]
) -> str:
    """Generate minimal modern ecommerce preview HTML with fully dynamic content.
    
    .. deprecated::
        This function is deprecated and maintained only for backward compatibility.
        Use HtmlGenerator.generate() directly instead:
        
            from services import HtmlGenerator
            generator = HtmlGenerator()
            html = generator.generate(product_data, faq_data, comparison_data)
    
    Args:
        product_data: Product page JSON data
        faq_data: FAQ page JSON data  
        comparison_data: Comparison page JSON data
        
    Returns:
        Complete HTML document as string
    """
    generator = HtmlGenerator()
    return generator.generate(product_data, faq_data, comparison_data)


def display_results():
    """Display generated content in tabs."""
    if not st.session_state.results:
        return
    
    results = st.session_state.results
    output_files = results.get("output_files", [])
    
    if not output_files:
        st.warning("No output files generated. Check errors below.")
        return
    
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    
    # Load all data
    faq_data = {}
    product_data = {}
    comparison_data = {}
    
    faq_path = os.path.join(output_dir, "faq.json")
    if os.path.exists(faq_path):
        with open(faq_path, 'r') as f:
            faq_data = json.load(f)
    
    product_path = os.path.join(output_dir, "product_page.json")
    if os.path.exists(product_path):
        with open(product_path, 'r') as f:
            product_data = json.load(f)
    
    comparison_path = os.path.join(output_dir, "comparison_page.json")
    if os.path.exists(comparison_path):
        with open(comparison_path, 'r') as f:
            comparison_data = json.load(f)
    
    # Basic Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Questions", len(results.get("questions", [])))
    with col2:
        st.metric("FAQ Items", len(faq_data.get("questions", [])))
    with col3:
        st.metric("Output Files", len(output_files))
    with col4:
        st.metric("Errors", len(results.get("errors", [])))
    
    # Observability Metrics (if available)
    workflow_metrics = results.get("metrics", {})
    if workflow_metrics:
        st.markdown("#### 📊 Workflow Metrics")
        metrics_cols = st.columns(len(workflow_metrics) if len(workflow_metrics) <= 4 else 4)
        for idx, (node_name, node_metrics) in enumerate(workflow_metrics.items()):
            col = metrics_cols[idx % len(metrics_cols)]
            with col:
                tokens_in = node_metrics.get("tokens_in", 0)
                tokens_out = node_metrics.get("tokens_out", 0)
                elapsed = node_metrics.get("elapsed_s", 0)
                st.markdown(f"**{node_name}**")
                st.caption(f"~{tokens_in} in / ~{tokens_out} out | {elapsed:.1f}s")
    
    st.markdown("---")
    
    # Preview Button
    st.markdown("### 🌐 Ecommerce Preview")
    
    # Generate and save HTML preview using HtmlGenerator directly
    generator = HtmlGenerator()
    html_content = generator.generate(product_data, faq_data, comparison_data)
    preview_path = os.path.join(output_dir, "preview.html")
    with open(preview_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📥 Download Preview HTML",
            html_content,
            "ecommerce_preview.html",
            "text/html",
            use_container_width=True
        )
    with col2:
        st.info(f"Preview saved to: `output/preview.html`\n\nOpen in browser to view.")
    
    # Show preview in iframe
    with st.expander("🖥️ Preview Ecommerce Page", expanded=True):
        st.components.v1.html(html_content, height=800, scrolling=True)
    
    st.markdown("---")
    
    # Create tabs for each output
    tab1, tab2, tab3 = st.tabs(["📋 FAQ JSON", "📦 Product JSON", "⚖️ Comparison JSON"])
    
    with tab1:
        if faq_data:
            st.subheader("FAQ Data")
            st.json(faq_data)
            st.download_button(
                "📥 Download FAQ JSON",
                json.dumps(faq_data, indent=2),
                "faq.json",
                "application/json"
            )
    
    with tab2:
        if product_data:
            st.subheader("Product Page Data")
            st.json(product_data)
            st.download_button(
                "📥 Download Product JSON",
                json.dumps(product_data, indent=2),
                "product_page.json",
                "application/json"
            )
    
    with tab3:
        if comparison_data:
            st.subheader("Comparison Data")
            st.json(comparison_data)
            st.download_button(
                "📥 Download Comparison JSON",
                json.dumps(comparison_data, indent=2),
                "comparison_page.json",
                "application/json"
            )


def main():
    """Main application entry point."""
    init_session_state()
    
    # Header
    st.markdown('<p class="main-header">🚀 Multi-Agent Content Generator</p>', 
                unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Multi-Agent AI-Powered Content Generation</p>', 
                unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ System Info")
        st.markdown("**6 Agents** • **5+ Logic Blocks** • **3 Outputs**")
        
        st.markdown("---")
        
        # LLM Provider Display (Groq-only)
        st.markdown("### 🤖 LLM Provider")
        from config import get_available_providers, get_current_provider, get_current_model
        
        available = get_available_providers()
        if not available:
            st.error("GROQ_API_KEY not configured. Add to .env")
        else:
            st.success("🟢 Groq (Fictional Competitor)")
            st.caption(f"Model: `{get_current_model()}`")
            st.caption("Generates fictional but realistic competitor")
        
        st.markdown("---")
        st.markdown("### 📊 Status")
        if st.session_state.workflow_running:
            st.warning("🔄 Workflow running...")
        elif st.session_state.results:
            st.success("✅ Results ready")
        else:
            st.info("Ready to generate")
        
        st.markdown("---")
        # Logs section is handled dynamically via log_placeholder during workflow
        st.markdown("### 📝 Logs")
        if not st.session_state.workflow_running and st.session_state.logs:
            for log in st.session_state.logs[-6:]:
                st.caption(log[:55] + "..." if len(log) > 55 else log)
        elif not st.session_state.logs:
            st.caption("No logs yet. Generate content to see logs.")
    
    # Main content
    st.markdown("### 📝 Product Input")
    
    # Input method selection
    input_method = st.radio(
        "Input Format:",
        ["JSON Editor", "Text Fields"],
        horizontal=True
    )
    
    if input_method == "JSON Editor":
        default_json = json.dumps(EXAMPLE_PRODUCT_DATA, indent=2)
        product_json = st.text_area(
            "Product JSON",
            value=default_json,
            height=300,
            help="Enter product data in JSON format"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✔️ Validate JSON", use_container_width=True):
                data, error = validate_json(product_json)
                if error:
                    st.error(f"❌ {error}")
                else:
                    st.success(f"✅ Valid - {data.get('name', 'Product')}")
        
        with col2:
            if st.button("🚀 Generate Content", type="primary", 
                        disabled=st.session_state.workflow_running,
                        use_container_width=True):
                data, error = validate_json(product_json)
                if error:
                    st.error(f"❌ {error}")
                else:
                    run_generation(data)
    
    else:  # Text Fields - Dynamic Key-Value Pairs
        st.markdown("#### Enter Product Details")
        st.caption("Edit keys and values below. Add more fields if needed (minimum 6 required).")
        
        # Initialize session state for key-value pairs if not exists
        if "kv_pairs" not in st.session_state:
            st.session_state.kv_pairs = [
                ("name", "GlowBoost Vitamin C Serum"),
                ("product_type", "10% Vitamin C"),
                ("target_users", "Oily, Combination"),
                ("key_features", "Vitamin C, Hyaluronic Acid"),
                ("benefits", "Brightening, Fades dark spots"),
                ("how_to_use", "Apply 2–3 drops in the morning before sunscreen"),
                ("considerations", "Mild tingling for sensitive skin"),
                ("price", "₹699"),
            ]
        
        # Display current key-value pairs
        st.markdown("##### Product Fields")
        
        pairs_to_remove = []
        updated_pairs = []
        
        for i, (key, value) in enumerate(st.session_state.kv_pairs):
            col1, col2, col3 = st.columns([2, 4, 1])
            with col1:
                new_key = st.text_input(
                    f"Key {i+1}",
                    value=key,
                    placeholder="e.g., name, price, benefits",
                    label_visibility="collapsed",
                    key=f"key_{i}"
                )
            with col2:
                new_value = st.text_input(
                    f"Value {i+1}",
                    value=value,
                    placeholder="Enter value...",
                    label_visibility="collapsed",
                    key=f"value_{i}"
                )
            with col3:
                if len(st.session_state.kv_pairs) > 6:  # Allow removal only if more than 6
                    if st.button("🗑️", key=f"remove_{i}", help="Remove this field"):
                        pairs_to_remove.append(i)
                else:
                    st.write("")  # Empty space
            
            updated_pairs.append((new_key, new_value))
        
        # Update session state with edited pairs
        st.session_state.kv_pairs = [p for i, p in enumerate(updated_pairs) if i not in pairs_to_remove]
        
        # Add new field button
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("➕ Add Field", use_container_width=True):
                st.session_state.kv_pairs.append(("new_field", ""))
                st.rerun()
        with col2:
            st.caption(f"Current: {len(st.session_state.kv_pairs)} fields (minimum 6)")
        
        st.markdown("---")
        
        # Generate button
        if st.button("🚀 Generate Content", type="primary", 
                    disabled=st.session_state.workflow_running,
                    use_container_width=True):
            # Build product data from key-value pairs
            product_data = {}
            list_fields = ["target_users", "key_features", "benefits"]
            
            for key, value in st.session_state.kv_pairs:
                if key.strip():
                    if key in list_fields:
                        product_data[key] = [v.strip() for v in value.split(",")]
                    else:
                        product_data[key] = value
            
            # Check minimum required fields
            required = ["name", "product_type", "target_users", "key_features", 
                       "benefits", "how_to_use", "considerations", "price"]
            missing = [f for f in required if f not in product_data]
            
            if missing:
                st.error(f"❌ Missing required fields: {', '.join(missing)}")
            else:
                run_generation(product_data)
    
    st.markdown("---")
    
    # Results section
    if st.session_state.results:
        st.markdown("### 📄 Generated Content")
        display_results()
        
        # Errors section
        errors = st.session_state.results.get("errors", [])
        if errors:
            st.markdown("### ⚠️ Warnings/Errors")
            for error in errors:
                st.warning(error)
        
        # Clear button
        if st.button("🗑️ Clear Results", use_container_width=True):
            st.session_state.results = None
            st.session_state.logs = []


if __name__ == "__main__":
    main()
