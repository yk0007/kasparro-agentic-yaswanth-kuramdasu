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
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
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
        ("🔄 Question Generator", "Generating user questions..."),
        ("🔄 FAQ Agent", "Creating FAQ content..."),
        ("🔄 Product Page Agent", "Building product page..."),
        ("🔄 Comparison Agent", "Generating comparison..."),
        ("🔄 Output Agent", "Saving JSON files...")
    ]
    
    def progress_callback(step: str, progress: float):
        st.session_state.current_step = step
        st.session_state.logs.append(f"{datetime.now().strftime('%H:%M:%S')} - {step}")
    
    # Show step-by-step progress
    for i, (agent, description) in enumerate(steps):
        status_text.markdown(f"**{agent}**: {description}")
        progress_bar.progress((i + 1) / len(steps))
        time.sleep(0.2)
    
    # Run actual workflow
    status_text.markdown("**Running workflow...**")
    
    try:
        result = run_workflow(product_data, progress_callback)
        st.session_state.results = result
        
        if result.get("errors"):
            st.session_state.logs.extend(result["errors"])
        
        st.session_state.logs.extend(result.get("logs", []))
        progress_bar.progress(1.0)
        status_text.markdown("**✅ Generation complete!**")
        
    except Exception as e:
        st.error(f"Workflow failed: {str(e)}")
        st.session_state.logs.append(f"ERROR: {str(e)}")
    
    st.session_state.workflow_running = False


def generate_ecommerce_html(
    product_data: Dict[str, Any],
    faq_data: Dict[str, Any],
    comparison_data: Dict[str, Any]
) -> str:
    """Generate minimal modern ecommerce preview HTML with fully dynamic content."""
    product = product_data.get("product", {})
    product_a = comparison_data.get("products", {}).get("product_a", {})
    product_b = comparison_data.get("products", {}).get("product_b", {})
    questions = faq_data.get("questions", [])
    
    # Get product name and basic info
    name = product.get('name') or product_a.get('name') or 'Product'
    product_type = product.get('product_type') or product_a.get('product_type') or ''
    price = product.get('price', {}).get('amount') if isinstance(product.get('price'), dict) else product_a.get('price', '')
    target = product.get('suitable_for', []) or product_a.get('target_users', [])
    
    # Get product description (short version)
    description = product.get('headline') or product.get('tagline') or ''
    if not description:
        benefits_list = product.get('benefits', {})
        if isinstance(benefits_list, dict):
            primary = benefits_list.get('primary_benefits', [])
            if primary:
                description = ' • '.join(primary[:2])
        elif isinstance(benefits_list, list) and benefits_list:
            description = ' • '.join(benefits_list[:2])
    
    # Get LLM-enriched benefits data
    benefits_data = product.get('benefits', {})
    if isinstance(benefits_data, dict):
        detailed_benefits = benefits_data.get('detailed_benefits', [])
        benefits_html = ''
        for item in detailed_benefits:
            benefit = item.get('benefit', '')
            desc = item.get('description', '')
            benefits_html += f'<li><strong>{benefit}</strong> — {desc}</li>'
        if not benefits_html:
            primary = benefits_data.get('primary_benefits', [])
            benefits_html = ''.join([f'<li>{b}</li>' for b in primary])
    else:
        benefits_html = ''.join([f'<li>{b}</li>' for b in benefits_data]) if benefits_data else '<li>Quality product</li>'
    
    # Get LLM-enriched features/ingredients data
    ingredients_data = product.get('ingredients', {})
    if isinstance(ingredients_data, dict):
        feature_details = ingredients_data.get('feature_details', [])
        features_html = ''
        for item in feature_details:
            features_html += f'<span class="tag">{item.get("name", "")}</span>'
        if not features_html:
            features = ingredients_data.get('key_features', [])
            features_html = ''.join([f'<span class="tag">{f}</span>' for f in features])
    else:
        features_html = ''
    
    # Get LLM-enriched usage data
    usage_data = product.get('how_to_use', {})
    if isinstance(usage_data, dict):
        expanded = usage_data.get('expanded_instructions', {})
        steps = expanded.get('steps', [])
        tips = expanded.get('tips', [])
        if steps:
            usage_html = '<ol style="text-align:left;max-width:600px;margin:0 auto;">'
            for step in steps:
                usage_html += f'<li style="margin:8px 0;">{step}</li>'
            usage_html += '</ol>'
            if tips:
                usage_html += '<p style="margin-top:16px;font-size:0.9rem;color:#888;"><strong>Pro Tips:</strong></p><ul style="text-align:left;max-width:600px;margin:0 auto;color:#888;">'
                for tip in tips:
                    usage_html += f'<li style="margin:4px 0;">{tip}</li>'
                usage_html += '</ul>'
        else:
            usage_html = f'<p>{usage_data.get("summary", "")}</p>'
    else:
        usage_html = f'<p>{usage_data}</p>'
    
    # Build target HTML
    target_html = ', '.join(target) if target else 'Everyone'
    
    # Build FAQ HTML with collapsible items
    faq_html = ''
    for q in questions[:5]:
        faq_html += f'''
        <details class="faq-item">
            <summary class="faq-q">{q.get('question', '')}</summary>
            <div class="faq-a">{q.get('answer', '')}</div>
        </details>'''
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', sans-serif; background: #fff; color: #111; line-height: 1.7; }}
        
        /* Hero */
        .hero {{ padding: 80px 20px; text-align: center; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); }}
        .hero h1 {{ font-size: 2.8rem; font-weight: 800; margin-bottom: 12px; letter-spacing: -0.5px; }}
        .hero .tagline {{ color: #10b981; font-size: 1rem; font-weight: 600; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; }}
        .hero .desc {{ color: #555; font-size: 1.1rem; max-width: 550px; margin: 0 auto 20px; }}
        .hero .price {{ font-size: 1.8rem; font-weight: 700; color: #111; }}
        
        /* Container */
        .container {{ max-width: 800px; margin: 0 auto; padding: 60px 20px; }}
        .section-title {{ font-size: 1.4rem; font-weight: 700; margin-bottom: 28px; text-align: center; letter-spacing: -0.3px; }}
        
        /* Tags */
        .tags {{ display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin: 20px 0; }}
        .tag {{ background: #fff; border: 1px solid #ddd; padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 500; }}
        
        /* Benefits */
        .benefits ul {{ list-style: none; max-width: 650px; margin: 0 auto; }}
        .benefits li {{ padding: 14px 0; border-bottom: 1px solid #eee; font-size: 0.95rem; }}
        .benefits li strong {{ color: #10b981; font-weight: 600; }}
        
        /* Usage */
        .usage {{ background: #f8f9fa; padding: 50px 20px; text-align: center; }}
        .usage p {{ color: #555; max-width: 600px; margin: 0 auto; font-size: 0.95rem; }}
        
        /* Comparison */
        .comparison {{ background: #111; color: #fff; padding: 60px 20px; }}
        .comparison .section-title {{ color: #fff; }}
        .comp-table {{ max-width: 850px; margin: 0 auto; }}
        .comp-row {{ display: grid; grid-template-columns: 140px 1fr 1fr; padding: 14px 8px; border-bottom: 1px solid #333; font-size: 0.9rem; }}
        .comp-row:first-child {{ font-weight: 600; color: #888; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.5px; }}
        .comp-row span {{ color: #10b981; font-size: 0.7rem; }}
        .comp-row div:first-child {{ color: #aaa; font-weight: 500; }}
        
        /* FAQ - Collapsible */
        .faq {{ padding: 60px 20px; background: #fafafa; }}
        .faq-item {{ max-width: 700px; margin: 0 auto 12px; background: #fff; border-radius: 10px; border: 1px solid #eee; overflow: hidden; }}
        .faq-item summary {{ padding: 18px 20px; font-weight: 600; font-size: 0.95rem; cursor: pointer; list-style: none; display: flex; justify-content: space-between; align-items: center; }}
        .faq-item summary::-webkit-details-marker {{ display: none; }}
        .faq-item summary::after {{ content: "+"; font-size: 1.2rem; color: #888; }}
        .faq-item[open] summary::after {{ content: "−"; }}
        .faq-item[open] summary {{ border-bottom: 1px solid #eee; }}
        .faq-a {{ padding: 16px 20px; color: #555; font-size: 0.9rem; line-height: 1.6; }}
        
        /* Footer */
        footer {{ text-align: center; padding: 30px; color: #888; font-size: 0.8rem; }}
    </style>
</head>
<body>
    <section class="hero">
        <p class="tagline">{product_type}</p>
        <h1>{name}</h1>
        <p class="desc">{description}</p>
        <div class="tags">{features_html}</div>
        <div class="price">{price}</div>
    </section>
    
    <div class="container benefits">
        <h2 class="section-title">Benefits</h2>
        <ul>{benefits_html}</ul>
    </div>
    
    <section class="usage">
        <h2 class="section-title">How to Use</h2>
        {usage_html}
        <p style="margin-top: 14px; font-size: 0.85rem;"><strong>Best for:</strong> {target_html}</p>
    </section>
    
    <section class="comparison">
        <h2 class="section-title">Compare Options</h2>
        <div class="comp-table">
            <div class="comp-row">
                <div>Feature</div>
                <div>{product_a.get('name', 'Our Product')}<br><span>Main</span></div>
                <div>{product_b.get('name', 'Alternative')}<br><span>Alternative</span></div>
            </div>
            <div class="comp-row">
                <div>Type</div>
                <div>{product_a.get('product_type', '-')}</div>
                <div>{product_b.get('product_type', '-')}</div>
            </div>
            <div class="comp-row">
                <div>Price</div>
                <div>{product_a.get('price', '-')}</div>
                <div>{product_b.get('price', '-')}</div>
            </div>
            <div class="comp-row">
                <div>Best for</div>
                <div>{', '.join(product_a.get('target_users', []))}</div>
                <div>{', '.join(product_b.get('target_users', []))}</div>
            </div>
            <div class="comp-row">
                <div>Key Features</div>
                <div>{', '.join(product_a.get('key_features', []))}</div>
                <div>{', '.join(product_b.get('key_features', []))}</div>
            </div>
            <div class="comp-row">
                <div>Benefits</div>
                <div>{', '.join(product_a.get('benefits', []))}</div>
                <div>{', '.join(product_b.get('benefits', []))}</div>
            </div>
            <div class="comp-row">
                <div>Considerations</div>
                <div>{product_a.get('considerations', '-')}</div>
                <div>{product_b.get('considerations', '-')}</div>
            </div>
        </div>
    </section>
    
    <section class="faq">
        <h2 class="section-title">FAQ</h2>
        {faq_html if faq_html else '<p style="text-align:center;color:#888;">No FAQs generated</p>'}
    </section>
    
    <footer>
        Generated by Multi-Agent Content System • Powered by LangGraph + Gemini
    </footer>
</body>
</html>'''
    return html


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
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Questions", len(results.get("questions", [])))
    with col2:
        st.metric("FAQ Items", len(faq_data.get("questions", [])))
    with col3:
        st.metric("Output Files", len(output_files))
    with col4:
        st.metric("Errors", len(results.get("errors", [])))
    
    st.markdown("---")
    
    # Preview Button
    st.markdown("### 🌐 Ecommerce Preview")
    
    # Generate and save HTML preview
    html_content = generate_ecommerce_html(product_data, faq_data, comparison_data)
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
        st.markdown("### 📝 Logs")
        if st.session_state.logs:
            for log in st.session_state.logs[-8:]:
                st.caption(log[:50] + "..." if len(log) > 50 else log)
    
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
