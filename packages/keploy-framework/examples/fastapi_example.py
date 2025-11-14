"""Example: Using Keploy Framework with FastAPI."""

import asyncio
from fastapi import FastAPI
from keploy_framework import KeployTestRunner, RecordingSession

# Create FastAPI app
app = FastAPI()


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Hello World"}


@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    """Get user by ID."""
    return {"id": user_id, "name": f"User {user_id}"}


@app.post("/api/users")
async def create_user(user: dict):
    """Create new user."""
    return {"id": 123, "name": user["name"], "created": True}


# Example: Recording tests
async def record_example():
    """Record API tests."""
    async with RecordingSession(api_url="http://localhost:8000") as session:
        # These requests will be recorded as test cases
        await session.client.get("/")
        await session.client.get("/api/users/1")
        await session.client.post(
            "/api/users",
            json={"name": "Alice"},
        )


# Example: Running tests
async def test_example():
    """Run recorded tests."""
    runner = KeployTestRunner(api_url="http://localhost:8000")
    results = await runner.run_all_tests(validate=True, generate_report=True)

    print(f"Tests: {results.passed}/{results.total}")
    print(f"Pass rate: {results.pass_rate}%")

    return results.is_success


if __name__ == "__main__":
    # Run example
    import uvicorn

    # Start server in background
    # Then run: asyncio.run(record_example())
    # Then run: asyncio.run(test_example())

    uvicorn.run(app, host="0.0.0.0", port=8000)
