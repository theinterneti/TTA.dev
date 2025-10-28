"""Decorators for tracing and metrics."""

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from .setup import get_meter, get_tracer, is_apm_enabled

logger = logging.getLogger(__name__)


def trace_workflow(span_name: str | None = None, attributes: dict[str, Any] | None = None):
    """Decorator to trace workflow function execution.

    Args:
        span_name: Custom span name (defaults to function name)
        attributes: Additional attributes to add to the span

    Example:
        >>> @trace_workflow("my_workflow")
        ... async def process_data(data):
        ...     return processed_data
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not is_apm_enabled():
                return await func(*args, **kwargs)

            tracer = get_tracer(func.__module__)
            if not tracer:
                return await func(*args, **kwargs)

            name = span_name or f"{func.__module__}.{func.__name__}"
            attrs = attributes or {}
            attrs["function.name"] = func.__name__
            attrs["function.module"] = func.__module__

            with tracer.start_as_current_span(name, attributes=attrs) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("function.result", "success")
                    return result
                except Exception as e:
                    span.set_attribute("function.result", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not is_apm_enabled():
                return func(*args, **kwargs)

            tracer = get_tracer(func.__module__)
            if not tracer:
                return func(*args, **kwargs)

            name = span_name or f"{func.__module__}.{func.__name__}"
            attrs = attributes or {}
            attrs["function.name"] = func.__name__
            attrs["function.module"] = func.__module__

            with tracer.start_as_current_span(name, attributes=attrs) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("function.result", "success")
                    return result
                except Exception as e:
                    span.set_attribute("function.result", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    raise

        # Return appropriate wrapper based on function type
        import inspect

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def track_metric(
    metric_name: str, metric_type: str = "counter", description: str = "", unit: str = "1"
):
    """Decorator to track metrics for function execution.

    Args:
        metric_name: Name of the metric
        metric_type: Type of metric ("counter", "histogram", "gauge")
        description: Description of the metric
        unit: Unit of measurement

    Example:
        >>> @track_metric("api_calls", "counter", "Number of API calls")
        ... async def call_api():
        ...     return result
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not is_apm_enabled():
                return await func(*args, **kwargs)

            meter = get_meter(func.__module__)
            if not meter:
                return await func(*args, **kwargs)

            # Create appropriate metric instrument
            if metric_type == "counter":
                instrument = meter.create_counter(metric_name, description=description, unit=unit)
            elif metric_type == "histogram":
                instrument = meter.create_histogram(metric_name, description=description, unit=unit)
            else:
                logger.warning(f"Unknown metric type: {metric_type}")
                return await func(*args, **kwargs)

            # Track execution
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)

                # Record metric
                if metric_type == "counter":
                    instrument.add(1, {"status": "success"})
                elif metric_type == "histogram":
                    duration = time.time() - start_time
                    instrument.record(duration, {"status": "success"})

                return result

            except Exception as e:
                # Record error metric
                if metric_type == "counter":
                    instrument.add(1, {"status": "error", "error_type": type(e).__name__})
                elif metric_type == "histogram":
                    duration = time.time() - start_time
                    instrument.record(duration, {"status": "error", "error_type": type(e).__name__})
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not is_apm_enabled():
                return func(*args, **kwargs)

            meter = get_meter(func.__module__)
            if not meter:
                return func(*args, **kwargs)

            # Create appropriate metric instrument
            if metric_type == "counter":
                instrument = meter.create_counter(metric_name, description=description, unit=unit)
            elif metric_type == "histogram":
                instrument = meter.create_histogram(metric_name, description=description, unit=unit)
            else:
                logger.warning(f"Unknown metric type: {metric_type}")
                return func(*args, **kwargs)

            # Track execution
            start_time = time.time()
            try:
                result = func(*args, **kwargs)

                # Record metric
                if metric_type == "counter":
                    instrument.add(1, {"status": "success"})
                elif metric_type == "histogram":
                    duration = time.time() - start_time
                    instrument.record(duration, {"status": "success"})

                return result

            except Exception as e:
                # Record error metric
                if metric_type == "counter":
                    instrument.add(1, {"status": "error", "error_type": type(e).__name__})
                elif metric_type == "histogram":
                    duration = time.time() - start_time
                    instrument.record(duration, {"status": "error", "error_type": type(e).__name__})
                raise

        # Return appropriate wrapper based on function type
        import inspect

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
