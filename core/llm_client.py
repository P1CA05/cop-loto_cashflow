"""
LLM client with error handling
"""
import os
import logging
from typing import Optional
import requests

logger = logging.getLogger(__name__)


def call_llm(prompt: str, model: str = "claude-sonnet-4-20250514") -> Optional[str]:
    """
    Call LLM API (OpenAI-compatible or Anthropic)
    
    Returns:
    - Generated text if successful
    - None if API key missing or error
    """
    
    # Check for API key
    api_key = os.environ.get('ANTHROPIC_API_KEY') or os.environ.get('OPENAI_API_KEY')
    
    if not api_key:
        logger.warning("No API key found (ANTHROPIC_API_KEY or OPENAI_API_KEY). Using rules-based report.")
        return None
    
    # Determine API type
    if os.environ.get('ANTHROPIC_API_KEY'):
        return _call_anthropic(prompt, api_key, model)
    else:
        return _call_openai_compatible(prompt, api_key, model)


def _call_anthropic(prompt: str, api_key: str, model: str) -> Optional[str]:
    """
    Call Anthropic Claude API
    """
    try:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        data = {
            "model": model,
            "max_tokens": 2000,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        logger.info(f"Calling Anthropic API with model {model}")
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            text = result['content'][0]['text']
            logger.info(f"LLM response received: {len(text)} chars")
            return text
        else:
            logger.error(f"Anthropic API error: {response.status_code} - {response.text}")
            return None
    
    except Exception as e:
        logger.error(f"Error calling Anthropic API: {e}")
        return None


def _call_openai_compatible(prompt: str, api_key: str, model: str) -> Optional[str]:
    """
    Call OpenAI-compatible API (OpenAI, Azure OpenAI, etc.)
    """
    try:
        url = os.environ.get('OPENAI_API_BASE', 'https://api.openai.com/v1') + '/chat/completions'
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Use gpt-4 if model contains 'claude' (fallback)
        if 'claude' in model.lower():
            model = 'gpt-4'
        
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": "Eres un asesor financiero experto en análisis de cashflow para PYMEs."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 2000,
            "temperature": 0.3
        }
        
        logger.info(f"Calling OpenAI-compatible API with model {model}")
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            text = result['choices'][0]['message']['content']
            logger.info(f"LLM response received: {len(text)} chars")
            return text
        else:
            logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
            return None
    
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        return None
