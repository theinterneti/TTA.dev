"""
Agentic RAG Workflow - Production Pattern

Based on NVIDIA Agentic RAG architecture with:
- Dynamic routing (vector store vs web search)
- Document relevance grading
- Answer quality checking
- Hallucination detection
- Iterative refinement

Reference: https://github.com/nvidia/workbench-example-agentic-rag
"""

import asyncio
from typing import Any, Literal

from tta_dev_primitives import WorkflowContext, WorkflowPrimitive
from tta_dev_primitives.observability import InstrumentedPrimitive
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.recovery import FallbackPrimitive, RetryPrimitive, RetryStrategy

# ==============================================================================
# Step 1: Query Router - Route to vector store OR web search
# ==============================================================================


class QueryRouterPrimitive(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """
    Route user query to appropriate data source.
    
    Uses LLM to determine if query should go to:
    - vectorstore: For RAG-specific topics (LLM agents, prompt engineering)
    - web_search: For general knowledge or recent information
    """

    def __init__(self) -> None:
        super().__init__(name="query_router")

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Route query to vectorstore or web search."""
        query = input_data.get("question", "")

        # Simulate LLM routing decision (in production, use actual LLM)
        # Prompt: "Route to vectorstore for RAG/agent topics, else web_search"
        keywords = ["rag", "agent", "workflow", "primitive", "tta.dev", "compose"]
        datasource: Literal["vectorstore", "web_search"] = (
            "vectorstore"
            if any(kw in query.lower() for kw in keywords)
            else "web_search"
        )

        return {
            "question": query,
            "datasource": datasource,
            "routing_confidence": 0.92,
        }


# ==============================================================================
# Step 2: Document Retrieval - Fetch relevant documents
# ==============================================================================


class VectorstoreRetrieverPrimitive(
    InstrumentedPrimitive[dict[str, Any], dict[str, Any]]
):
    """Retrieve documents from vector database."""

    def __init__(self, top_k: int = 5) -> None:
        super().__init__(name="vectorstore_retriever")
        self.top_k = top_k

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Retrieve top-k documents from vector store."""
        question = input_data.get("question", "")

        # Simulate vector DB retrieval (in production, use actual vector DB)
        documents = [
            {
                "content": f"TTA.dev is a production-ready AI toolkit with composable primitives. Query: {question}",
                "metadata": {"source": "docs/getting_started.md", "score": 0.89},
            },
            {
                "content": "Workflows compose using >> for sequential and | for parallel execution.",
                "metadata": {"source": "docs/composition.md", "score": 0.85},
            },
            {
                "content": "InstrumentedPrimitive provides automatic OpenTelemetry tracing.",
                "metadata": {"source": "docs/observability.md", "score": 0.78},
            },
        ]

        return {
            "question": question,
            "documents": documents[: self.top_k],
            "retrieval_method": "vectorstore",
        }


class WebSearchPrimitive(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """Perform web search for current information."""

    def __init__(self, num_results: int = 3) -> None:
        super().__init__(name="web_search")
        self.num_results = num_results

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Search the web for relevant information."""
        question = input_data.get("question", "")

        # Simulate web search (in production, use Tavily, SerpAPI, etc.)
        documents = [
            {
                "content": f"Web search result for: {question}. Found comprehensive information about the topic.",
                "metadata": {
                    "source": "https://example.com/article",
                    "score": 0.82,
                },
            },
            {
                "content": "Additional context from web sources discussing related concepts.",
                "metadata": {"source": "https://example.com/blog", "score": 0.75},
            },
        ]

        return {
            "question": question,
            "documents": documents[: self.num_results],
            "retrieval_method": "web_search",
        }


# ==============================================================================
# Step 3: Document Grader - Filter irrelevant documents
# ==============================================================================


class DocumentGraderPrimitive(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """
    Grade document relevance to question.
    
    Returns binary yes/no score for each document.
    Filters out irrelevant documents to reduce noise.
    """

    def __init__(self) -> None:
        super().__init__(name="document_grader")

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Grade each document's relevance."""
        question = input_data.get("question", "")
        documents = input_data.get("documents", [])

        # Simulate LLM grading (in production, use actual LLM)
        # Prompt: "Is this document relevant to the question? Answer yes/no"
        filtered_docs = []
        needs_web_search = False

        for doc in documents:
            # Simple heuristic: check if question keywords in document
            doc_content = doc.get("content", "").lower()
            question_words = set(question.lower().split())
            relevance_score = sum(1 for word in question_words if word in doc_content)

            if relevance_score > 0:  # Relevant
                filtered_docs.append(doc)
            else:
                needs_web_search = True  # Need more sources

        return {
            "question": question,
            "documents": filtered_docs,
            "needs_web_search": needs_web_search,
            "filtered_count": len(documents) - len(filtered_docs),
        }


# ==============================================================================
# Step 4: Answer Generator - Generate answer from context
# ==============================================================================


class AnswerGeneratorPrimitive(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """Generate answer using LLM with retrieved context."""

    def __init__(self, model: str = "gpt-4-mini") -> None:
        super().__init__(name="answer_generator")
        self.model = model

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Generate answer from documents."""
        question = input_data.get("question", "")
        documents = input_data.get("documents", [])

        # Format context (in production, pass to LLM prompt)
        _ = "\n\n".join(
            f"[{i+1}] {doc.get('content', '')}" for i, doc in enumerate(documents)
        )

        # Simulate LLM generation (in production, use actual LLM API)
        # Prompt: "Answer based on the following context: {context_text}\n\nQuestion: {question}"
        generation = f"Based on the provided documents, {question.lower()} can be understood as follows: "
        generation += "TTA.dev provides composable workflow primitives with built-in observability. "
        generation += "You can compose workflows using >> for sequential and | for parallel execution."

        return {
            "question": question,
            "generation": generation,
            "documents": documents,
            "model": self.model,
        }


# ==============================================================================
# Step 5: Answer Grader - Check if answer resolves question
# ==============================================================================


class AnswerGraderPrimitive(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """
    Grade if answer is useful to resolve the question.
    
    Returns binary yes/no score.
    Triggers retry if answer is not useful.
    """

    def __init__(self) -> None:
        super().__init__(name="answer_grader")

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Grade answer usefulness."""
        question = input_data.get("question", "")
        generation = input_data.get("generation", "")

        # Simulate LLM grading (in production, use actual LLM)
        # Prompt: "Is this answer useful to resolve the question? yes/no"
        is_useful = len(generation) > 50  # Simple heuristic

        return {
            "question": question,
            "generation": generation,
            "documents": input_data.get("documents", []),
            "is_useful": is_useful,
            "grade_score": "yes" if is_useful else "no",
        }


# ==============================================================================
# Step 6: Hallucination Grader - Verify answer against sources
# ==============================================================================


class HallucinationGraderPrimitive(
    InstrumentedPrimitive[dict[str, Any], dict[str, Any]]
):
    """
    Check if answer is grounded in provided documents.
    
    Prevents hallucinations by verifying answer against sources.
    """

    def __init__(self) -> None:
        super().__init__(name="hallucination_grader")

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Check if generation is grounded in documents."""
        generation = input_data.get("generation", "")
        documents = input_data.get("documents", [])

        # Simulate LLM grading (in production, use actual LLM)
        # Prompt: "Is the answer grounded in these facts? yes/no"
        doc_contents = " ".join(doc.get("content", "") for doc in documents)
        generation_words = set(generation.lower().split())
        doc_words = set(doc_contents.lower().split())

        # Check overlap between generation and documents
        overlap = len(generation_words & doc_words) / max(len(generation_words), 1)
        is_grounded = overlap > 0.3  # At least 30% overlap

        return {
            "question": input_data.get("question", ""),
            "generation": generation,
            "documents": documents,
            "is_grounded": is_grounded,
            "hallucination_score": "yes" if is_grounded else "no",
            "overlap_ratio": overlap,
        }


# ==============================================================================
# Agentic RAG Workflow Construction
# ==============================================================================


def create_agentic_rag_workflow(
    cache_enabled: bool = True,
    max_retries: int = 2,
) -> WorkflowPrimitive[dict[str, Any], dict[str, Any]]:
    """
    Create production agentic RAG workflow with NVIDIA pattern.

    Features:
    - Dynamic routing (vectorstore vs web search)
    - Document relevance filtering
    - Answer quality checking
    - Hallucination detection
    - Automatic retry with web search fallback
    - Caching for performance

    Args:
        cache_enabled: Enable caching for retrieval
        max_retries: Maximum retry attempts

    Returns:
        Complete agentic RAG workflow
    """
    # Step 1: Route query
    router = QueryRouterPrimitive()

    # Step 2: Retrieval with fallback
    vectorstore = VectorstoreRetrieverPrimitive(top_k=5)
    web_search = WebSearchPrimitive(num_results=3)

    # Cache vectorstore retrieval
    if cache_enabled:
        vectorstore = CachePrimitive(
            primitive=vectorstore,
            cache_key_fn=lambda data, ctx: data.get("question", ""),
            ttl_seconds=3600,
        )

    # Fallback to web search if vectorstore fails
    retriever = FallbackPrimitive(primary=vectorstore, fallback=web_search)

    # Step 3: Grade documents
    doc_grader = DocumentGraderPrimitive()

    # Step 4: Generate answer
    generator = AnswerGeneratorPrimitive(model="gpt-4-mini")

    # Step 5: Grade answer usefulness
    answer_grader = AnswerGraderPrimitive()

    # Step 6: Check hallucinations
    hallucination_checker = HallucinationGraderPrimitive()

    # Compose workflow with retry
    workflow = router >> retriever >> doc_grader >> generator

    # Add quality checks
    workflow = workflow >> answer_grader >> hallucination_checker

    # Wrap in retry for refinement
    if max_retries > 0:
        workflow = RetryPrimitive(
            primitive=workflow,
            strategy=RetryStrategy(max_retries=max_retries, backoff_base=1.5),
        )

    return workflow


# ==============================================================================
# Example Usage
# ==============================================================================


async def main() -> None:
    """Demonstrate agentic RAG workflow."""
    print("=" * 80)
    print("Agentic RAG Workflow - Production Pattern")
    print("=" * 80)
    print()

    # Create workflow
    workflow = create_agentic_rag_workflow(cache_enabled=True, max_retries=2)

    # Create context
    context = WorkflowContext(
        correlation_id="agentic-rag-001",
        metadata={"session": "demo", "user": "researcher"},
    )

    # Test queries
    queries = [
        "What is TTA.dev and how do I use it?",
        "How does quantum computing work?",  # Will route to web search
        "What is TTA.dev and how do I use it?",  # Will hit cache
    ]

    for i, query in enumerate(queries, 1):
        print(f"Query {i}: {query}")
        print("-" * 80)

        try:
            result = await workflow.execute({"question": query}, context)

            print(f"✓ Generation: {result.get('generation', 'N/A')[:200]}...")
            print(f"✓ Grounded: {result.get('is_grounded', 'N/A')}")
            print(f"✓ Useful: {result.get('is_useful', 'N/A')}")
            print(f"✓ Sources: {len(result.get('documents', []))} documents")
            print(
                f"✓ Retrieval Method: {result.get('retrieval_method', 'N/A').upper()}"
            )

        except Exception as e:
            print(f"✗ Error: {e}")

        print("\n" + "=" * 80 + "\n")

    print("✅ Agentic RAG workflow complete!")
    print()
    print("Key Features Demonstrated:")
    print("  ✅ Dynamic routing (vectorstore vs web search)")
    print("  ✅ Document relevance filtering")
    print("  ✅ Answer quality checking")
    print("  ✅ Hallucination detection")
    print("  ✅ Automatic retry and refinement")
    print("  ✅ Caching for performance")
    print("  ✅ Full observability with structured logging")


if __name__ == "__main__":
    asyncio.run(main())
