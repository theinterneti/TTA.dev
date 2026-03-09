#!/usr/bin/env python3
import asyncio
import sys

sys.path.insert(0, '.')

from observability.collector import trace_collector

async def test():
    print("🧪 Testing Persistent Observability")
    print("=" * 50)
    
    # Generate some test spans
    for i in range(5):
        span_data = {
            'trace_id': f'test-trace-{i % 2}',
            'name': f'TestPrimitive{i}',
            'start_time': 1234567890.0 + i,
            'end_time': 1234567890.5 + i,
            'duration_ms': 500.0,
            'status': 'ok' if i % 3 != 0 else 'error',
            'attributes': {
                'primitive.type': f'TestPrimitive{i}',
                'test.run': i
            }
        }
        await trace_collector.collect_span(span_data)
    
    print(f'✅ Generated 5 test spans')
    print(f'📊 Database location: {trace_collector.db_path}')
    print()
    
    # Retrieve and display
    spans = trace_collector.get_recent_spans(limit=10)
    print(f'✅ Retrieved {len(spans)} spans from database:')
    print()
    
    for span in spans:
        status_icon = "✅" if span["status"] == "ok" else "❌"
        print(f'  {status_icon} {span["name"]}: {span["duration_ms"]}ms')
    
    print()
    print("=" * 50)
    print("💡 Data persists! Restart the dashboard and it's still there.")
    print("🌐 View at: http://localhost:8000")

asyncio.run(test())
