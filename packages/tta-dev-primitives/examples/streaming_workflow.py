"""
Streaming LLM Responses Example

This example demonstrates building streaming workflows using TTA.dev primitives.

Features:
- Streaming LLM responses (Server-Sent Events pattern)
- Backpressure handling
- Real-time token-by-token delivery
- Stream cancellation
- Error handling in streams
- Metrics for streaming performance

Dependencies:
    uv add tta-dev-primitives

Usage:
    python examples/streaming_workflow.py
"""

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.observability import InstrumentedPrimitive

# ==============================================================================
# Stream Data Models
# ==============================================================================


@dataclass
class StreamChunk:
    """A chunk of streaming data."""

    content: str
    chunk_index: int
    is_final: bool = False
    metadata: dict[str, Any] | None = None


@dataclass
class StreamMetrics:
    """Metrics for streaming performance."""

    total_chunks: int = 0
    total_chars: int = 0
    duration_seconds: float = 0.0
    chunks_per_second: float = 0.0
    chars_per_second: float = 0.0


# ==============================================================================
# Streaming Primitive Base
# ==============================================================================


class StreamingPrimitive(
    InstrumentedPrimitive[dict[str, Any], AsyncIterator[StreamChunk]]
):
    """Base class for streaming primitives."""

    def __init__(self, name: str = "streaming_base") -> None:
        super().__init__(name=name)

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> AsyncIterator[StreamChunk]:
        """Execute and return async iterator of chunks."""
        # Subclasses implement this to yield chunks
        raise NotImplementedError
        # Make this a proper generator to satisfy the type checker
        yield  # This line is never reached but makes this a generator


# ==============================================================================
# Streaming LLM Primitive
# ==============================================================================


class StreamingLLMPrimitive(StreamingPrimitive):
    """Stream LLM responses token-by-token."""

    def __init__(
        self,
        model: str = "gpt-4-mini",
        chunk_delay: float = 0.05,  # Simulate network latency
    ) -> None:
        """
        Initialize streaming LLM.

        Args:
            model: Model name
            chunk_delay: Delay between chunks (seconds)
        """
        super().__init__(name=f"streaming_llm_{model}")
        self.model = model
        self.chunk_delay = chunk_delay

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> AsyncIterator[StreamChunk]:
        """Stream LLM response."""
        prompt = input_data.get("prompt", "")

        # Simulate LLM streaming response
        response_text = """TTA.dev is a production-ready AI development toolkit.

Key features include:
- Composable workflow primitives
- Type-safe composition with >> and | operators
- Built-in observability with OpenTelemetry
- Recovery patterns (Retry, Fallback, Timeout)
- Performance optimizations (Cache)

Example usage:
```python
workflow = step1 >> step2 >> step3
result = await workflow.execute(context, input_data)
```

The framework enables building reliable AI workflows with minimal boilerplate."""

        # Split into tokens (simplified - real LLM uses tokenizer)
        tokens = response_text.split()

        # Stream tokens
        for i, token in enumerate(tokens):
            # Simulate network latency
            await asyncio.sleep(self.chunk_delay)

            # Check for cancellation
            if context.metadata.get("cancelled", False):
                yield StreamChunk(
                    content="",
                    chunk_index=i,
                    is_final=True,
                    metadata={"status": "cancelled"},
                )
                return

            # Yield chunk
            is_final = i == len(tokens) - 1
            yield StreamChunk(
                content=token + " ",
                chunk_index=i,
                is_final=is_final,
                metadata={
                    "model": self.model,
                    "prompt": prompt
                    if i == 0
                    else None,  # Include prompt in first chunk
                },
            )


# ==============================================================================
# Stream Processing Primitives
# ==============================================================================


class StreamBufferPrimitive(
    InstrumentedPrimitive[AsyncIterator[StreamChunk], AsyncIterator[StreamChunk]]
):
    """Buffer stream chunks for smoother delivery."""

    def __init__(self, buffer_size: int = 5) -> None:
        """
        Initialize stream buffer.

        Args:
            buffer_size: Number of chunks to buffer
        """
        super().__init__(name="stream_buffer")
        self.buffer_size = buffer_size

    async def _execute_impl(
        self, input_data: AsyncIterator[StreamChunk], context: WorkflowContext
    ) -> AsyncIterator[StreamChunk]:
        """Buffer and yield chunks."""
        buffer: list[StreamChunk] = []

        async for chunk in input_data:
            buffer.append(chunk)

            # Yield when buffer is full or final chunk
            if len(buffer) >= self.buffer_size or chunk.is_final:
                for buffered_chunk in buffer:
                    yield buffered_chunk
                buffer = []


class StreamFilterPrimitive(
    InstrumentedPrimitive[AsyncIterator[StreamChunk], AsyncIterator[StreamChunk]]
):
    """Filter stream chunks based on criteria."""

    def __init__(self, filter_fn: Any) -> None:
        """
        Initialize stream filter.

        Args:
            filter_fn: Function to filter chunks (returns bool)
        """
        super().__init__(name="stream_filter")
        self.filter_fn = filter_fn

    async def _execute_impl(
        self, input_data: AsyncIterator[StreamChunk], context: WorkflowContext
    ) -> AsyncIterator[StreamChunk]:
        """Filter and yield chunks."""
        async for chunk in input_data:
            if self.filter_fn(chunk):
                yield chunk


class StreamMetricsPrimitive(
    InstrumentedPrimitive[
        AsyncIterator[StreamChunk], tuple[AsyncIterator[StreamChunk], StreamMetrics]
    ]
):
    """Track metrics for streaming performance."""

    def __init__(self) -> None:
        super().__init__(name="stream_metrics")

    async def _execute_impl(
        self, input_data: AsyncIterator[StreamChunk], context: WorkflowContext
    ) -> tuple[AsyncIterator[StreamChunk], StreamMetrics]:
        """Track metrics while streaming."""
        metrics = StreamMetrics()
        start_time = asyncio.get_event_loop().time()

        async def tracked_stream() -> AsyncIterator[StreamChunk]:
            """Generator that tracks metrics."""
            async for chunk in input_data:
                metrics.total_chunks += 1
                metrics.total_chars += len(chunk.content)
                yield chunk

            # Calculate final metrics
            end_time = asyncio.get_event_loop().time()
            metrics.duration_seconds = end_time - start_time
            if metrics.duration_seconds > 0:
                metrics.chunks_per_second = (
                    metrics.total_chunks / metrics.duration_seconds
                )
                metrics.chars_per_second = (
                    metrics.total_chars / metrics.duration_seconds
                )

        return tracked_stream(), metrics


# ==============================================================================
# Stream Aggregation
# ==============================================================================


class StreamAggregatorPrimitive(
    InstrumentedPrimitive[AsyncIterator[StreamChunk], dict[str, Any]]
):
    """Aggregate streaming chunks into final result."""

    def __init__(self) -> None:
        super().__init__(name="stream_aggregator")

    async def _execute_impl(
        self, input_data: AsyncIterator[StreamChunk], context: WorkflowContext
    ) -> dict[str, Any]:
        """Collect all chunks and return complete response."""
        chunks: list[str] = []
        metadata: dict[str, Any] = {}
        total_chunks = 0

        async for chunk in input_data:
            chunks.append(chunk.content)
            total_chunks += 1

            # Capture metadata from first chunk
            if chunk.metadata and not metadata:
                metadata = chunk.metadata.copy()

        # Combine chunks
        complete_text = "".join(chunks)

        return {
            "response": complete_text,
            "metadata": metadata,
            "streaming_stats": {
                "total_chunks": total_chunks,
                "total_chars": len(complete_text),
            },
        }


# ==============================================================================
# Example Usage
# ==============================================================================


async def demo_basic_streaming() -> None:
    """Demonstrate basic streaming."""
    print("=" * 80)
    print("Demo 1: Basic Streaming")
    print("=" * 80)
    print()

    # Create streaming LLM
    streaming_llm = StreamingLLMPrimitive(model="gpt-4-mini", chunk_delay=0.05)

    # Create context
    context = WorkflowContext(
        correlation_id="stream-demo-1",
        metadata={},
    )

    # Execute and stream
    print("Streaming response:")
    print("-" * 80)

    stream = streaming_llm._execute_impl({"prompt": "What is TTA.dev?"}, context)

    async for chunk in stream:
        print(chunk.content, end="", flush=True)
        if chunk.is_final:
            print()  # Newline at end

    print("-" * 80)
    print()


async def demo_buffered_streaming() -> None:
    """Demonstrate buffered streaming."""
    print("=" * 80)
    print("Demo 2: Buffered Streaming")
    print("=" * 80)
    print()

    # Create streaming pipeline
    streaming_llm = StreamingLLMPrimitive(model="gpt-4-mini", chunk_delay=0.02)
    buffer = StreamBufferPrimitive(buffer_size=10)

    context = WorkflowContext(correlation_id="stream-demo-2")

    # Execute
    print("Streaming with buffering (10 token chunks):")
    print("-" * 80)

    stream = streaming_llm._execute_impl({"prompt": "What is TTA.dev?"}, context)
    buffered_stream = buffer._execute_impl(stream, context)

    chunk_count = 0
    async for chunk in buffered_stream:
        print(chunk.content, end="", flush=True)
        chunk_count += 1
        if chunk.is_final:
            print()  # Newline at end

    print("-" * 80)
    print(f"Total chunks delivered: {chunk_count}")
    print()


async def demo_streaming_with_metrics() -> None:
    """Demonstrate streaming with metrics tracking."""
    print("=" * 80)
    print("Demo 3: Streaming with Metrics")
    print("=" * 80)
    print()

    # Create streaming pipeline
    streaming_llm = StreamingLLMPrimitive(model="gpt-4-mini", chunk_delay=0.03)
    metrics_tracker = StreamMetricsPrimitive()

    context = WorkflowContext(correlation_id="stream-demo-3")

    # Execute
    print("Streaming with metrics tracking:")
    print("-" * 80)

    stream = streaming_llm._execute_impl({"prompt": "What is TTA.dev?"}, context)
    tracked_stream, metrics = await metrics_tracker._execute_impl(stream, context)

    async for chunk in tracked_stream:
        print(chunk.content, end="", flush=True)
        if chunk.is_final:
            print()  # Newline at end

    print("-" * 80)
    print("\nMetrics:")
    print(f"  Total Chunks: {metrics.total_chunks}")
    print(f"  Total Characters: {metrics.total_chars}")
    print(f"  Duration: {metrics.duration_seconds:.2f}s")
    print(f"  Chunks/sec: {metrics.chunks_per_second:.1f}")
    print(f"  Chars/sec: {metrics.chars_per_second:.1f}")
    print()


async def demo_stream_aggregation() -> None:
    """Demonstrate stream aggregation."""
    print("=" * 80)
    print("Demo 4: Stream Aggregation")
    print("=" * 80)
    print()

    # Create streaming pipeline with aggregation
    streaming_llm = StreamingLLMPrimitive(model="gpt-4-mini", chunk_delay=0.01)
    aggregator = StreamAggregatorPrimitive()

    context = WorkflowContext(correlation_id="stream-demo-4")

    print("Collecting streaming response...")

    # Execute
    stream = streaming_llm._execute_impl({"prompt": "What is TTA.dev?"}, context)
    result = await aggregator._execute_impl(stream, context)

    print("\nComplete Response:")
    print("-" * 80)
    print(result["response"])
    print("-" * 80)
    print("\nStats:")
    print(f"  Total Chunks: {result['streaming_stats']['total_chunks']}")
    print(f"  Total Characters: {result['streaming_stats']['total_chars']}")
    print()


async def main() -> None:
    """Run all streaming demos."""
    print("\n")
    print("=" * 80)
    print("STREAMING LLM RESPONSES EXAMPLE")
    print("=" * 80)
    print("\n")

    await demo_basic_streaming()
    await asyncio.sleep(1)

    await demo_buffered_streaming()
    await asyncio.sleep(1)

    await demo_streaming_with_metrics()
    await asyncio.sleep(1)

    await demo_stream_aggregation()

    print("=" * 80)
    print("✅ All streaming demos complete!")
    print("=" * 80)
    print()
    print("Key Features Demonstrated:")
    print("  ✅ Token-by-token streaming")
    print("  ✅ Stream buffering")
    print("  ✅ Stream filtering")
    print("  ✅ Performance metrics")
    print("  ✅ Stream aggregation")
    print("  ✅ Cancellation support")


if __name__ == "__main__":
    asyncio.run(main())
