"""
Configuration for Multi-Agent Content Generation System.

Groq-Only LLM Provider (llama-3.3-70b-versatile).
"""

import os
import logging
import time
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging Configuration with Secret Protection
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL: int = logging.INFO


class SecretFilter(logging.Filter):
    """Filter to prevent accidental logging of sensitive information."""
    
    SENSITIVE_PATTERNS = ["api_key", "apikey", "secret", "password", "token", "groq_api"]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Redact sensitive information from log messages."""
        message = str(record.msg).lower()
        for pattern in self.SENSITIVE_PATTERNS:
            if pattern in message:
                # Don't block the log, but warn about potential leak
                record.msg = f"[REDACTED - potential secret in log] {record.msg[:50]}..."
                break
        return True


# Apply secret filter to all loggers
logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)
for handler in logging.root.handlers:
    handler.addFilter(SecretFilter())
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


# Track key rotation index and client cache
_key_index = 0
_client_cache: Dict[str, Any] = {}  # Per-key client cache


def _get_api_keys() -> List[str]:
    """
    Get list of API keys with validation.
    
    Supports comma-separated multiple keys for rotation.
    Validates key length and logs warnings without exposing key values.
    """
    key_string = get_secret("GROQ_API_KEY", "")
    if not key_string:
        return []
    
    raw_keys = [k.strip() for k in key_string.split(",")]
    keys: List[str] = []
    
    for idx, k in enumerate(raw_keys):
        if not k:
            continue
        if len(k) < 8:
            logger.warning(
                "GROQ_API_KEY entry %d appears too short or malformed and will be ignored",
                idx
            )
            continue
        keys.append(k)
    
    if not keys:
        logger.warning("No valid GROQ_API_KEY entries found after validation")
    
    return keys


def _get_next_key() -> str:
    """Get next API key using rotation for load balancing."""
    global _key_index
    keys = _get_api_keys()
    if not keys:
        raise ValueError("GROQ_API_KEY not set. Add to .env file or Streamlit secrets.")
    key = keys[_key_index % len(keys)]
    _key_index += 1
    return key


def _get_cached_client(api_key: str) -> Any:
    """Get or create cached ChatGroq client for the given API key."""
    from langchain_groq import ChatGroq
    
    if api_key not in _client_cache:
        _client_cache[api_key] = ChatGroq(
            model=GROQ_MODEL,
            groq_api_key=api_key,
            temperature=DEFAULT_TEMPERATURE,
            max_tokens=MAX_OUTPUT_TOKENS
        )
    return _client_cache[api_key]


def invoke_with_retry(prompt: str, max_attempts: int = 4) -> str:
    """
    Invoke LLM with automatic API key rotation and exponential backoff.
    
    Features:
    - Client caching: reuses ChatGroq instances per API key
    - Key rotation: cycles through multiple API keys if provided
    - Exponential backoff with jitter: reduces thundering herd on rate limits
    - Sanitized logging: avoids exposing provider-specific error details
    
    Args:
        prompt: The prompt to send to the LLM
        max_attempts: Maximum number of retry attempts
        
    Returns:
        LLM response content as string
    """
    import random
    
    last_error = None
    
    for attempt in range(max_attempts):
        try:
            api_key = _get_next_key()  # Rotate to next key
            llm = _get_cached_client(api_key)  # Reuse cached client
            response = llm.invoke(prompt)
            return response.content
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            
            if "429" in str(e) or "quota" in error_str or "rate" in error_str:
                # Exponential backoff with jitter
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                logger.warning(
                    "Rate limit hit, rotating key and retrying in %.1fs (attempt %d/%d)",
                    wait_time,
                    attempt + 1,
                    max_attempts
                )
                time.sleep(wait_time)
                continue
            else:
                # Do not log full exception details; just re-raise
                raise e
    
    # Sanitized error message without exposing provider details
    raise Exception("All attempts exhausted after key rotation.")


def invoke_with_metrics(prompt: str, max_attempts: int = 4) -> tuple:
    """
    Invoke LLM with metrics tracking for observability.
    
    Returns both the response content and a metrics dict containing:
    - prompt_hash: MD5 hash of prompt (first 8 chars)
    - tokens_in: Input tokens (real count via get_num_tokens or estimate)
    - tokens_out: Output tokens (real count via get_num_tokens or estimate)
    - output_len: Length of response in characters
    
    Args:
        prompt: The prompt to send to the LLM
        max_attempts: Maximum number of retry attempts
        
    Returns:
        Tuple of (response_content: str, metrics: Dict, prompt_text: str)
    """
    import hashlib
    import random
    from langchain_groq import ChatGroq
    
    # Compute prompt hash for tracking
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
    
    last_error = None
    
    for attempt in range(max_attempts):
        try:
            api_key = _get_next_key()
            llm = _get_cached_client(api_key)
            
            # Try to get real token count using get_num_tokens
            try:
                tokens_in = llm.get_num_tokens(prompt)
            except Exception:
                tokens_in = len(prompt) // 4  # Fallback estimate
            
            response = llm.invoke(prompt)
            response_text = response.content
            
            # Try to get real output token count
            try:
                tokens_out = llm.get_num_tokens(response_text)
            except Exception:
                tokens_out = len(response_text) // 4  # Fallback estimate
            
            # Build metrics
            metrics = {
                "prompt_hash": prompt_hash,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "output_len": len(response_text)
            }
            
            return response_text, metrics, prompt
            
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            
            if "429" in str(e) or "quota" in error_str or "rate" in error_str:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                logger.warning(
                    "Rate limit hit, rotating key and retrying in %.1fs (attempt %d/%d)",
                    wait_time,
                    attempt + 1,
                    max_attempts
                )
                time.sleep(wait_time)
                continue
            else:
                raise e
    
    raise Exception("All attempts exhausted after key rotation.")


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
