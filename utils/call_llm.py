from openai import OpenAI
import os
import logging
from typing import Optional

# Global client instance for reuse
_client_cache = {}

def get_llm_client(api_key: str = None, base_url: str = None) -> OpenAI:
    """Get or create OpenAI client with specified configuration"""
    # Use configuration from parameters or environment variables
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    base_url = base_url or os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
    
    if not api_key:
        raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
    
    # Create cache key
    cache_key = f"{api_key[:8]}_{base_url}"
    
    # Return cached client if available
    if cache_key in _client_cache:
        return _client_cache[cache_key]
    
    # Create new client
    try:
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        _client_cache[cache_key] = client
        logging.debug(f"Created new OpenAI client for base_url: {base_url}")
        return client
    except Exception as e:
        logging.error(f"Failed to create OpenAI client: {e}")
        raise

def call_llm(prompt: str, model: str = None, api_key: str = None, 
             base_url: str = None, max_tokens: int = None, 
             temperature: float = None) -> str:
    """
    Call LLM with configurable parameters
    
    Args:
        prompt: The input prompt
        model: Model name (defaults to AI_MODEL env var or gpt-4o-mini)
        api_key: API key (defaults to OPENAI_API_KEY env var)
        base_url: API base URL (defaults to OPENAI_API_BASE env var)
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature (0-2)
    
    Returns:
        Generated text response
    """
    # Get configuration from environment if not provided
    model = model or os.environ.get("AI_MODEL", "gpt-4o-mini")
    
    try:
        # Get configured client
        client = get_llm_client(api_key=api_key, base_url=base_url)
        
        # Prepare request parameters
        request_params = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        # Add optional parameters if provided
        if max_tokens:
            request_params["max_tokens"] = max_tokens
        if temperature is not None:
            request_params["temperature"] = temperature
        
        # Make API call
        response = client.chat.completions.create(**request_params)
        
        # Extract and return content
        content = response.choices[0].message.content
        if not content:
            raise ValueError("LLM returned empty response")
        
        return content
        
    except Exception as e:
        logging.error(f"LLM API call failed: {e}")
        raise

def call_llm_with_config(prompt: str, config: dict = None) -> str:
    """
    Call LLM using configuration object
    
    Args:
        prompt: The input prompt
        config: Configuration dictionary with LLM settings
    
    Returns:
        Generated text response
    """
    if not config:
        # Load config if not provided
        try:
            from utils.config import load_config
            cfg = load_config()
            config = cfg.to_dict()
        except ImportError:
            # Fallback to environment variables
            config = {}
    
    return call_llm(
        prompt=prompt,
        model=config.get("ai_model"),
        api_key=config.get("openai_api_key"),
        base_url=config.get("openai_api_base"),
        max_tokens=config.get("max_tokens"),
        temperature=config.get("temperature")
    )

def test_llm_connection(api_key: str = None, base_url: str = None, 
                       model: str = None) -> bool:
    """
    Test LLM connection with given configuration
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        test_prompt = "Hello, respond with 'OK' if you can read this."
        response = call_llm(
            prompt=test_prompt,
            model=model,
            api_key=api_key,
            base_url=base_url,
            max_tokens=10
        )
        
        # Check if response contains expected content
        success = response and len(response.strip()) > 0
        logging.info(f"LLM connection test {'successful' if success else 'failed'}")
        return success
        
    except Exception as e:
        logging.error(f"LLM connection test failed: {e}")
        return False

if __name__ == "__main__":
    # Test the LLM function
    try:
        # Test with default configuration
        print("Testing LLM with default configuration...")
        prompt = "What is the meaning of life? Respond in one sentence."
        response = call_llm(prompt)
        print(f"Response: {response}")
        
        # Test connection
        print("\nTesting connection...")
        if test_llm_connection():
            print("✅ LLM connection successful")
        else:
            print("❌ LLM connection failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
