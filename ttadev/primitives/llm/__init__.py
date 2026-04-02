"""LLM primitives — runtime LLM provider abstraction and routing."""

from ttadev.primitives.llm.eval_harness import (
    COST_PER_1K_OUTPUT_TOKENS,
    TASK_TYPE_PROFILES,
    EvalHarnessPrimitive,
    EvalRun,
    EvalTask,
    ModelEvalResult,
)
from ttadev.primitives.llm.free_model_tracker import (
    FreeModelTracker,
    ORModel,
    fetch_free_models,
    get_free_models,
    rank_models_for_role,
)
from ttadev.primitives.llm.model_monitor import (
    ModelMonitorPrimitive,
    ModelStats,
    MonitorRequest,
    MonitorResponse,
)
from ttadev.primitives.llm.model_registry import (
    ModelEntry,
    ModelRegistryPrimitive,
    RegistryRequest,
    RegistryResponse,
    SelectionPolicy,
)
from ttadev.primitives.llm.model_router import (
    ModelRouterPrimitive,
    ModelRouterRequest,
    RouterModeConfig,
    RouterTierConfig,
)
from ttadev.primitives.llm.ollama_primitive import (
    OllamaEmbeddingsPrimitive,
    OllamaEmbeddingsRequest,
    OllamaEmbeddingsResponse,
    OllamaManagerRequest,
    OllamaManagerResponse,
    OllamaModelInfo,
    OllamaModelManagerPrimitive,
    OllamaPrimitive,
    OllamaRequest,
    OllamaResponse,
    RunningModel,
)
from ttadev.primitives.llm.providers import (
    PROVIDERS,
    ProviderSpec,
    get_provider,
    openai_compat_providers,
)
from ttadev.primitives.llm.universal_llm_primitive import (
    LLMProvider,
    LLMRequest,
    LLMResponse,
    UniversalLLMPrimitive,
)

__all__ = [
    # eval harness
    "EvalTask",
    "ModelEvalResult",
    "EvalRun",
    "EvalHarnessPrimitive",
    "TASK_TYPE_PROFILES",
    "COST_PER_1K_OUTPUT_TOKENS",
    # universal primitive
    "LLMProvider",
    "LLMRequest",
    "LLMResponse",
    "UniversalLLMPrimitive",
    # free model tracker
    "FreeModelTracker",
    "ORModel",
    "fetch_free_models",
    "get_free_models",
    "rank_models_for_role",
    # model monitor
    "ModelMonitorPrimitive",
    "ModelStats",
    "MonitorRequest",
    "MonitorResponse",
    # model registry
    "ModelEntry",
    "ModelRegistryPrimitive",
    "RegistryRequest",
    "RegistryResponse",
    "SelectionPolicy",
    # model router
    "ModelRouterPrimitive",
    "ModelRouterRequest",
    "RouterModeConfig",
    "RouterTierConfig",
    # provider registry
    "PROVIDERS",
    "ProviderSpec",
    "get_provider",
    "openai_compat_providers",
    # Ollama dedicated primitives
    "OllamaPrimitive",
    "OllamaRequest",
    "OllamaResponse",
    "OllamaModelManagerPrimitive",
    "OllamaManagerRequest",
    "OllamaManagerResponse",
    "OllamaModelInfo",
    "OllamaEmbeddingsPrimitive",
    "OllamaEmbeddingsRequest",
    "OllamaEmbeddingsResponse",
    "RunningModel",
]
