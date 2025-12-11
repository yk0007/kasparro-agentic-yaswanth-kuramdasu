"""
Integration tests for LangGraph workflow.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestWorkflowIntegration:
    """Integration tests for the LangGraph workflow."""
    
    def test_workflow_uses_langgraph_invoke(self):
        """Test that run_workflow uses compiled.invoke() not manual execution."""
        from orchestrator.workflow import run_workflow
        import inspect
        
        source = inspect.getsource(run_workflow)
        
        # Should use compiled.invoke()
        assert "compiled.invoke" in source or "compiled = create_workflow()" in source
        
        # Should NOT have manual step iteration
        assert "for i, (step_name, step_fn) in enumerate(steps)" not in source
        assert 'steps = [' not in source
    
    def test_create_workflow_returns_compiled_graph(self):
        """Test that create_workflow returns a compiled StateGraph."""
        from orchestrator.workflow import create_workflow
        
        compiled = create_workflow()
        
        # Should be a compiled graph with invoke method
        assert compiled is not None
        assert hasattr(compiled, "invoke")
    
    def test_workflow_state_initialization(self, sample_product_data):
        """Test that initial state is created correctly."""
        from orchestrator.state import create_initial_state
        
        state = create_initial_state(sample_product_data)
        
        assert "product_data" in state
        assert "current_step" in state
        assert "errors" in state
        assert state["product_data"] == sample_product_data
        assert state["current_step"] == "initialized"
    
    def test_workflow_node_functions_exist(self):
        """Test that all node functions are defined."""
        from orchestrator import workflow
        
        # All required node functions should exist
        assert hasattr(workflow, "parse_node")
        assert hasattr(workflow, "generate_questions_node")
        assert hasattr(workflow, "faq_node")
        assert hasattr(workflow, "product_page_node")
        assert hasattr(workflow, "comparison_node")
        assert hasattr(workflow, "output_node")


class TestNoExternalSearch:
    """Tests verifying no external search is used."""
    
    def test_config_no_grounding_functions(self):
        """Test that config.py does not have grounding functions."""
        import config
        
        # These functions should not exist in Groq-only config
        assert not hasattr(config, "invoke_grounded")
        assert not hasattr(config, "is_grounding_available")
        assert not hasattr(config, "get_grounded_llm")
    
    def test_config_groq_only(self):
        """Test that config uses Groq."""
        import config
        
        assert hasattr(config, "GROQ_MODEL")
        assert hasattr(config, "_get_groq_llm")
        assert config.GROQ_MODEL == "llama-3.3-70b-versatile"


class TestFAQMinimumQuestions:
    """Tests verifying FAQ generates 15+ questions."""
    
    def test_question_generator_min_questions(self):
        """Test that QuestionGeneratorAgent has min_questions = 15."""
        from agents import QuestionGeneratorAgent
        
        agent = QuestionGeneratorAgent()
        assert agent.min_questions == 15
    
    def test_faq_agent_min_faqs(self):
        """Test that FAQAgent has min_faqs = 15."""
        from agents import FAQAgent
        
        agent = FAQAgent()
        assert agent.min_faqs == 15
        assert FAQAgent.MIN_FAQ_QUESTIONS == 15
    
    def test_question_prompt_requests_correct_count(self):
        """Test that the prompt requests the correct number of questions."""
        from agents import QuestionGeneratorAgent
        from models import ProductModel
        
        agent = QuestionGeneratorAgent()
        product = ProductModel(
            name="Test",
            product_type="Test",
            target_users=["User"],
            key_features=["Feature"],
            benefits=["Benefit"],
            how_to_use="Use it",
            considerations="None",
            price="$10"
        )
        
        prompt = agent._build_prompt(product)
        
        # Prompt should reference self.min_questions (15)
        assert "15" in prompt or str(agent.min_questions) in prompt
