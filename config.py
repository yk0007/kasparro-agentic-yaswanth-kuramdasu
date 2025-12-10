"""
Configuration for Multi-Agent Content Generation System.

Centralized configuration for API keys, models, and logging.
Supports Gemini and Groq as LLM providers.
"""

import os
import logging
import random
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging Configuration
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL: int = logging.INFO
logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)
logger = logging.getLogger(__name__)

# ============ LLM Provider Selection ============
# Can be set via environment variable or changed at runtime
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")  # "gemini" or "groq"

# ============ Gemini Configuration ============
GEMINI_API_KEYS_STR = os.getenv("GEMINI_API_KEYS", os.getenv("GOOGLE_API_KEY", ""))
GEMINI_API_KEYS: List[str] = [k.strip() for k in GEMINI_API_KEYS_STR.split(",") if k.strip()]
GEMINI_MODEL: str = "gemini-2.5-flash-lite"

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
    if not GEMINI_API_KEYS:
        raise ValueError("No Gemini API keys configured")
    key = GEMINI_API_KEYS[_gemini_key_index]
    _gemini_key_index = (_gemini_key_index + 1) % len(GEMINI_API_KEYS)
    logger.debug(f"Using Gemini key ending in: ...{key[-4:]}")
    return key


def get_llm():
    """
    Get a configured LLM instance based on current provider setting.
    
    Returns:
        Configured LLM instance (Gemini or Groq)
    """
    if LLM_PROVIDER == "groq":
        return _get_groq_llm()
    else:
        return _get_gemini_llm()


def _get_gemini_llm():
    """Get Gemini LLM instance with key rotation."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    api_key = get_next_gemini_key()
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=api_key,
        temperature=DEFAULT_TEMPERATURE,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        max_retries=2
    )


def _get_groq_llm():
    """Get Groq LLM instance."""
    from langchain_groq import ChatGroq
    
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set in .env file")
    
    return ChatGroq(
        model=GROQ_MODEL,
        groq_api_key=GROQ_API_KEY,
        temperature=DEFAULT_TEMPERATURE,
        max_tokens=MAX_OUTPUT_TOKENS
    )


def get_grounded_llm():
    """Get LLM for grounded tasks (uses same as regular LLM)."""
    return get_llm()


def invoke_with_retry(prompt: str, max_attempts: int = 4) -> str:
    """
    Invoke LLM with automatic retry on rate limit errors.
    
    For Gemini: rotates API keys on rate limit.
    For Groq: retries with delay.
    
    Args:
        prompt: The prompt to send to the LLM
        max_attempts: Maximum number of attempts
        
    Returns:
        LLM response content as string
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
            
            # Check if it's a rate limit error
            if "429" in str(e) or "quota" in error_str or "rate" in error_str:
                logger.warning(f"Rate limit hit, retrying (attempt {attempt + 1}/{max_attempts})")
                time.sleep(2)  # Pause before retry
                continue
            else:
                raise e
    
    raise Exception(f"All attempts exhausted. Last error: {last_error}")


def get_available_providers() -> List[str]:
    """Get list of available LLM providers based on configured keys."""
    providers = []
    if GEMINI_API_KEYS:
        providers.append("gemini")
    if GROQ_API_KEY:
        providers.append("groq")
    return providers


def get_current_provider() -> str:
    """Get current LLM provider."""
    return LLM_PROVIDER


def get_current_model() -> str:
    """Get current model name based on provider."""
    if LLM_PROVIDER == "groq":
        return GROQ_MODEL
    return GEMINI_MODEL


# Output directory
OUTPUT_DIR: str = "output"

# Backward compatibility aliases
API_KEYS = GEMINI_API_KEYS
get_next_api_key = get_next_gemini_key
