"""
HTML Generator Service.

Responsible for generating ecommerce preview HTML from product data.
Extracted from app.py for better separation of concerns.
"""

from typing import Dict, Any, List


class HtmlGenerator:
    """
    Generates modern ecommerce preview HTML from product, FAQ, and comparison data.
    
    This service handles all dynamic content extraction including:
    - Normalized price fields (with backward compatibility)
    - LLM-enriched blocks (benefits, usage, ingredients)
    - Comparison tables and FAQ sections
    """
    
    def generate(
        self,
        product_data: Dict[str, Any],
        faq_data: Dict[str, Any],
        comparison_data: Dict[str, Any]
    ) -> str:
        """
        Generate minimal modern ecommerce preview HTML with fully dynamic content.
        
        Args:
            product_data: Product page JSON data
            faq_data: FAQ page JSON data
            comparison_data: Comparison page JSON data
            
        Returns:
            Complete HTML document as string
        """
        product = product_data.get("product", {})
        product_a = comparison_data.get("products", {}).get("product_a", {})
        product_b = comparison_data.get("products", {}).get("product_b", {})
        questions = faq_data.get("questions", [])
        
        # Get product name and basic info
        name = product.get('name') or product_a.get('name') or 'Product'
        product_type = product.get('product_type') or product_a.get('product_type') or ''
        
        # Handle both normalized_price (new) and price (legacy/string)
        price = self._extract_price(product, product_a)
        target = product.get('suitable_for', []) or product_a.get('target_users', [])
        
        # Get product description
        description = self._extract_description(product)
        
        # Get LLM-enriched content
        benefits_html = self._build_benefits_html(product)
        features_html = self._build_features_html(product)
        usage_html = self._build_usage_html(product)
        target_html = ', '.join(target) if target else 'Everyone'
        faq_html = self._build_faq_html(questions)
        
        return self._build_html_document(
            name=name,
            product_type=product_type,
            description=description,
            price=price,
            features_html=features_html,
            benefits_html=benefits_html,
            usage_html=usage_html,
            target_html=target_html,
            product_a=product_a,
            product_b=product_b,
            faq_html=faq_html
        )
    
    def _extract_price(self, product: Dict, product_a: Dict) -> str:
        """Extract price, preferring normalized_price if available."""
        # Try normalized_price first (new format)
        normalized = product.get('normalized_price')
        if isinstance(normalized, dict):
            amount = normalized.get('amount', '')
            currency = normalized.get('currency', '')
            if amount:
                symbol = '₹' if currency == 'INR' else '$' if currency == 'USD' else ''
                return f"{symbol}{amount}"
        
        # Fall back to legacy price field
        price = product.get('price')
        if isinstance(price, dict):
            return price.get('amount', '')
        elif isinstance(price, str):
            return price
        
        # Try product_a as last resort
        return product_a.get('price', '')
    
    def _extract_description(self, product: Dict) -> str:
        """Extract product description from various sources."""
        description = product.get('headline') or product.get('tagline') or ''
        if not description:
            benefits_list = product.get('benefits', {})
            if isinstance(benefits_list, dict):
                primary = benefits_list.get('primary_benefits', [])
                if primary:
                    description = ' • '.join(primary[:2])
            elif isinstance(benefits_list, list) and benefits_list:
                description = ' • '.join(benefits_list[:2])
        return description
    
    def _build_benefits_html(self, product: Dict) -> str:
        """Build HTML for benefits section."""
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
        return benefits_html
    
    def _build_features_html(self, product: Dict) -> str:
        """Build HTML for features/ingredients tags."""
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
        return features_html
    
    def _build_usage_html(self, product: Dict) -> str:
        """Build HTML for usage instructions."""
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
        return usage_html
    
    def _build_faq_html(self, questions: List[Dict]) -> str:
        """Build HTML for FAQ section with collapsible items."""
        faq_html = ''
        for q in questions[:5]:
            faq_html += f'''
        <details class="faq-item">
            <summary class="faq-q">{q.get('question', '')}</summary>
            <div class="faq-a">{q.get('answer', '')}</div>
        </details>'''
        return faq_html
    
    def _build_html_document(
        self,
        name: str,
        product_type: str,
        description: str,
        price: str,
        features_html: str,
        benefits_html: str,
        usage_html: str,
        target_html: str,
        product_a: Dict,
        product_b: Dict,
        faq_html: str
    ) -> str:
        """Build the complete HTML document."""
        return f'''<!DOCTYPE html>
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
        Generated by Multi-Agent Content System • Powered by LangGraph + Groq
    </footer>
</body>
</html>'''
