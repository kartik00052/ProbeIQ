"""Central LLM construction for ProbeIQ.

The interview engine depends on ``app.llm.factory.get_llm`` -- a single provider
abstraction -- never on a vendor-specific chat class. NVIDIA-hosted GLM 5.2 is
reached through its OpenAI-compatible Chat Completions endpoint using the
already-installed ``langchain-openai`` integration, so no NVIDIA-specific
package is required and the boundary stays clean.
"""

from app.llm.factory import NVIDIA_BASE_URL, SUPPORTED_PROVIDERS, get_llm

__all__ = ["NVIDIA_BASE_URL", "SUPPORTED_PROVIDERS", "get_llm"]
