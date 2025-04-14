"""
LLM Client for the TTA.dev Framework.

This module provides a client for interacting with various LLM providers,
including local models, Ollama, and potentially other API-based services.
"""

import os
import json
import logging
import signal
from contextlib import contextmanager
from typing import Dict, Any, Optional, List, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TimeoutException(Exception):
    """Exception raised when a timeout occurs."""
    pass


@contextmanager
def timeout(seconds):
    """Context manager for timing out operations."""

    def signal_handler(signum, frame):
        raise TimeoutException(f"Timed out after {seconds} seconds")

    # Set the timeout handler
    original_handler = signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, original_handler)


# Load model configuration from environment variables
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "")
MODEL_CACHE_DIR = os.getenv("MODEL_CACHE_DIR", "/app/.model_cache")

# Check which model backend to use
USE_HF_MODELS = os.getenv("USE_HF_MODELS", "false").lower() == "true"
USE_OLLAMA = os.getenv("USE_OLLAMA", "false").lower() == "true"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Optimization settings
USE_QUANTIZATION = os.getenv("USE_QUANTIZATION", "none").lower()  # "4bit", "8bit", or "none"
USE_BETTER_TRANSFORMER = os.getenv("USE_BETTER_TRANSFORMER", "true").lower() == "true"

# Default generation settings
DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
DEFAULT_MAX_TOKENS = int(os.getenv("DEFAULT_MAX_TOKENS", "1024"))

# Flag to determine if transformers is available
TRANSFORMERS_AVAILABLE = False
CUDA_AVAILABLE = False

# Check for Hugging Face token
HF_TOKEN = os.getenv("HF_TOKEN", None)
if HF_TOKEN:
    logger.info("Hugging Face token found in environment variables.")
else:
    try:
        # Check if token exists in the default location
        from huggingface_hub import HfFolder

        if HfFolder().get_token():
            HF_TOKEN = HfFolder().get_token()
            logger.info("Hugging Face token found in default location.")
        else:
            logger.warning(
                "No Hugging Face token found. Some models may not be accessible."
            )
    except ImportError:
        logger.warning("huggingface_hub not available. Cannot check for HF token.")

# Try to import transformers
try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from huggingface_hub import login

    # Try to login if token is available
    if HF_TOKEN:
        try:
            login(token=HF_TOKEN, add_to_git_credential=False)
            logger.info("Successfully logged in to Hugging Face.")
        except Exception as e:
            logger.warning(f"Failed to login to Hugging Face: {e}")

    TRANSFORMERS_AVAILABLE = True
    logger.info("Transformers library is available. Using local models.")

    # Check for CUDA availability
    try:
        CUDA_AVAILABLE = torch.cuda.is_available()
        if CUDA_AVAILABLE:
            logger.info(f"CUDA is available. Found {torch.cuda.device_count()} GPU(s).")
        else:
            logger.warning("CUDA is not available. Using CPU for inference.")
    except Exception as e:
        logger.warning(f"Error checking CUDA availability: {e}. Assuming CPU only.")

except ImportError:
    logger.warning("Transformers library not available. Using mock responses.")


class Message:
    """A message in a conversation."""

    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

    def to_dict(self):
        return {"role": self.role, "content": self.content}


# Default timeout for operations
DEFAULT_TIMEOUT = 60.0  # seconds


class LLMClient:
    """
    LLM client for text generation using various model providers.
    """

    def __init__(self, model_cache_dir: str = MODEL_CACHE_DIR):
        """
        Initialize the LLM client.

        Args:
            model_cache_dir: Directory to cache models
        """
        self.model_cache_dir = model_cache_dir
        self.default_model = DEFAULT_MODEL

        # Model and tokenizer cache
        self.models = {}
        self.tokenizers = {}

        # Check if transformers is available
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("Transformers not available. Using mock responses.")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        expect_json: bool = False,
        json_schema: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate text using the LLM.

        Args:
            prompt: The prompt to send to the model
            system_prompt: Optional system prompt
            model: Model to use (defaults to self.default_model)
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            expect_json: Whether to expect JSON output
            json_schema: JSON schema for structured output

        Returns:
            Generated text
        """
        # Try to use Ollama if enabled
        if USE_OLLAMA:
            try:
                from .ollama_client import get_ollama_client

                ollama_client = get_ollama_client(OLLAMA_BASE_URL)

                # Check if Ollama is available
                if ollama_client.available:
                    logger.info(f"Using Ollama for prompt: {prompt[:50]}...")

                    # Use the specified model or default
                    model_name = model or self.default_model

                    # Convert HF model names to Ollama format if needed
                    if "/" in model_name:
                        # Extract the model name without the organization
                        # e.g., google/gemma-2b -> gemma-2b
                        model_name = model_name.split("/")[-1]

                        # Convert to Ollama format if needed
                        # e.g., gemma-2b -> gemma:2b
                        if "-" in model_name and not ":" in model_name:
                            parts = model_name.split("-")
                            if len(parts) > 1 and parts[-1].lower() in [
                                "2b",
                                "7b",
                                "13b",
                                "70b",
                            ]:
                                model_name = f"{parts[0]}:{parts[-1]}"

                    # Generate text using Ollama
                    return ollama_client.generate(
                        prompt=prompt,
                        model=model_name,
                        system_prompt=system_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
            except Exception as e:
                logger.error(f"Error using Ollama: {e}")
                # Fall back to other methods

        # If transformers is available and we're using HF models, use transformers
        if TRANSFORMERS_AVAILABLE and USE_HF_MODELS:
            # Use the specified model or default
            model_name = model or self.default_model

            try:
                # Create the full prompt with system prompt if provided
                full_prompt = ""
                if system_prompt:
                    # Add JSON schema to system prompt if needed
                    if expect_json and json_schema:
                        schema_str = json.dumps(json_schema, indent=2)
                        system_prompt += f"\n\nYou MUST respond with a valid JSON object that conforms to this schema:\n{schema_str}\n\nDo not include any text outside of the JSON object."

                    # Format the prompt based on model type
                    if "gemma" in model_name.lower():
                        full_prompt = f"<start_of_turn>system\n{system_prompt}<end_of_turn>\n<start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model\n"
                    elif "qwen" in model_name.lower():
                        full_prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
                    elif "llama" in model_name.lower():
                        full_prompt = f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{prompt} [/INST]"
                    elif "mistral" in model_name.lower():
                        full_prompt = f"<s>[INST] {system_prompt}\n\n{prompt} [/INST]"
                    else:
                        # Generic format for other models
                        full_prompt = (
                            f"System: {system_prompt}\n\nUser: {prompt}\n\nAssistant: "
                        )
                else:
                    # No system prompt, just user prompt
                    if "gemma" in model_name.lower():
                        full_prompt = f"<start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model\n"
                    elif "qwen" in model_name.lower():
                        full_prompt = (
                            f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
                        )
                    elif "llama" in model_name.lower():
                        full_prompt = f"<s>[INST] {prompt} [/INST]"
                    elif "mistral" in model_name.lower():
                        full_prompt = f"<s>[INST] {prompt} [/INST]"
                    else:
                        full_prompt = f"User: {prompt}\n\nAssistant: "

                # Load or get the model and tokenizer
                model_obj, tokenizer = self._get_model_and_tokenizer(model_name)

                # Generate text
                inputs = tokenizer(full_prompt, return_tensors="pt")

                # Move inputs to GPU if available
                if CUDA_AVAILABLE:
                    inputs = {k: v.cuda() for k, v in inputs.items()}
                    # Only move model to GPU if not using device_map="auto"
                    if not hasattr(model_obj, "hf_device_map"):
                        model_obj = model_obj.cuda()

                # Generate with the model, using Flash Attention if available
                try:
                    if CUDA_AVAILABLE and torch.__version__ >= "2.0.0":
                        logger.info("Using Flash Attention for generation")
                        # Modern PyTorch versions use a different API for Flash Attention
                        if hasattr(torch.nn.functional, "scaled_dot_product_attention"):
                            # Flash Attention is automatically used when appropriate with FP16
                            logger.info(
                                "Using modern Flash Attention via scaled_dot_product_attention"
                            )
                            with torch.no_grad():
                                # Add a timeout to prevent hanging
                                with timeout(30):  # 30 second timeout
                                    outputs = model_obj.generate(
                                        **inputs,
                                        max_new_tokens=max_tokens,
                                        temperature=temperature,
                                        top_p=0.95,
                                        do_sample=temperature > 0.0,
                                    )
                        else:
                            # Older PyTorch versions use the sdp_kernel context manager
                            logger.info("Using legacy Flash Attention via sdp_kernel")
                            with torch.no_grad():
                                # Add a timeout to prevent hanging
                                with timeout(30):  # 30 second timeout
                                    with torch.backends.cuda.sdp_kernel(
                                        enable_flash=True,
                                        enable_math=False,
                                        enable_mem_efficient=False,
                                    ):
                                        outputs = model_obj.generate(
                                            **inputs,
                                            max_new_tokens=max_tokens,
                                            temperature=temperature,
                                            top_p=0.95,
                                            do_sample=temperature > 0.0,
                                        )
                    else:
                        # Standard generation without Flash Attention
                        with torch.no_grad():
                            # Add a timeout to prevent hanging
                            with timeout(30):  # 30 second timeout
                                outputs = model_obj.generate(
                                    **inputs,
                                    max_new_tokens=max_tokens,
                                    temperature=temperature,
                                    top_p=0.95,
                                    do_sample=temperature > 0.0,
                                )
                except Exception as e:
                    logger.warning(
                        f"Error using Flash Attention: {e}. Falling back to standard generation."
                    )
                    # Fallback to standard generation
                    with torch.no_grad():
                        # Add a timeout to prevent hanging
                        with timeout(30):  # 30 second timeout
                            outputs = model_obj.generate(
                                **inputs,
                                max_new_tokens=max_tokens,
                                temperature=temperature,
                                top_p=0.95,
                                do_sample=temperature > 0.0,
                            )

                # Decode the output
                generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

                # Extract just the assistant's response
                if "gemma" in model_name.lower():
                    # For Gemma models
                    response_text = generated_text.split("<start_of_turn>model\n", 1)[
                        -1
                    ].split("<end_of_turn>", 1)[0]
                elif "qwen" in model_name.lower():
                    # For Qwen models
                    response_text = generated_text.split("<|im_start|>assistant\n", 1)[
                        -1
                    ].split("<|im_end|", 1)[0]
                elif "llama" in model_name.lower() or "mistral" in model_name.lower():
                    # For LLaMA and Mistral models
                    response_text = generated_text.split("[/INST]", 1)[-1].strip()
                else:
                    # Generic extraction
                    response_text = generated_text.split("Assistant: ", 1)[-1]

                # For JSON output, try to parse and validate
                if expect_json:
                    # Extract JSON from the response if needed
                    response_text = self._extract_json(response_text)

                    # Clean up the content to handle common formatting issues
                    response_text = self._clean_json_content(response_text)

                    # Validate against schema (basic validation)
                    try:
                        json_content = json.loads(response_text)
                        # In a real implementation, validate against the schema
                        return json.dumps(json_content)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse JSON from response: {response_text}")
                        return response_text

                return response_text

            except Exception as e:
                logger.error(f"Error generating text: {e}")
                return f"Error: {str(e)}"
        else:
            # Fall back to mock responses
            logger.info(f"Using mock response for prompt: {prompt[:50]}...")
            return self._mock_generate(prompt, system_prompt, expect_json)

    def generate_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        expect_json: bool = False,
        json_schema: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate text using the LLM with a chat format.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model to use (defaults to self.default_model)
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            expect_json: Whether to expect JSON output
            json_schema: JSON schema for structured output

        Returns:
            Generated text
        """
        # Extract system prompt if present
        system_prompt = None
        user_messages = []
        
        for message in messages:
            if message["role"] == "system":
                system_prompt = message["content"]
            elif message["role"] == "user":
                user_messages.append(message["content"])
        
        # Combine user messages into a single prompt
        prompt = "\n".join(user_messages) if user_messages else ""
        
        # Generate response
        return self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            expect_json=expect_json,
            json_schema=json_schema,
        )

    def _get_model_and_tokenizer(self, model_name):
        """
        Get or load the model and tokenizer with optimizations.

        Args:
            model_name: Name of the model to load

        Returns:
            Tuple of (model, tokenizer)
        """
        # Fix model name if it doesn't have the organization prefix
        if model_name == "gemma-2b" and not model_name.startswith("google/"):
            model_name = "google/gemma-2b"
        elif model_name == "gemma-7b" and not model_name.startswith("google/"):
            model_name = "google/gemma-7b"
        elif model_name == "llama-3-8b" and not model_name.startswith("meta-llama/"):
            model_name = "meta-llama/Llama-3-8B-Instruct"
        elif model_name == "mistral-7b" and not model_name.startswith("mistralai/"):
            model_name = "mistralai/Mistral-7B-Instruct-v0.2"

        # Check if model is already loaded
        if model_name in self.models and model_name in self.tokenizers:
            return self.models[model_name], self.tokenizers[model_name]

        logger.info(f"Loading model: {model_name}")

        try:
            # Prepare kwargs for loading models
            kwargs = {
                "cache_dir": self.model_cache_dir,
                "trust_remote_code": True,
            }

            # Add token if available
            if HF_TOKEN:
                kwargs["token"] = HF_TOKEN

            # Load the tokenizer
            logger.info(f"Loading tokenizer for {model_name}...")
            tokenizer = AutoTokenizer.from_pretrained(model_name, **kwargs)

            # Add model-specific kwargs
            model_kwargs = kwargs.copy()
            if CUDA_AVAILABLE:
                # Always use float16 for GPU to enable Flash Attention
                model_kwargs["torch_dtype"] = torch.float16
                model_kwargs["device_map"] = "auto"
                model_kwargs["low_cpu_mem_usage"] = True
                # Explicitly enable Flash Attention if available
                if hasattr(torch.backends, "cuda") and hasattr(
                    torch.backends.cuda, "enable_flash_sdp"
                ):
                    torch.backends.cuda.enable_flash_sdp(True)
                    logger.info("Enabled Flash Attention at model loading time")
            else:
                model_kwargs["torch_dtype"] = torch.float32

            # Configure quantization if enabled
            if USE_QUANTIZATION in ["4bit", "8bit"] and CUDA_AVAILABLE:
                try:
                    from transformers import BitsAndBytesConfig

                    if USE_QUANTIZATION == "4bit":
                        logger.info("Using 4-bit quantization with bitsandbytes")
                        model_kwargs["quantization_config"] = BitsAndBytesConfig(
                            load_in_4bit=True,
                            bnb_4bit_compute_dtype=torch.float16,
                            bnb_4bit_use_double_quant=True,
                            bnb_4bit_quant_type="nf4",
                        )
                    elif USE_QUANTIZATION == "8bit":
                        logger.info("Using 8-bit quantization with bitsandbytes")
                        model_kwargs["quantization_config"] = BitsAndBytesConfig(
                            load_in_8bit=True
                        )
                except ImportError:
                    logger.warning(
                        "BitsAndBytesConfig not available. Disabling quantization."
                    )

            # Load the model
            logger.info(f"Loading model {model_name}...")
            model = AutoModelForCausalLM.from_pretrained(model_name, **model_kwargs)

            # Apply BetterTransformer for optimized inference if requested
            if USE_BETTER_TRANSFORMER and CUDA_AVAILABLE:
                try:
                    logger.info(
                        "Converting model to BetterTransformer for optimized inference..."
                    )
                    model = model.to_bettertransformer()
                    logger.info("Model converted to BetterTransformer successfully!")
                except Exception as e:
                    logger.warning(f"Failed to convert model to BetterTransformer: {e}")

            # Cache the model and tokenizer
            self.models[model_name] = model
            self.tokenizers[model_name] = tokenizer

            logger.info(f"Successfully loaded model and tokenizer for {model_name}")
            return model, tokenizer
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
            # Fall back to mock responses
            raise

    def _mock_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        expect_json: bool = False,
    ) -> str:
        """
        Generate a mock response for testing.

        Args:
            prompt: The prompt
            system_prompt: Optional system prompt
            expect_json: Whether to expect JSON output

        Returns:
            Mock response
        """
        logger.info(f"Generating mock response for: {prompt}")
        # Use system prompt in the response if provided
        system_context = ""
        if system_prompt:
            system_context = f"Based on the instruction: '{system_prompt}', "

        # Simple keyword-based responses
        if "hello" in prompt.lower() or "hi" in prompt.lower():
            if expect_json:
                return json.dumps(
                    {
                        "greeting": "Hello!",
                        "message": "I'm a mock LLM response. How can I help you today?",
                    }
                )
            else:
                return f"{system_context}Hello! I'm a mock LLM response. How can I help you today?"

        elif "test" in prompt.lower() or "example" in prompt.lower():
            if expect_json:
                return json.dumps(
                    {
                        "status": "success",
                        "message": "This is a test response from the mock LLM client.",
                        "details": {
                            "prompt": prompt[:50] + "..." if len(prompt) > 50 else prompt,
                            "system_prompt": system_prompt[:50] + "..." if system_prompt and len(system_prompt) > 50 else system_prompt,
                        }
                    }
                )
            else:
                return f"{system_context}This is a test response from the mock LLM client. Your prompt was: '{prompt[:50]}...'"

        else:
            if expect_json:
                return json.dumps(
                    {
                        "response": "I'm a mock LLM client response.",
                        "prompt_length": len(prompt),
                        "has_system_prompt": system_prompt is not None,
                    }
                )
            else:
                return f"{system_context}I'm a mock LLM client response. In a real scenario, I would generate a meaningful response to your prompt."

    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from text that might contain other content.

        Args:
            text: Text that might contain JSON

        Returns:
            json_str: Extracted JSON string
        """
        # Remove markdown code blocks if present
        import re

        # Check for markdown code blocks
        code_block_match = re.search(
            r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.DOTALL
        )
        if code_block_match:
            text = code_block_match.group(1).strip()

        # Look for JSON object between curly braces
        json_match = re.search(r"(\{.*\})", text, re.DOTALL)
        if json_match:
            return json_match.group(1)

        # If no JSON object found, return the original text
        return text

    def _clean_json_content(self, text: str) -> str:
        """
        Clean up JSON content to handle common formatting issues.

        Args:
            text: JSON content to clean

        Returns:
            cleaned_text: Cleaned JSON content
        """
        import re

        # Replace human-readable number formats with numeric values
        # Example: "67 million" -> "67000000"
        text = re.sub(r"(\d+)\s*million", r"\1000000", text)
        text = re.sub(r"(\d+)\s*millions", r"\1000000", text)
        text = re.sub(r"(\d+)\s*billion", r"\1000000000", text)
        text = re.sub(r"(\d+)\s*trillion", r"\1000000000000", text)

        # Replace comma-separated numbers
        # Example: "4,830,640" -> "4830640"
        text = re.sub(r"(\d),(?=\d)", r"\1", text)

        return text


# Singleton instance
_LLM_CLIENT = None


def get_llm_client(
    model_cache_dir: str = MODEL_CACHE_DIR, timeout_seconds: int = 30
) -> LLMClient:
    """
    Get the singleton instance of the LLMClient.

    Args:
        model_cache_dir: Directory to cache models
        timeout_seconds: Maximum time to wait for model loading (default: 30 seconds)

    Returns:
        LLMClient instance

    Raises:
        TimeoutException: If model loading takes longer than timeout_seconds
    """
    global _LLM_CLIENT
    if _LLM_CLIENT is None:
        try:
            with timeout(timeout_seconds):
                _LLM_CLIENT = LLMClient(model_cache_dir)
        except TimeoutException as e:
            logger.warning(f"LLM client initialization timed out: {e}")
            raise
    return _LLM_CLIENT
