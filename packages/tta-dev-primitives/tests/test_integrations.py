"""Tests for integration primitives."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.integrations.anthropic_primitive import (
    AnthropicPrimitive,
    AnthropicRequest,
    AnthropicResponse,
)
from tta_dev_primitives.integrations.ollama_primitive import (
    OllamaPrimitive,
    OllamaRequest,
    OllamaResponse,
)
from tta_dev_primitives.integrations.openai_primitive import (
    OpenAIPrimitive,
    OpenAIRequest,
    OpenAIResponse,
)
from tta_dev_primitives.integrations.sqlite_primitive import (
    SQLitePrimitive,
    SQLiteRequest,
    SQLiteResponse,
)
from tta_dev_primitives.integrations.supabase_primitive import (
    SupabasePrimitive,
    SupabaseRequest,
    SupabaseResponse,
)


class TestOpenAIPrimitive:
    """Tests for OpenAIPrimitive."""

    @pytest.mark.asyncio
    async def test_openai_basic_execution(self) -> None:
        """Test basic OpenAI execution with mocked client."""
        # Create mock response
        mock_choice = MagicMock()
        mock_choice.message.content = "Hello! How can I help you?"
        mock_choice.finish_reason = "stop"

        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 8
        mock_usage.total_tokens = 18

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.model = "gpt-4o-mini"
        mock_response.usage = mock_usage

        # Create primitive with mocked client (provide dummy API key for testing)
        primitive = OpenAIPrimitive(model="gpt-4o-mini", api_key="test-key")
        primitive.client.chat.completions.create = AsyncMock(return_value=mock_response)

        # Execute
        context = WorkflowContext(workflow_id="test")
        request = OpenAIRequest(messages=[{"role": "user", "content": "Hello"}])
        response = await primitive.execute(request, context)

        # Verify
        assert isinstance(response, OpenAIResponse)
        assert response.content == "Hello! How can I help you?"
        assert response.model == "gpt-4o-mini"
        assert response.usage["prompt_tokens"] == 10
        assert response.usage["completion_tokens"] == 8
        assert response.usage["total_tokens"] == 18
        assert response.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_openai_with_temperature(self) -> None:
        """Test OpenAI with custom temperature."""
        mock_choice = MagicMock()
        mock_choice.message.content = "Creative response"
        mock_choice.finish_reason = "stop"

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.model = "gpt-4o-mini"
        mock_response.usage = MagicMock(prompt_tokens=5, completion_tokens=3, total_tokens=8)

        primitive = OpenAIPrimitive(api_key="test-key")
        primitive.client.chat.completions.create = AsyncMock(return_value=mock_response)

        context = WorkflowContext(workflow_id="test")
        request = OpenAIRequest(
            messages=[{"role": "user", "content": "Be creative"}],
            temperature=1.5,
        )
        response = await primitive.execute(request, context)

        # Verify temperature was passed
        call_args = primitive.client.chat.completions.create.call_args
        assert call_args.kwargs["temperature"] == 1.5
        assert response.content == "Creative response"

    @pytest.mark.asyncio
    async def test_openai_model_override(self) -> None:
        """Test overriding model in request."""
        mock_choice = MagicMock()
        mock_choice.message.content = "Response"
        mock_choice.finish_reason = "stop"

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.model = "gpt-4"
        mock_response.usage = MagicMock(prompt_tokens=5, completion_tokens=3, total_tokens=8)

        primitive = OpenAIPrimitive(model="gpt-4o-mini", api_key="test-key")
        primitive.client.chat.completions.create = AsyncMock(return_value=mock_response)

        context = WorkflowContext(workflow_id="test")
        request = OpenAIRequest(
            messages=[{"role": "user", "content": "Test"}],
            model="gpt-4",  # Override default
        )
        response = await primitive.execute(request, context)

        # Verify correct model was used
        call_args = primitive.client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "gpt-4"


class TestAnthropicPrimitive:
    """Tests for AnthropicPrimitive."""

    @pytest.mark.asyncio
    async def test_anthropic_basic_execution(self) -> None:
        """Test basic Anthropic execution with mocked client."""
        # Create mock response
        mock_content = MagicMock()
        mock_content.text = "Hello! I'm Claude."

        mock_usage = MagicMock()
        mock_usage.input_tokens = 12
        mock_usage.output_tokens = 6

        mock_response = MagicMock()
        mock_response.content = [mock_content]
        mock_response.model = "claude-3-5-sonnet-20241022"
        mock_response.usage = mock_usage
        mock_response.stop_reason = "end_turn"

        # Create primitive with mocked client
        primitive = AnthropicPrimitive()
        primitive.client.messages.create = AsyncMock(return_value=mock_response)

        # Execute
        context = WorkflowContext(workflow_id="test")
        request = AnthropicRequest(
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=1024,
        )
        response = await primitive.execute(request, context)

        # Verify
        assert isinstance(response, AnthropicResponse)
        assert response.content == "Hello! I'm Claude."
        assert response.model == "claude-3-5-sonnet-20241022"
        assert response.usage["input_tokens"] == 12
        assert response.usage["output_tokens"] == 6
        assert response.usage["total_tokens"] == 18
        assert response.stop_reason == "end_turn"

    @pytest.mark.asyncio
    async def test_anthropic_with_system_prompt(self) -> None:
        """Test Anthropic with system prompt."""
        mock_content = MagicMock()
        mock_content.text = "I am a helpful assistant."

        mock_response = MagicMock()
        mock_response.content = [mock_content]
        mock_response.model = "claude-3-5-sonnet-20241022"
        mock_response.usage = MagicMock(input_tokens=10, output_tokens=5)
        mock_response.stop_reason = "end_turn"

        primitive = AnthropicPrimitive()
        primitive.client.messages.create = AsyncMock(return_value=mock_response)

        context = WorkflowContext(workflow_id="test")
        request = AnthropicRequest(
            messages=[{"role": "user", "content": "Who are you?"}],
            max_tokens=1024,
            system="You are a helpful assistant.",
        )
        response = await primitive.execute(request, context)

        # Verify system prompt was passed
        call_args = primitive.client.messages.create.call_args
        assert call_args.kwargs["system"] == "You are a helpful assistant."
        assert response.content == "I am a helpful assistant."

    @pytest.mark.asyncio
    async def test_anthropic_model_override(self) -> None:
        """Test overriding model in request."""
        mock_content = MagicMock()
        mock_content.text = "Response"

        mock_response = MagicMock()
        mock_response.content = [mock_content]
        mock_response.model = "claude-3-opus-20240229"
        mock_response.usage = MagicMock(input_tokens=5, output_tokens=3)
        mock_response.stop_reason = "end_turn"

        primitive = AnthropicPrimitive(model="claude-3-5-sonnet-20241022")
        primitive.client.messages.create = AsyncMock(return_value=mock_response)

        context = WorkflowContext(workflow_id="test")
        request = AnthropicRequest(
            messages=[{"role": "user", "content": "Test"}],
            max_tokens=1024,
            model="claude-3-opus-20240229",  # Override default
        )
        response = await primitive.execute(request, context)

        # Verify correct model was used
        call_args = primitive.client.messages.create.call_args
        assert call_args.kwargs["model"] == "claude-3-opus-20240229"


class TestOllamaPrimitive:
    """Tests for OllamaPrimitive."""

    @pytest.mark.asyncio
    async def test_ollama_basic_execution(self) -> None:
        """Test basic Ollama execution with mocked client."""
        # Create mock response
        mock_response = {
            "message": {"content": "Hello! I'm a local LLM."},
            "model": "llama3.2",
            "done": True,
            "total_duration": 1000000,
            "load_duration": 500000,
            "prompt_eval_count": 10,
            "eval_count": 8,
        }

        # Create primitive with mocked client
        primitive = OllamaPrimitive(model="llama3.2")
        primitive.client.chat = AsyncMock(return_value=mock_response)

        # Execute
        context = WorkflowContext(workflow_id="test")
        request = OllamaRequest(messages=[{"role": "user", "content": "Hello"}])
        response = await primitive.execute(request, context)

        # Verify
        assert isinstance(response, OllamaResponse)
        assert response.content == "Hello! I'm a local LLM."
        assert response.model == "llama3.2"
        assert response.done is True
        assert response.total_duration == 1000000
        assert response.prompt_eval_count == 10
        assert response.eval_count == 8

    @pytest.mark.asyncio
    async def test_ollama_with_temperature(self) -> None:
        """Test Ollama with custom temperature."""
        mock_response = {
            "message": {"content": "Creative response"},
            "model": "llama3.2",
            "done": True,
        }

        primitive = OllamaPrimitive()
        primitive.client.chat = AsyncMock(return_value=mock_response)

        context = WorkflowContext(workflow_id="test")
        request = OllamaRequest(
            messages=[{"role": "user", "content": "Be creative"}],
            temperature=1.5,
        )
        response = await primitive.execute(request, context)

        # Verify temperature was passed in options
        call_args = primitive.client.chat.call_args
        assert call_args.kwargs.get("options", {}).get("temperature") == 1.5
        assert response.content == "Creative response"

    @pytest.mark.asyncio
    async def test_ollama_model_override(self) -> None:
        """Test overriding model in request."""
        mock_response = {
            "message": {"content": "Response"},
            "model": "mistral",
            "done": True,
        }

        primitive = OllamaPrimitive(model="llama3.2")
        primitive.client.chat = AsyncMock(return_value=mock_response)

        context = WorkflowContext(workflow_id="test")
        request = OllamaRequest(
            messages=[{"role": "user", "content": "Test"}],
            model="mistral",  # Override default
        )
        response = await primitive.execute(request, context)

        # Verify correct model was used
        call_args = primitive.client.chat.call_args
        assert call_args.kwargs["model"] == "mistral"
        assert response.model == "mistral"


class TestSupabasePrimitive:
    """Tests for SupabasePrimitive."""

    @pytest.mark.asyncio
    async def test_supabase_select(self) -> None:
        """Test Supabase SELECT operation with mocked client."""
        # Create mock response
        mock_response = MagicMock()
        mock_response.data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

        # Create primitive with mocked client
        primitive = SupabasePrimitive(url="https://test.supabase.co", key="test-key")
        primitive.client.table = MagicMock(
            return_value=MagicMock(
                select=MagicMock(
                    return_value=MagicMock(execute=MagicMock(return_value=mock_response))
                )
            )
        )

        # Execute
        context = WorkflowContext(workflow_id="test")
        request = SupabaseRequest(operation="select", table="users")
        response = await primitive.execute(request, context)

        # Verify
        assert isinstance(response, SupabaseResponse)
        assert response.data == [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        assert response.count == 2
        assert response.status == "success"

    @pytest.mark.asyncio
    async def test_supabase_insert(self) -> None:
        """Test Supabase INSERT operation."""
        mock_response = MagicMock()
        mock_response.data = [{"id": 3, "name": "Charlie"}]

        primitive = SupabasePrimitive(url="https://test.supabase.co", key="test-key")
        primitive.client.table = MagicMock(
            return_value=MagicMock(
                insert=MagicMock(
                    return_value=MagicMock(execute=MagicMock(return_value=mock_response))
                )
            )
        )

        context = WorkflowContext(workflow_id="test")
        request = SupabaseRequest(operation="insert", table="users", data={"name": "Charlie"})
        response = await primitive.execute(request, context)

        assert response.data == [{"id": 3, "name": "Charlie"}]
        assert response.count == 1
        assert response.status == "success"

    @pytest.mark.asyncio
    async def test_supabase_with_filters(self) -> None:
        """Test Supabase SELECT with filters."""
        mock_response = MagicMock()
        mock_response.data = [{"id": 1, "name": "Alice", "age": 25}]

        primitive = SupabasePrimitive(url="https://test.supabase.co", key="test-key")

        # Create mock chain for filters
        mock_eq = MagicMock(execute=MagicMock(return_value=mock_response))
        mock_select = MagicMock(eq=MagicMock(return_value=mock_eq))
        primitive.client.table = MagicMock(
            return_value=MagicMock(select=MagicMock(return_value=mock_select))
        )

        context = WorkflowContext(workflow_id="test")
        request = SupabaseRequest(operation="select", table="users", filters={"age": 25})
        response = await primitive.execute(request, context)

        # Verify filter was applied
        assert response.data == [{"id": 1, "name": "Alice", "age": 25}]
        assert response.count == 1


class TestSQLitePrimitive:
    """Tests for SQLitePrimitive."""

    @pytest.mark.asyncio
    async def test_sqlite_create_and_select(self) -> None:
        """Test SQLite CREATE TABLE and SELECT operations."""
        # Use temporary file database for testing (in-memory doesn't persist across connections)
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        primitive = SQLitePrimitive(database=db_path)
        context = WorkflowContext(workflow_id="test")

        # Create table
        create_request = SQLiteRequest(
            query="CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)",
            fetch="none",
        )
        await primitive.execute(create_request, context)

        # Insert data
        insert_request = SQLiteRequest(
            query="INSERT INTO users (name, age) VALUES (?, ?)",
            parameters=("Alice", 25),
            fetch="none",
        )
        insert_response = await primitive.execute(insert_request, context)
        assert insert_response.rowcount == 1
        assert insert_response.lastrowid == 1

        # Select data
        select_request = SQLiteRequest(
            query="SELECT * FROM users WHERE age > ?", parameters=(20,), fetch="all"
        )
        select_response = await primitive.execute(select_request, context)

        assert isinstance(select_response, SQLiteResponse)
        assert len(select_response.data) == 1
        assert select_response.data[0]["name"] == "Alice"
        assert select_response.data[0]["age"] == 25

    @pytest.mark.asyncio
    async def test_sqlite_fetch_one(self) -> None:
        """Test SQLite fetch one row."""
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        primitive = SQLitePrimitive(database=db_path)
        context = WorkflowContext(workflow_id="test")

        # Create and populate table
        await primitive.execute(
            SQLiteRequest(
                query="CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)",
                fetch="none",
            ),
            context,
        )
        await primitive.execute(
            SQLiteRequest(
                query="INSERT INTO users (name) VALUES (?)",
                parameters=("Bob",),
                fetch="none",
            ),
            context,
        )

        # Fetch one
        request = SQLiteRequest(query="SELECT * FROM users LIMIT 1", fetch="one")
        response = await primitive.execute(request, context)

        assert response.data is not None
        assert response.data["name"] == "Bob"

    @pytest.mark.asyncio
    async def test_sqlite_update_and_delete(self) -> None:
        """Test SQLite UPDATE and DELETE operations."""
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        primitive = SQLitePrimitive(database=db_path)
        context = WorkflowContext(workflow_id="test")

        # Setup
        await primitive.execute(
            SQLiteRequest(
                query="CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)",
                fetch="none",
            ),
            context,
        )
        await primitive.execute(
            SQLiteRequest(
                query="INSERT INTO users (name, age) VALUES (?, ?)",
                parameters=("Charlie", 30),
                fetch="none",
            ),
            context,
        )

        # Update
        update_request = SQLiteRequest(
            query="UPDATE users SET age = ? WHERE name = ?",
            parameters=(35, "Charlie"),
            fetch="none",
        )
        update_response = await primitive.execute(update_request, context)
        assert update_response.rowcount == 1

        # Delete
        delete_request = SQLiteRequest(
            query="DELETE FROM users WHERE name = ?",
            parameters=("Charlie",),
            fetch="none",
        )
        delete_response = await primitive.execute(delete_request, context)
        assert delete_response.rowcount == 1
