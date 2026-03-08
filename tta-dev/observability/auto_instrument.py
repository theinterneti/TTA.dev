"""Automatic instrumentation for TTA.dev primitives.

This module provides decorators and utilities to automatically instrument
all WorkflowPrimitive executions with observability traces.
"""

import functools
import time
import traceback
from typing import Any, Callable, TypeVar

from primitives.core.base import WorkflowContext, WorkflowPrimitive
from observability.collector import trace_collector

T = TypeVar("T")
U = TypeVar("U")


def instrument_primitive(execute_method: Callable) -> Callable:
    """
    Decorator to automatically instrument primitive execute() methods.
    
    Captures:
    - Input/output data
    - Execution duration
    - Errors and stack traces
    - Context metadata
    
    Args:
        execute_method: The primitive's execute() method
        
    Returns:
        Instrumented execute method
    """
    @functools.wraps(execute_method)
    async def instrumented_execute(
        self: WorkflowPrimitive,
        input_data: T,
        context: WorkflowContext,
    ) -> U:
        primitive_name = self.__class__.__name__
        start_time = time.time()
        
        # Create span data
        span_data = {
            "name": primitive_name,
            "start_time": start_time,
            "attributes": {
                "primitive.type": primitive_name,
                "primitive.input_type": type(input_data).__name__,
                **context.to_otel_context(),
            },
        }
        
        # Add context tags
        if context.tags:
            span_data["attributes"].update(
                {f"tag.{k}": v for k, v in context.tags.items()}
            )
        
        try:
            # Execute the primitive
            result = await execute_method(self, input_data, context)
            
            # Record success
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            span_data.update({
                "end_time": end_time,
                "duration_ms": duration_ms,
                "status": "ok",
                "attributes": {
                    **span_data["attributes"],
                    "primitive.output_type": type(result).__name__,
                },
            })
            
            # Send to collector
            await trace_collector.collect_span(span_data)
            
            return result
            
        except Exception as e:
            # Record failure
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            span_data.update({
                "end_time": end_time,
                "duration_ms": duration_ms,
                "status": "error",
                "attributes": {
                    **span_data["attributes"],
                    "error.type": type(e).__name__,
                    "error.message": str(e),
                    "error.stacktrace": traceback.format_exc(),
                },
            })
            
            # Send to collector
            await trace_collector.collect_span(span_data)
            
            # Re-raise
            raise
    
    return instrumented_execute


def auto_instrument_primitives() -> None:
    """
    Automatically instrument all WorkflowPrimitive subclasses.
    
    This patches the execute() method of all primitives to add observability.
    Should be called once at application startup.
    
    Example:
        ```python
        from tta-dev.observability.auto_instrument import auto_instrument_primitives
        
        # At application startup
        auto_instrument_primitives()
        
        # Now all primitives are automatically instrumented
        workflow = RetryPrimitive(my_operation)
        result = await workflow.execute(data, context)  # Automatically traced!
        ```
    """
    from primitives.core.base import WorkflowPrimitive
    
    # Get all primitive subclasses
    def get_all_subclasses(cls):
        all_subclasses = []
        for subclass in cls.__subclasses__():
            all_subclasses.append(subclass)
            all_subclasses.extend(get_all_subclasses(subclass))
        return all_subclasses
    
    primitives = get_all_subclasses(WorkflowPrimitive)
    
    # Instrument each primitive's execute method
    instrumented_count = 0
    for primitive_cls in primitives:
        if hasattr(primitive_cls, "execute") and not hasattr(
            primitive_cls.execute, "_instrumented"
        ):
            original_execute = primitive_cls.execute
            instrumented = instrument_primitive(original_execute)
            instrumented._instrumented = True  # Mark as instrumented
            primitive_cls.execute = instrumented
            instrumented_count += 1
    
    print(f"🔍 Auto-instrumented {instrumented_count} primitives for observability")


# Convenience function for manual instrumentation
def trace_workflow(workflow_name: str):
    """
    Decorator to manually instrument any async function as a workflow.
    
    Args:
        workflow_name: Name for the workflow span
        
    Example:
        ```python
        @trace_workflow("data_processing")
        async def process_data(data: dict) -> dict:
            # Your code here
            return processed_data
        ```
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            span_data = {
                "name": workflow_name,
                "start_time": start_time,
                "attributes": {
                    "workflow.name": workflow_name,
                    "workflow.function": func.__name__,
                },
            }
            
            try:
                result = await func(*args, **kwargs)
                
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                
                span_data.update({
                    "end_time": end_time,
                    "duration_ms": duration_ms,
                    "status": "ok",
                })
                
                await trace_collector.collect_span(span_data)
                return result
                
            except Exception as e:
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                
                span_data.update({
                    "end_time": end_time,
                    "duration_ms": duration_ms,
                    "status": "error",
                    "attributes": {
                        **span_data["attributes"],
                        "error.type": type(e).__name__,
                        "error.message": str(e),
                    },
                })
                
                await trace_collector.collect_span(span_data)
                raise
        
        return wrapper
    return decorator
