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
from ttadev.primitives.llm.hardware_detector import (
    GPUInfo,
    HardwareDetector,
    HardwareProfile,
)
from ttadev.primitives.llm.hardware_detector import (
    detector as hardware_detector,
)
from ttadev.primitives.llm.litellm_primitive import (
    LiteLLMPrimitive,
    make_resilient_llm,
)
from ttadev.primitives.llm.model_advisor import (
    ModelAdvisor,
    ROIEstimate,
    TaskSuggestion,
    TierRecommendation,
    advisor,
)
from ttadev.primitives.llm.model_catalog import (
    PROVIDER_SUMMARY,
    print_catalog,
)
from ttadev.primitives.llm.model_monitor import (
    ModelMonitorPrimitive,
    ModelStats,
    MonitorRequest,
    MonitorResponse,
)
from ttadev.primitives.llm.model_pricing import (
    PROVIDER_PRICING,
    ModelPricing,
    get_effective_cost_tier,
    get_pricing,
)
from ttadev.primitives.llm.model_registry import (
    GEMINI_MODELS,
    GROQ_ROTATION_MODELS,
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
from ttadev.primitives.llm.smart_router import LiteLLMSmartAdapter, SmartRouterPrimitive
from ttadev.primitives.llm.task_selector import (
    COMPLEXITY_COMPLEX,
    COMPLEXITY_MODERATE,
    COMPLEXITY_SIMPLE,
    TASK_CHAT,
    TASK_CODING,
    TASK_FUNCTION_CALLING,
    TASK_GENERAL,
    TASK_MATH,
    TASK_REASONING,
    TASK_VISION,
    TaskProfile,
    meets_complexity_threshold,
    min_ollama_params_for_complexity,
    rank_models_for_task,
    score_model_for_task,
)
from ttadev.primitives.llm.universal_llm_primitive import (
    LLMProvider,
    LLMRequest,
    LLMResponse,
    ToolCall,
    ToolSchema,
    UniversalLLMPrimitive,
)

__all__ = [
    # litellm primitive (primary LLM path)
    "LiteLLMPrimitive",
    "make_resilient_llm",
    # eval harness
    "EvalTask",
    "ModelEvalResult",
    "EvalRun",
    "EvalHarnessPrimitive",
    "TASK_TYPE_PROFILES",
    "COST_PER_1K_OUTPUT_TOKENS",
    # universal primitive (preserved as fallback)
    "LLMProvider",
    "LLMRequest",
    "LLMResponse",
    "ToolCall",
    "ToolSchema",
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
    "GROQ_ROTATION_MODELS",
    "GEMINI_MODELS",
    # model catalog
    "PROVIDER_SUMMARY",
    "print_catalog",
    # model pricing
    "ModelPricing",
    "PROVIDER_PRICING",
    "get_pricing",
    "get_effective_cost_tier",
    # model router
    "ModelRouterPrimitive",
    "ModelRouterRequest",
    "RouterModeConfig",
    "RouterTierConfig",
    # smart router (zero-config cascade)
    "LiteLLMSmartAdapter",
    "SmartRouterPrimitive",
    # task-aware selection
    "TaskProfile",
    "TASK_CODING",
    "TASK_REASONING",
    "TASK_MATH",
    "TASK_CHAT",
    "TASK_FUNCTION_CALLING",
    "TASK_VISION",
    "TASK_GENERAL",
    "COMPLEXITY_SIMPLE",
    "COMPLEXITY_MODERATE",
    "COMPLEXITY_COMPLEX",
    "score_model_for_task",
    "meets_complexity_threshold",
    "rank_models_for_task",
    "min_ollama_params_for_complexity",
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
    # hardware detection
    "HardwareDetector",
    "HardwareProfile",
    "GPUInfo",
    "hardware_detector",
    # model advisor
    "ModelAdvisor",
    "TierRecommendation",
    "ROIEstimate",
    "TaskSuggestion",
    "advisor",
]
