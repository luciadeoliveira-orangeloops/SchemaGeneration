# llm/openai_client.py
import os
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OpenAIClient:
    """OpenAI API client with flexible token handling"""
    
    def __init__(self):
        self.client = OpenAI()  # uses OPENAI_API_KEY from the environment
        self.default_model = os.getenv("LLM_MODEL", "gpt-5")
    
    def run_model(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 6000,
        max_output_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        response_format: Optional[dict] = None
    ) -> str:
        """
        Execute a prompt and return the response
        Supports both legacy and new parameter names
        """
        target_model = model or self.default_model
        
        print(f"🤖 [LLM] Starting API call to model: {target_model}")
        print(f"🤖 [LLM] Prompt length: {len(prompt)} characters")
        
        # Prepare API parameters
        api_params = {
            "model": target_model,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        # Handle token limits - use new parameter name for newer models
        if max_output_tokens is not None:
            api_params["max_completion_tokens"] = max_output_tokens
            print(f"🤖 [LLM] Max completion tokens: {max_output_tokens}")
        elif target_model.startswith("gpt-5"):
            # Use max_completion_tokens for GPT-5
            api_params["max_completion_tokens"] = max_tokens
            print(f"🤖 [LLM] Max completion tokens: {max_tokens}")
        else:
            # Use max_tokens for older models
            api_params["max_tokens"] = max_tokens
            print(f"🤖 [LLM] Max tokens: {max_tokens}")
        
        # Add temperature if specified (GPT-5 doesn't support it)
        if temperature is not None and not target_model.startswith("gpt-5"):
            api_params["temperature"] = temperature
            print(f"🤖 [LLM] Temperature: {temperature}")
        
        # Add response format if specified
        if response_format is not None:
            api_params["response_format"] = response_format
            print(f"🤖 [LLM] Response format: {response_format}")
        
        try:
            print(f"🤖 [LLM] Calling OpenAI API...")
            resp = self.client.chat.completions.create(**api_params)
            print(f"🤖 [LLM] API call completed successfully")
            
            result = resp.choices[0].message.content
            print(f"🤖 [LLM] Response length: {len(result)} characters")
            return result
            
        except Exception as e:
            print(f"❌ [LLM] API call failed: {e}")
            raise

# Legacy function for backward compatibility
_client_instance = OpenAIClient()

def run_model(
    prompt: str,
    model: Optional[str] = None,
    max_output_tokens: int = 6000,
    temperature: float = 0.1,
) -> str:
    """
    Legacy function for backward compatibility
    """
    return _client_instance.run_model(
        prompt=prompt,
        model=model,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        response_format={"type": "json_object"}
    )
