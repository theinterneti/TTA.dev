#!/usr/bin/env python3
"""Generate test observability data to verify the dashboard works."""

import json
import sqlite3
import time
from pathlib import Path

# Create database
db_path = Path(".tta/traces.db")
db_path.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create tables
cursor.execute("""
    CREATE TABLE IF NOT EXISTS spans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trace_id TEXT,
        span_name TEXT,
        primitive_type TEXT,
        start_time REAL,
        end_time REAL,
        duration_ms REAL,
        status TEXT,
        attributes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# Clear old test data
cursor.execute("DELETE FROM spans WHERE trace_id LIKE 'test-%'")

# Generate test spans
now = time.time()
test_workflows = [
    {
        "trace_id": "test-001",
        "workflow": "DataProcessing",
        "primitives": [
            ("FetchData", "LambdaPrimitive", 0.5, "success"),
            ("Validate", "ConditionalPrimitive", 0.2, "success"),
            ("Transform", "MapPrimitive", 1.2, "success"),
            ("Save", "LambdaPrimitive", 0.8, "success"),
        ],
    },
    {
        "trace_id": "test-002",
        "workflow": "APICall",
        "primitives": [
            ("Authenticate", "LambdaPrimitive", 0.3, "success"),
            ("CallAPI", "RetryPrimitive", 2.5, "success"),
            ("ParseResponse", "LambdaPrimitive", 0.4, "success"),
        ],
    },
    {
        "trace_id": "test-003",
        "workflow": "FailedWorkflow",
        "primitives": [
            ("Setup", "LambdaPrimitive", 0.2, "success"),
            ("ProcessData", "CircuitBreakerPrimitive", 1.0, "error"),
            ("Cleanup", "FallbackPrimitive", 0.5, "success"),
        ],
    },
]

for workflow in test_workflows:
    offset = 0.0
    for span_name, primitive_type, duration, status in workflow["primitives"]:
        start_time = now + offset
        end_time = start_time + duration

        cursor.execute(
            """
            INSERT INTO spans 
            (trace_id, span_name, primitive_type, start_time, end_time, duration_ms, status, attributes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                workflow["trace_id"],
                span_name,
                primitive_type,
                start_time,
                end_time,
                duration * 1000,
                status,
                json.dumps(
                    {
                        "workflow": workflow["workflow"],
                        "agent": "test-agent",
                        "input_size": 1024,
                        "output_size": 2048,
                    }
                ),
            ),
        )

        offset += duration

conn.commit()

# Verify data
cursor.execute("SELECT COUNT(*) FROM spans")
count = cursor.fetchone()[0]
print(f"✓ Generated {count} test spans in {db_path}")

cursor.execute("SELECT DISTINCT trace_id FROM spans")
traces = cursor.fetchall()
print(f"✓ Created {len(traces)} test workflows:")
for (trace_id,) in traces:
    cursor.execute("SELECT COUNT(*) FROM spans WHERE trace_id = ?", (trace_id,))
    span_count = cursor.fetchone()[0]
    print(f"  - {trace_id}: {span_count} spans")

conn.close()

print("\n🎯 Now restart the dashboard to see the data!")
print("   Run: uv run python tta-dev/ui/observability_server.py")
