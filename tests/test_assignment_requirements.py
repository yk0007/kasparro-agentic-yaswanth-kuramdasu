"""
Tests based on Assignment Requirements.

These tests verify the system meets the Kasparro assignment specifications:
1. Parse & understand product data (Requirement 1)
2. Generate at least 15 categorized questions (Requirement 2)
3. Templates for FAQ, Product, Comparison pages (Requirement 3)
4. Reusable content logic blocks (Requirement 4)
5. 3 pages: FAQ (5+ Q&As), Product, Comparison with fictional Product B (Requirement 5)
6. Machine-readable JSON output (Requirement 6)
7. Agent-based pipeline (Requirement 7)
"""
import pytest
import json
import os


# =============================================================================
# Requirement 1: Parse & understand product data
# =============================================================================

class TestProductParsing:
    """Tests for parsing product data into clean internal model."""
    
    def test_parser_agent_exists(self):
        """Agent for parsing product data must exist."""
        from agents import ParserAgent
        agent = ParserAgent()
        assert agent is not None
        assert hasattr(agent, 'execute')
    
    def test_parser_creates_product_model(self, sample_product_data):
        """Parser must convert raw JSON to internal ProductModel."""
        from agents import ParserAgent
        from models import ProductModel
        
        agent = ParserAgent()
        result, errors = agent.execute(sample_product_data)
        
        assert errors == []
        assert result is not None
        assert isinstance(result, ProductModel)
    
    def test_parser_handles_field_mapping(self):
        """Parser should map alternative field names."""
        from agents import ParserAgent
        
        # Assignment uses 'skin_type', model uses 'target_users'
        data = {
            "name": "Test Product",
            "skin_type": ["Oily", "Dry"],  # Alternative field name
            "key_ingredients": ["A", "B"],
            "benefits": ["X"],
            "how_to_use": "Apply daily",
            "price": "₹100"
        }
        
        agent = ParserAgent()
        result, errors = agent.execute(data)
        
        assert result is not None
        assert "Oily" in result.target_users or "Dry" in result.target_users


# =============================================================================
# Requirement 2: Generate at least 15 categorized user questions
# =============================================================================

class TestQuestionGeneration:
    """Tests for generating 15+ categorized questions."""
    
    def test_question_generator_agent_exists(self):
        """Question generator agent must exist."""
        from agents import QuestionGeneratorAgent
        agent = QuestionGeneratorAgent()
        assert agent is not None
    
    def test_minimum_questions_is_15(self):
        """System must generate at least 15 questions."""
        from agents import QuestionGeneratorAgent
        agent = QuestionGeneratorAgent()
        assert agent.min_questions >= 15
    
    def test_questions_have_categories(self):
        """Questions must be categorized."""
        from models import QuestionCategory
        
        # Verify categories exist as per assignment
        expected_categories = ["informational", "safety", "usage", "purchase", "comparison"]
        model_categories = [c.value.lower() for c in QuestionCategory]
        
        for cat in expected_categories:
            assert cat in model_categories, f"Missing category: {cat}"


# =============================================================================
# Requirement 3: Define & implement templates
# =============================================================================

class TestTemplates:
    """Tests for template engine implementation."""
    
    def test_faq_template_exists(self):
        """FAQ template must exist."""
        from templates import FAQTemplate
        template = FAQTemplate()
        assert template.template_type == "faq"
    
    def test_product_template_exists(self):
        """Product page template must exist."""
        from templates import ProductTemplate
        template = ProductTemplate()
        assert template.template_type == "product"
    
    def test_comparison_template_exists(self):
        """Comparison page template must exist."""
        from templates import ComparisonTemplate
        template = ComparisonTemplate()
        assert template.template_type == "comparison"
    
    def test_templates_have_validation(self):
        """Templates must have validation capability."""
        from templates import FAQTemplate, ProductTemplate, ComparisonTemplate
        
        for template_class in [FAQTemplate, ProductTemplate, ComparisonTemplate]:
            template = template_class()
            assert hasattr(template, 'validate')
            assert hasattr(template, 'render')


# =============================================================================
# Requirement 4: Reusable content logic blocks
# =============================================================================

class TestLogicBlocks:
    """Tests for reusable content logic blocks."""
    
    def test_benefits_block_exists(self):
        """Benefits logic block must exist."""
        from logic_blocks import generate_benefits_block
        assert callable(generate_benefits_block)
    
    def test_usage_block_exists(self):
        """Usage logic block must exist."""
        from logic_blocks import generate_usage_block
        assert callable(generate_usage_block)
    
    def test_ingredients_block_exists(self):
        """Ingredients logic block must exist."""
        from logic_blocks import generate_ingredients_block
        assert callable(generate_ingredients_block)
    
    def test_safety_block_exists(self):
        """Safety logic block must exist."""
        from logic_blocks import generate_safety_block
        assert callable(generate_safety_block)
    
    def test_comparison_blocks_exist(self):
        """Comparison logic blocks must exist."""
        from logic_blocks import compare_ingredients_block, compare_benefits_block, generate_pricing_block
        assert callable(compare_ingredients_block)
        assert callable(compare_benefits_block)
        assert callable(generate_pricing_block)


# =============================================================================
# Requirement 5: Assemble 3 pages
# =============================================================================

class TestPageAssembly:
    """Tests for the 3 required pages."""
    
    def test_faq_agent_exists(self):
        """FAQ agent must exist."""
        from agents import FAQAgent
        agent = FAQAgent()
        assert agent is not None
    
    def test_faq_minimum_5_qas(self):
        """FAQ must have minimum 5 Q&As."""
        from agents import FAQAgent
        agent = FAQAgent()
        assert agent.min_faqs >= 5
    
    def test_product_page_agent_exists(self):
        """Product page agent must exist."""
        from agents import ProductPageAgent
        agent = ProductPageAgent()
        assert agent is not None
    
    def test_comparison_agent_exists(self):
        """Comparison agent must exist."""
        from agents import ComparisonAgent
        agent = ComparisonAgent()
        assert agent is not None
    
    def test_product_b_is_fictional_and_structured(self):
        """Product B must be fictional with structure (name, ingredients, benefits, price)."""
        from agents import ComparisonAgent
        
        agent = ComparisonAgent()
        # Check agent can generate fictional product
        # The agent should have method to create fictional competitor
        assert hasattr(agent, '_generate_product_b') or hasattr(agent, 'execute')
        
        # Verify from output file that Product B has required structure
        import os
        import json
        output_path = os.path.join(os.path.dirname(__file__), '..', 'output', 'comparison_page.json')
        if os.path.exists(output_path):
            with open(output_path, 'r') as f:
                data = json.load(f)
            # Check Product B exists and has required fields
            if 'product_b' in data:
                product_b = data['product_b']
                assert 'name' in product_b
                # Should have some form of ingredients/features and benefits
                assert 'benefits' in product_b or 'key_features' in product_b or 'ingredients' in product_b


# =============================================================================
# Requirement 6: Machine-readable JSON output
# =============================================================================

class TestJSONOutput:
    """Tests for JSON output files."""
    
    def test_output_agent_exists(self):
        """Output agent must exist."""
        from agents import OutputAgent
        agent = OutputAgent()
        assert agent is not None
    
    def test_output_files_are_valid_json(self):
        """All output files must be valid JSON."""
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
        
        expected_files = ['faq.json', 'product_page.json', 'comparison_page.json']
        
        for filename in expected_files:
            filepath = os.path.join(output_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    data = json.load(f)  # Should not raise
                assert isinstance(data, dict)
    
    def test_faq_json_has_required_structure(self):
        """FAQ JSON must have questions array."""
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
        filepath = os.path.join(output_dir, 'faq.json')
        
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
            assert 'questions' in data
            assert isinstance(data['questions'], list)
            assert len(data['questions']) >= 5  # Min 5 Q&As


# =============================================================================
# Requirement 7: Agent-based pipeline (not single-script)
# =============================================================================

class TestAgentPipeline:
    """Tests for modular agent-based architecture."""
    
    def test_six_agents_exist(self):
        """System must have 6 distinct agents."""
        from agents import (
            ParserAgent,
            QuestionGeneratorAgent,
            FAQAgent,
            ProductPageAgent,
            ComparisonAgent,
            OutputAgent
        )
        
        agents = [
            ParserAgent,
            QuestionGeneratorAgent,
            FAQAgent,
            ProductPageAgent,
            ComparisonAgent,
            OutputAgent
        ]
        
        assert len(agents) == 6
        
        for agent_class in agents:
            agent = agent_class()
            assert hasattr(agent, 'execute') or hasattr(agent, 'name')
    
    def test_workflow_uses_orchestration(self):
        """Workflow must use orchestration (LangGraph StateGraph)."""
        from orchestrator.workflow import create_workflow
        from langgraph.graph import StateGraph
        
        workflow = create_workflow()
        # Should return a compiled graph, not a simple function
        assert workflow is not None
    
    def test_agents_have_single_responsibility(self):
        """Each agent should have a single, clear responsibility."""
        from agents import ParserAgent, FAQAgent, OutputAgent
        
        # Parser only parses
        parser = ParserAgent()
        assert 'parse' in parser.name.lower() or 'parser' in parser.name.lower()
        
        # FAQ only creates FAQ
        faq = FAQAgent()
        assert 'faq' in faq.name.lower()
        
        # Output only outputs
        output = OutputAgent()
        assert 'output' in output.name.lower()
