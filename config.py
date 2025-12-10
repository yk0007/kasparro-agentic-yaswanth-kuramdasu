"""
Configuration for Multi-Agent Content Generation System.

Centralized configuration for API keys, models, and logging.
Supports multiple API keys with rotation for rate limit avoidance.
"""

import os
import logging
import random
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys - Read from environment variable (comma-separated)
# Set GEMINI_API_KEYS in .env: GEMINI_API_KEYS=key1,key2,key3,key4
_api_keys_str = os.getenv("GEMINI_API_KEYS", os.getenv("GOOGLE_API_KEY", ""))
API_KEYS: List[str] = [k.strip() for k in _api_keys_str.split(",") if k.strip()]

if not API_KEYS:
    raise ValueError("No API keys found. Set GEMINI_API_KEYS or GOOGLE_API_KEY in .env file")

# Current key index for rotation
_current_key_index = 0

def get_next_api_key() -> str:
    """Get next API key using round-robin rotation."""
    global _current_key_index
    key = API_KEYS[_current_key_index]
    _current_key_index = (_current_key_index + 1) % len(API_KEYS)
    logger.debug(f"Using API key ending in: ...{key[-4:]}")
    return key

def get_random_api_key() -> str:
    """Get a random API key."""
    return random.choice(API_KEYS)

# Model Configuration
DEFAULT_MODEL: str = "gemini-2.5-flash-lite"
GROUNDED_MODEL: str = "gemini-2.5-flash-lite"

# Generation Parameters
DEFAULT_TEMPERATURE: float = 0.7
MAX_OUTPUT_TOKENS: int = 2048

# Logging Configuration
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL: int = logging.INFO

# Configure logging
logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)
logger = logging.getLogger(__name__)


def get_llm(force_new_key: bool = True):
    """
    Get a configured LangChain ChatGoogleGenerativeAI instance.
    
    Always uses a new rotated API key by default.
    
    Args:
        force_new_key: If True, rotates to next API key
        
    Returns:
        Configured ChatGoogleGenerativeAI instance
    """
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    api_key = get_next_api_key() if force_new_key else API_KEYS[0]
    
    return ChatGoogleGenerativeAI(
        model=DEFAULT_MODEL,
        google_api_key=api_key,
        temperature=DEFAULT_TEMPERATURE,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        max_retries=2  # Reduce retries so we can rotate keys faster
    )


def get_grounded_llm(force_new_key: bool = True):
    """
    Get LLM with Google Search grounding for Product B generation.
    
    Args:
        force_new_key: If True, rotates to next API key
        
    Returns:
        Configured ChatGoogleGenerativeAI with grounding
    """
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    api_key = get_next_api_key() if force_new_key else API_KEYS[0]
    
    return ChatGoogleGenerativeAI(
        model=GROUNDED_MODEL,
        google_api_key=api_key,
        temperature=DEFAULT_TEMPERATURE,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        max_retries=2  # Reduce retries so we can rotate keys faster
    )


def invoke_with_retry(prompt: str, max_attempts: int = 4) -> str:
    """
    Invoke LLM with automatic key rotation on rate limit errors.
    
    Args:
        prompt: The prompt to send to the LLM
        max_attempts: Maximum number of attempts (one per API key)
        
    Returns:
        LLM response content as string
        
    Raises:
        Exception: If all API keys are exhausted
    """
    import time
    
    last_error = None
    
    for attempt in range(max_attempts):
        try:
            llm = get_llm(force_new_key=True)
            response = llm.invoke(prompt)
            return response.content
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            
            # Check if it's a rate limit error
            if "429" in str(e) or "quota" in error_str or "rate" in error_str:
                logger.warning(f"Rate limit hit, rotating to next API key (attempt {attempt + 1}/{max_attempts})")
                time.sleep(1)  # Brief pause before retry
                continue
            else:
                # Not a rate limit error, re-raise
                raise e
    
    # All keys exhausted
    raise Exception(f"All API keys exhausted. Last error: {last_error}")


# Output directory
OUTPUT_DIR: str = "output"
