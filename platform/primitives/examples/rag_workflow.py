"""
RAG (Retrieval-Augmented Generation) Workflow Example

This example demonstrates building a production-ready RAG workflow using TTA.dev primitives.

Features:
- Vector database integration (simulated)
- Context retrieval with relevance scoring
- LLM augmentation with retrieved context
- Cost optimization through caching
- Error handling with fallbacks
- Performance metrics tracking

Dependencies:
    uv add tta-dev-primitives

Usage:
    python examples/rag_workflow.py
"""

import asyncio
from typing import Any

from tta_dev_primitives import WorkflowContext, WorkflowPrimitive
from tta_dev_primitives.observability import InstrumentedPrimitive
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.recovery import FallbackPrimitive, RetryPrimitive, RetryStrategy

# ==============================================================================
# Step 1: Query Processing
# ==============================================================================


class QueryProcessorPrimitive(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """Process and normalize user query."""

    def __init__(self) -> None:
        super().__init__(name="query_processor")

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Extract and normalize query from input."""
        query = input_data.get("query", "")

        # Normalize query
        normalized = query.strip().lower()

        # Extract query type
        query_type = "general"
        if any(word in normalized for word in ["how", "what", "why"]):
            query_type = "factual"
        elif any(word in normalized for word in ["show", "example", "demo"]):
            query_type = "example"

        return {
            "original_query": query,
            "normalized_query": normalized,
            "query_type": query_type,
            "timestamp": context.metadata.get("timestamp", "unknown"),
        }


# ==============================================================================
# Step 2: Vector Retrieval
# ==============================================================================


class VectorRetrievalPrimitive(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """Retrieve relevant documents from vector database."""

    def __init__(self, top_k: int = 5, similarity_threshold: float = 0.7) -> None:
        """
        Initialize retrieval primitive.

        Args:
            top_k: Number of documents to retrieve
            similarity_threshold: Minimum similarity score (0-1)
        """
        super().__init__(name="vector_retrieval")
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Retrieve documents from vector DB (simulated)."""
        query = input_data["normalized_query"]

        # Simulate vector DB query (in production, use Pinecone, Weaviate, etc.)
        await asyncio.sleep(0.1)  # Simulate network latency

        # Simulated results
        documents = [
            {
                "content": f"Document about {query}: TTA.dev provides composable workflow primitives.",
                "score": 0.95,
                "metadata": {"source": "docs/primitives.md"},
            },
            {
                "content": f"Related to {query}: Use >> operator for sequential composition.",
                "score": 0.88,
                "metadata": {"source": "docs/patterns.md"},
            },
            {
                "content": f"Context for {query}: WorkflowContext carries correlation IDs.",
                "score": 0.82,
                "metadata": {"source": "docs/context.md"},
            },
            {
                "content": f"Additional info on {query}: All primitives have built-in observability.",
                "score": 0.75,
                "metadata": {"source": "docs/observability.md"},
            },
            {
                "content": f"Background on {query}: Recovery primitives handle failures gracefully.",
                "score": 0.68,
                "metadata": {"source": "docs/recovery.md"},
            },
        ]

        # Filter by threshold and limit to top_k
        relevant_docs = [doc for doc in documents if doc["score"] >= self.similarity_threshold][
            : self.top_k
        ]

        return {
            **input_data,
            "retrieved_documents": relevant_docs,
            "num_retrieved": len(relevant_docs),
        }


# ==============================================================================
# Step 3: Context Augmentation
# ==============================================================================


class ContextAugmentationPrimitive(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """Augment user query with retrieved context."""

    def __init__(self, max_context_length: int = 2000) -> None:
        """
        Initialize context augmentation primitive.

        Args:
            max_context_length: Maximum length of context to include
        """
        super().__init__(name="context_augmentation")
        self.max_context_length = max_context_length

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Build augmented prompt with retrieved context."""
        query = input_data["original_query"]
        documents = input_data["retrieved_documents"]

        # Build context from documents
        context_parts = []
        total_length = 0

        for i, doc in enumerate(documents, 1):
            doc_text = f"[{i}] {doc['content']} (relevance: {doc['score']:.2f})"
            if total_length + len(doc_text) > self.max_context_length:
                break
            context_parts.append(doc_text)
            total_length += len(doc_text)

        # Build augmented prompt
        augmented_prompt = f"""Answer the following question using the provided context.

Context:
{chr(10).join(context_parts)}

Question: {query}

Answer:"""

        return {
            **input_data,
            "augmented_prompt": augmented_prompt,
            "num_context_docs": len(context_parts),
            "context_length": total_length,
        }


# ==============================================================================
# Step 4: LLM Generation
# ==============================================================================


class LLMGenerationPrimitive(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """Generate answer using LLM."""

    def __init__(self, model: str = "gpt-4-mini", max_tokens: int = 500) -> None:
        """
        Initialize LLM generation primitive.

        Args:
            model: LLM model name
            max_tokens: Maximum tokens to generate
        """
        super().__init__(name="llm_generation")
        self.model = model
        self.max_tokens = max_tokens

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Generate answer using LLM with augmented context."""
        augmented_query = input_data.get("augmented_query", "")
        sources = input_data.get("sources", [])

        # Simulate LLM generation (in production, call actual LLM API)
        # Example: response = await openai_client.chat.completions.create(...)
        generated_answer = f"Based on the context, here's an answer to: {augmented_query}"

        return {
            "response": generated_answer,
            "model": self.model,
            "confidence": 0.85,
            "num_sources": len(sources),
            "sources": sources,
            "usage": {
                "prompt_tokens": 150,
                "completion_tokens": 50,
                "total_tokens": 200,
            },
        }


# ==============================================================================
# RAG Workflow Construction
# ==============================================================================


def create_rag_workflow(
    cache_enabled: bool = True,
    cache_ttl: int = 3600,
    retry_enabled: bool = True,
) -> WorkflowPrimitive[dict[str, Any], dict[str, Any]]:
    """
    Create production-ready RAG workflow.

    Args:
        cache_enabled: Enable caching for vector retrieval
        cache_ttl: Cache TTL in seconds
        retry_enabled: Enable retry on failures

    Returns:
        Complete RAG workflow primitive
    """
    # Step 1: Query processing
    query_processor = QueryProcessorPrimitive()

    # Step 2: Vector retrieval with caching
    vector_retrieval = VectorRetrievalPrimitive(top_k=5, similarity_threshold=0.7)

    if cache_enabled:
        # Cache retrieval results to reduce vector DB load
        vector_retrieval = CachePrimitive(
            primitive=vector_retrieval,
            cache_key_fn=lambda data, ctx: data["normalized_query"],
            ttl_seconds=cache_ttl,
        )

    # Step 3: Context augmentation
    context_augmentation = ContextAugmentationPrimitive(max_context_length=2000)

    # Step 4: LLM generation with fallback
    primary_llm = LLMGenerationPrimitive(model="gpt-4-mini", max_tokens=500)
    fallback_llm = LLMGenerationPrimitive(model="gpt-3.5-turbo", max_tokens=500)

    llm_with_fallback = FallbackPrimitive(
        primary=primary_llm,
        fallback=fallback_llm,
    )

    if retry_enabled:
        # Add retry for transient failures
        llm_with_fallback = RetryPrimitive(
            primitive=llm_with_fallback,
            strategy=RetryStrategy(max_retries=3, backoff_base=2.0),
        )

    # Compose complete workflow
    workflow = query_processor >> vector_retrieval >> context_augmentation >> llm_with_fallback

    return workflow


# ==============================================================================
# Example Usage
# ==============================================================================


async def main() -> None:
    """Demonstrate RAG workflow."""
    print("=" * 80)
    print("RAG (Retrieval-Augmented Generation) Workflow Example")
    print("=" * 80)
    print()

    # Create workflow
    workflow = create_rag_workflow(
        cache_enabled=True,
        cache_ttl=3600,  # 1 hour
        retry_enabled=True,
    )

    # Create context
    context = WorkflowContext(
        correlation_id="rag-demo-001",
        metadata={"timestamp": "2025-10-30T10:00:00Z"},
    )

    # Example queries
    queries = [
        "What is TTA.dev?",
        "How do I compose workflows?",
        "What is TTA.dev?",  # Duplicate to show caching
    ]

    for i, query in enumerate(queries, 1):
        print(f"Query {i}: {query}")
        print("-" * 80)

        # Execute workflow
        result = await workflow.execute({"query": query}, context)

        # Display results
        print(f"Model: {result['model']}")
        print(f"Sources Used: {result['num_sources']}")
        print(f"Token Usage: {result['usage']['total_tokens']} tokens")
        print(f"\nResponse:\n{result['response']}")
        print("\nSources:")
        for source in result["sources"]:
            print(f"  - {source}")
        print("\n" + "=" * 80 + "\n")

    print("✅ RAG workflow complete!")
    print()
    print("Key Features Demonstrated:")
    print("  ✅ Vector database retrieval")
    print("  ✅ Context augmentation")
    print("  ✅ LLM generation with fallback")
    print("  ✅ Caching for performance")
    print("  ✅ Retry for reliability")
    print("  ✅ Source attribution")


if __name__ == "__main__":
    asyncio.run(main())
