"""
Configuration for Multi-Agent Content Generation System.

Supports two LLM providers:
- Gemini: Uses gemma-3-27b for content generation + gemini-flash-latest (grounded) for real competitor
- Groq: Uses llama-3.3-70b for all tasks (fictional competitor)
"""

import os
import logging
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

# ============ LLM Provider Selection ============
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")  # "gemini" or "groq"

# ============ Gemini Configuration ============
GEMINI_API_KEYS_STR = os.getenv("GEMINI_API_KEYS", os.getenv("GOOGLE_API_KEY", ""))
GEMINI_API_KEYS: List[str] = [k.strip() for k in GEMINI_API_KEYS_STR.split(",") if k.strip()]

# Model for general content generation
GEMINI_CONTENT_MODEL: str = "gemma-3-1b-it"
# Model for grounded Product B generation (supports Google Search)
GEMINI_GROUNDED_MODEL: str = "gemini-2.0-flash"

# ============ Groq Configuration ============
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = "llama-3.3-70b-versatile"

# ============ Common Parameters ============
DEFAULT_TEMPERATURE: float = 0.7
MAX_OUTPUT_TOKENS: int = 2048

# Current key index for Gemini rotation
_gemini_key_index = 0


def set_llm_provider(provider: str):
    """Set the LLM provider at runtime."""
    global LLM_PROVIDER
    if provider.lower() in ["gemini", "groq"]:
        LLM_PROVIDER = provider.lower()
        logger.info(f"LLM provider set to: {LLM_PROVIDER}")
    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Use 'gemini' or 'groq'")


def get_next_gemini_key() -> str:
    """Get next Gemini API key using round-robin rotation."""
    global _gemini_key_index
    
    # Get API keys dynamically (supports both .env and st.secrets)
    keys_str = get_secret("GEMINI_API_KEYS", get_secret("GOOGLE_API_KEY", ""))
    keys = [k.strip() for k in keys_str.split(",") if k.strip()]
    
    if not keys:
        raise ValueError("No Gemini API keys configured. Add to .env or Streamlit secrets.")
    
    key = keys[_gemini_key_index % len(keys)]
    _gemini_key_index = (_gemini_key_index + 1) % len(keys)
    return key


def get_llm():
    """
    Get a configured LLM instance for general content generation.
    - Gemini: uses gemma-3-27b-it
    - Groq: uses llama-3.3-70b-versatile
    """
    if LLM_PROVIDER == "groq":
        return _get_groq_llm()
    else:
        return _get_gemini_content_llm()


def _get_gemini_content_llm():
    """Get Gemini LLM for content generation (gemma-3-27b)."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    api_key = get_next_gemini_key()
    return ChatGoogleGenerativeAI(
        model=GEMINI_CONTENT_MODEL,
        google_api_key=api_key,
        temperature=DEFAULT_TEMPERATURE,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        max_retries=2
    )


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


def get_grounded_llm():
    """
    Get LLM with Google Search grounding for Product B generation.
    Only available with Gemini provider.
    """
    if LLM_PROVIDER == "groq":
        # Groq doesn't support grounding, use regular LLM
        return _get_groq_llm()
    
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    api_key = get_next_gemini_key()
    return ChatGoogleGenerativeAI(
        model=GEMINI_GROUNDED_MODEL,
        google_api_key=api_key,
        temperature=DEFAULT_TEMPERATURE,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        max_retries=2
    )


def invoke_with_retry(prompt: str, max_attempts: int = 4) -> str:
    """
    Invoke LLM with automatic retry on rate limit errors.
    """
    import time
    
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


def invoke_grounded(prompt: str, max_attempts: int = 3) -> str:
    """
    Invoke grounded LLM for Product B generation.
    Uses Google Search grounding when Gemini is selected.
    """
    import time
    
    last_error = None
    
    for attempt in range(max_attempts):
        try:
            llm = get_grounded_llm()
            response = llm.invoke(prompt)
            return response.content
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            
            if "429" in str(e) or "quota" in error_str or "rate" in error_str:
                logger.warning(f"Rate limit hit on grounded call, retrying (attempt {attempt + 1}/{max_attempts})")
                time.sleep(2)
                continue
            else:
                raise e
    
    raise Exception(f"Grounded call failed. Last error: {last_error}")


def get_available_providers() -> List[str]:
    """Get list of available LLM providers based on configured keys.
    
    Checks both environment variables and Streamlit secrets dynamically.
    """
    providers = []
    # Check dynamically at runtime (important for Streamlit Cloud)
    groq_key = get_secret("GROQ_API_KEY", "")
    gemini_keys = get_secret("GEMINI_API_KEYS", get_secret("GOOGLE_API_KEY", ""))
    
    if gemini_keys.strip():
        providers.append("gemini")
    if groq_key.strip():
        providers.append("groq")
    return providers


def get_current_provider() -> str:
    """Get current LLM provider."""
    return LLM_PROVIDER


def get_current_model() -> str:
    """Get current model name based on provider."""
    if LLM_PROVIDER == "groq":
        return GROQ_MODEL
    return GEMINI_CONTENT_MODEL


def is_grounding_available() -> bool:
    """Check if grounding is available (only with Gemini)."""
    return LLM_PROVIDER == "gemini" and bool(GEMINI_API_KEYS)


# Output directory
OUTPUT_DIR: str = "output"

# Backward compatibility
API_KEYS = GEMINI_API_KEYS
get_next_api_key = get_next_gemini_key
