"""
Configuration for Multi-Agent Content Generation System.

Groq-Only LLM Provider (llama-3.3-70b-versatile).
"""

import os
import logging
import time
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging Configuration
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL: int = logging.INFO
logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)
logger = logging.getLogger(__name__)


def get_secret(key: str, default: str = "") -> str:
    """Get secret from Streamlit secrets or environment variable.
    
    This function checks st.secrets first (for Streamlit Cloud),
    then falls back to environment variables (for local development).
    """
    # Try Streamlit secrets first (for Streamlit Cloud deployment)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    # Fall back to environment variable
    return os.getenv(key, default)


# ============ Groq Configuration (Only LLM Provider) ============
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = "llama-3.3-70b-versatile"

# ============ Common Parameters ============
DEFAULT_TEMPERATURE: float = 0.7
MAX_OUTPUT_TOKENS: int = 2048


def get_llm():
    """
    Get a configured Groq LLM instance for content generation.
    Uses llama-3.3-70b-versatile model.
    """
    return _get_groq_llm()


def _get_groq_llm():
    """Get Groq LLM instance."""
    from langchain_groq import ChatGroq
    
    # Get API key dynamically (supports both .env and st.secrets)
    api_key = get_secret("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set. Add to .env file or Streamlit secrets.")
    
    return ChatGroq(
        model=GROQ_MODEL,
        groq_api_key=api_key,
        temperature=DEFAULT_TEMPERATURE,
        max_tokens=MAX_OUTPUT_TOKENS
    )


def invoke_with_retry(prompt: str, max_attempts: int = 4) -> str:
    """
    Invoke LLM with automatic retry on rate limit errors.
    
    Args:
        prompt: The prompt to send to the LLM
        max_attempts: Maximum number of retry attempts
        
    Returns:
        LLM response content as string
    """
    last_error = None
    
    for attempt in range(max_attempts):
        try:
            llm = get_llm()
            response = llm.invoke(prompt)
            return response.content
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            
            if "429" in str(e) or "quota" in error_str or "rate" in error_str:
                logger.warning(f"Rate limit hit, retrying (attempt {attempt + 1}/{max_attempts})")
                time.sleep(2)
                continue
            else:
                raise e
    
    raise Exception(f"All attempts exhausted. Last error: {last_error}")


def get_available_providers() -> List[str]:
    """Get list of available LLM providers based on configured keys.
    
    Checks both environment variables and Streamlit secrets dynamically.
    Returns ["groq"] if GROQ_API_KEY is configured, otherwise empty list.
    """
    providers = []
    # Check dynamically at runtime (important for Streamlit Cloud)
    groq_key = get_secret("GROQ_API_KEY", "")
    
    if groq_key.strip():
        providers.append("groq")
    return providers


def get_current_provider() -> str:
    """Get current LLM provider (always 'groq')."""
    return "groq"


def get_current_model() -> str:
    """Get current model name."""
    return GROQ_MODEL


# Output directory
OUTPUT_DIR: str = "output"
